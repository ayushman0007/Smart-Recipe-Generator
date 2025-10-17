import requests

headers = {"Authorization": "Bearer <YOUR_HF_TOKEN>"}  # free token from huggingface.co
image = open("ingredients.jpg", "rb").read()

response = requests.post(
    "https://api-inference.huggingface.co/models/openai/clip-vit-base-patch32",
    headers=headers,
    data=image
)
print(response.json())
