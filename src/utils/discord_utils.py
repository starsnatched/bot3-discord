import discord
from discord.ext import commands
from utils.models import ReasoningModel
from services.infer import OpenAI
from utils.voice_utils import VoiceUtils
from typing import Any, Optional, Union
import json
import io
import numpy as np
from scipy.io import wavfile
import random
import torch
import logging

class DiscordUtils:
    def __init__(self, bot: commands.Bot):
        self.client = OpenAI()
            
        self.voice_client = VoiceUtils()
            
        self.logger = logging.getLogger(__name__)
        self.bot = bot
            
    async def upload_audio(self, message: discord.Message, audio: Union[torch.Tensor, np.ndarray], transcription: str) -> None:
        if isinstance(audio, torch.Tensor):
            audio = audio.cpu().numpy()
        else:
            audio = audio
            
        audio = audio.astype(np.float32)
        
        with io.BytesIO() as wav_buffer:
            wavfile.write(wav_buffer, 22050, audio)
            wav_buffer.seek(0)
            file = discord.File(wav_buffer, filename="audio.wav")
            
            await message.channel.send(
                content=f"-# {transcription}",
                file=file
            )
                
    @staticmethod
    def create_tool_return_json(tool_type: str, content: Any) -> str:
        return json.dumps({
            "message_type": "tool_return",
            "tool_type": tool_type,
            "content": content
        }, indent=4)
        
    @staticmethod
    def create_error_json(tool_type: str, error: Exception) -> str:
        print(f"Error in tool {tool_type}: {error}")
        return json.dumps({
            "message_type": "error_message",
            "tool_type": tool_type,
            "content": str(error)
        }, indent=4)
        
    async def handle_tools(self, message: discord.Message, output: ReasoningModel) -> Optional[str]:
        output.reasoning = output.reasoning.replace('\n', '\n-# ')
        if len(output.reasoning) > 2000:
            output.reasoning = output.reasoning[:1996] + " ..."
            
        if not output.tool_args:
            return
        
        # Basic tools
        if output.tool_args.tool_type == "send_message":
            await message.reply(output.tool_args.content, mention_author=False)
            return
        
        if output.tool_args.tool_type == "send_voice_message":
            audio, out_ps = await self.voice_client.generate_voice(output.tool_args.content)
            if audio is None:
                return self.create_error_json(output.tool_args.tool_type, Exception("Failed to generate voice."))
            
            await self.upload_audio(message, audio, output.tool_args.content)
            return
        
        if output.tool_args.tool_type == "memory_insert":
            result = await self.client.store_memory(output.tool_args.memory)
            return self.create_tool_return_json(output.tool_args.tool_type, result)
            
        if output.tool_args.tool_type == "memory_retrieve":
            result = await self.client.retrieve_memory(output.tool_args.memory)
            return self.create_tool_return_json(output.tool_args.tool_type, result)
        
        if output.tool_args.tool_type == "dice_roll":
            result = random.randint(1, output.tool_args.sides)
            return self.create_tool_return_json(output.tool_args.tool_type, result)
        
        return self.create_error_json(output.tool_args.tool_type, Exception("Tool not found."))