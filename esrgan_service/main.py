import io
import os

import numpy as np
import torch
from basicsr.archs.rrdbnet_arch import RRDBNet
from fastapi import FastAPI, HTTPException, Request, Response
from PIL import Image
from realesrgan import RealESRGANer

# Determine if we should use GPU
USE_GPU = os.getenv("USE_GPU", "0").lower() in ("true", "1", "t")
DEVICE = "cuda" if USE_GPU and torch.cuda.is_available() else "cpu"

print(f"Initializing Real-ESRGAN using device: {DEVICE}")

MODEL_PATH = "/app/models/RealESRGAN_x4plus.pth"

# Verify model exists
if not os.path.exists(MODEL_PATH):
    raise RuntimeError(
        f"Model not found at {MODEL_PATH}. Please ensure the model is mounted correctly."
    )

# Get request timeout from environment
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "60"))

# Initialize model once at startup
print("Initializing Real-ESRGAN...")
model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32)
upsampler = RealESRGANer(
    scale=4,
    model_path=MODEL_PATH,
    model=model,
    tile=200,  # Use smaller tiles on CPU to manage memory
    tile_pad=10,
    pre_pad=0,
    half=USE_GPU,  # Use half precision only on GPU
    device=DEVICE,
)

if DEVICE == "cpu":
    print("Running on CPU mode...")
else:
    print("Running on GPU mode...")

app = FastAPI(
    title="Real-ESRGAN Service",
    # Set longer timeout for the whole application
    timeout=REQUEST_TIMEOUT,
)


@app.get("/health")
def health_check():
    """Health check endpoint that returns the current device being used"""
    try:
        # Try to create a small tensor to verify CUDA/CPU is working
        device = torch.device(DEVICE)
        torch.tensor([1.0], device=device)
        return {
            "status": "healthy",
            "device": DEVICE,
            "gpu_available": torch.cuda.is_available() if USE_GPU else False,
        }
    except Exception as err:
        raise HTTPException(500, "ESRGAN service is unhealthy") from err


@app.post("/upscale")
async def upscale_image(request: Request):
    """
    Upscale an image using Real-ESRGAN.
    Accepts raw binary image data with a content type header.
    Returns the upscaled image as JPEG.
    """
    try:
        content_type = request.headers.get("content-type", "")
        print(f"Received request with content-type: {content_type}")

        if not content_type.startswith("image/"):
            raise HTTPException(
                status_code=400, detail="Content-Type must be an image format"
            )

        # Get the raw image data
        image_data = await request.body()
        print(f"Received image data, size: {len(image_data)} bytes")

        # Convert to PIL Image
        try:
            image = Image.open(io.BytesIO(image_data))
            print(f"Loaded image: {image.format}, size: {image.size}")
            image = image.convert("RGB")
        except Exception as err:
            raise HTTPException(400, "Invalid image data") from err

        # Check image size
        max_pixels = 2000 * 2000  # Max 4MP image
        if image.size[0] * image.size[1] > max_pixels:
            raise HTTPException(
                status_code=413,
                detail=f"Image too large. Max size: {max_pixels} pixels",
            )

        print("Processing image with Real-ESRGAN...")
        try:
            output, _ = upsampler.enhance(np.array(image))
            print(f"Processing complete, output shape: {output.shape}")
            output_image = Image.fromarray(output)
            output_buffer = io.BytesIO()
            output_image.save(output_buffer, format="JPEG")
            output_buffer.seek(0)
            return Response(
                content=output_buffer.read(),
                media_type="image/jpeg",
            )
        except Exception as err:
            print(f"Unexpected error: {str(err)}")
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error during processing: {str(err)}",
            ) from err

    except HTTPException:
        raise
