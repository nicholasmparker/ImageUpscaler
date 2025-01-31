import os
from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse
import numpy as np
from PIL import Image
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer
import uuid
import torch

app = FastAPI(title="Real-ESRGAN Service")

# Determine if we should use GPU
USE_GPU = os.getenv('USE_GPU', '0').lower() in ('true', '1', 't')
DEVICE = 'cuda' if USE_GPU and torch.cuda.is_available() else 'cpu'

print(f"Initializing Real-ESRGAN using device: {DEVICE}")

# Initialize model once at startup
model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32)
upsampler = RealESRGANer(
    scale=4,
    model_path=os.getenv('MODEL_PATH'),
    model=model,
    tile=400 if DEVICE == 'cuda' else 0,  # Use tiling on CPU to manage memory
    tile_pad=10,
    pre_pad=0,
    half=USE_GPU  # Only use half precision on GPU
)

if DEVICE == 'cuda':
    print("Moving model to GPU...")
    upsampler.device = torch.device('cuda')
    upsampler.model.cuda()
else:
    print("Running on CPU mode...")
    upsampler.device = torch.device('cpu')
    upsampler.model.cpu()

@app.get("/health")
async def health_check():
    """Health check endpoint that returns the current device being used"""
    return {
        "status": "healthy",
        "device": DEVICE,
        "gpu_available": torch.cuda.is_available() if USE_GPU else False
    }

@app.post("/upscale")
async def upscale_image(image: UploadFile):
    """
    Upscale an image using Real-ESRGAN.
    Returns the path to the upscaled image.
    """
    # Create unique filename for this request
    temp_input = f"/tmp/{uuid.uuid4()}_input.png"
    temp_output = f"/tmp/{uuid.uuid4()}_output.png"
    
    try:
        # Save uploaded image
        content = await image.read()
        with open(temp_input, 'wb') as f:
            f.write(content)
        
        # Process image
        input_img = Image.open(temp_input)
        output, _ = upsampler.enhance(np.array(input_img))
        output_img = Image.fromarray(output)
        output_img.save(temp_output)
        
        # Return the processed image
        return FileResponse(temp_output, media_type="image/png")
    
    finally:
        # Cleanup temporary files
        for file in [temp_input, temp_output]:
            if os.path.exists(file):
                os.remove(file)
