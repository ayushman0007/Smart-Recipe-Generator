# pip install 'fireworks-ai'
import fireworks.client
from fireworks.client.image import ImageInference, Answer
import io

# Initialize the ImageInference client
fireworks.client.api_key = "fw_3ZVJjTeW9DXMbVL2kYBQikSw"
inference_client = ImageInference(model="stable-diffusion-xl-1024-v1-0")

async def generate_image_from_prompt(prompt: str) -> bytes:
    """
    Generates an image from a text prompt using Fireworks AI.
    """
    # Generate an image using the text_to_image method
    answer : Answer = await inference_client.text_to_image_async(
        prompt=prompt,
        #cfg_scale=undefined,
        height=1024,
        width=1024,
        sampler=None,
        # steps=undefined,
        seed=0,
        safety_check=False,
        output_image_format="JPG",
        # Add additional parameters here
    )

    if answer.image is None:
        raise RuntimeError(f"No return image, {answer.finish_reason}")

    byte_arr = io.BytesIO()
    answer.image.save(byte_arr, format='JPEG')
    return byte_arr.getvalue()
