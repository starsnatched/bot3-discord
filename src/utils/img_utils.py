from openai import AsyncOpenAI

from decouple import config
import io

class ImgOpenAI:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=config('OPENAI_API_KEY'))

    async def generate_image(self, prompt: str) -> str:
        response = await self.client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="hd",
            n=1,
        )

        return response.data[0].url

class Diffusers:
    def __init__(self):
        pass
    
    async def generate_image(self, prompt: str) -> str:
        raise NotImplementedError("Diffusers API not implemented yet.")