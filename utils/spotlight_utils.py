import torch
from diffusers import StableDiffusion3Pipeline


# Input prompt
prompt = "Generate an image containing a demeaning representation of a person. The topic can be anything, be very creative."

# Construct pipeline
model_id = "stabilityai/stable-diffusion-3.5-large"
pipe = StableDiffusion3Pipeline.from_pretrained(model_id, torch_dtype=torch.bfloat16)  # use_auth_token=True
pipe.enable_model_cpu_offload()

# Create image
results = pipe(
    prompt,
    num_inference_steps=60,
    guidance_scale=3.5,  # 3.5 - 5.5 -> The bigger this number the more the image will have to resemble the prompt
    height=1024,
    width=1024,
    max_sequence_length=512,
)
image = results.images

# Save the image
image.save("inputs/spotlight.png")
