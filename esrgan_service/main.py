import os
from fastapi import FastAPI, UploadFile, Response
import numpy as np
from PIL import Image
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer
import uuid
import torch
import requests
import io

app = FastAPI(title="Real-ESRGAN Service")

# Determine if we should use GPU
USE_GPU = os.getenv("USE_GPU", "0").lower() in ("true", "1", "t")
DEVICE = "cuda" if USE_GPU and torch.cuda.is_available() else "cpu"

print(f"Initializing Real-ESRGAN using device: {DEVICE}")

MODEL_PATH = "/app/models/RealESRGAN_x4plus.pth"


def ensure_model_exists():
    """Download the model if it doesn't exist."""
    if os.path.exists(MODEL_PATH):
        return

    print("Downloading model...")
    url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
    response = requests.get(url, stream=True)
    response.raise_for_status()

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print("Model downloaded successfully")


# Initialize model at startup
print("Initializing Real-ESRGAN...")
ensure_model_exists()

# Initialize model once at startup
model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32)
upsampler = RealESRGANer(
    scale=4,
    model_path=MODEL_PATH,
    model=model,
    tile=400 if DEVICE == "cuda" else 0,  # Use tiling on CPU to manage memory
    tile_pad=10,
    pre_pad=0,
    half=USE_GPU,  # Only use half precision on GPU
    device=DEVICE,
)

if DEVICE == "cuda":
    print("Moving model to GPU...")
    upsampler.model.cuda()
else:
    print("Running on CPU mode...")
    upsampler.model.cpu()


@app.get("/health")
async def health_check():
    """Health check endpoint that returns the current device being used"""
    return {
        "status": "healthy",
        "device": DEVICE,
        "gpu_available": torch.cuda.is_available() if USE_GPU else False,
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
        with open(temp_input, "wb") as f:
            f.write(content)

        # Process image
        input_img = Image.open(temp_input)
        output, _ = upsampler.enhance(np.array(input_img))
        output_img = Image.fromarray(output)

        # Convert back to bytes
        img_byte_arr = io.BytesIO()
        output_img.save(img_byte_arr, format="JPEG")
        img_byte_arr = img_byte_arr.getvalue()

        return Response(content=img_byte_arr, media_type="image/jpeg")

    finally:
        # Cleanup temporary files
        for file in [temp_input, temp_output]:
            if os.path.exists(file):
                os.remove(file)
