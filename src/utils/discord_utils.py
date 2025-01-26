import discord
from discord.ext import commands

from utils.voice_utils import VoiceUtils
from utils.img_utils import ImgOpenAI, Diffusers
from utils.models import ReasoningModel
from utils.discord_model import ButtonView
from services.infer import OpenAI, Ollama
from services.database import DatabaseService

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
        self.voice_client = VoiceUtils()
        self.db = DatabaseService()
        self.bot = bot
        if self.bot.backend == 'openai':
            self.img = ImgOpenAI()
        elif self.bot.backend == 'ollama':
            self.img = Diffusers()
            
        self.logger = logging.getLogger(__name__)
        self._get_client()
        
    def _get_client(self):
        if self.bot.backend == 'openai':
            self.client = OpenAI()
        elif self.bot.backend == 'ollama':
            self.client = Ollama()
        else:
            raise ValueError("Invalid backend type.")
            
    async def upload_audio(self, message: discord.Message, audio: Union[torch.Tensor, np.ndarray], transcription: str, reasoning: str) -> None:
        if isinstance(audio, torch.Tensor):
            audio = audio.cpu().numpy()
        else:
            audio = audio
            
        audio = audio.astype(np.float32)
        
        with io.BytesIO() as wav_buffer:
            wavfile.write(wav_buffer, 22050, audio)
            wav_buffer.seek(0)
            file = discord.File(wav_buffer, filename="audio.wav")
            
            transcription = transcription.replace("\n", "\n-# ")
            
            if len(transcription) > 2000:
                transcription = transcription[:1996].strip() + " ..."
                
            if message.author.id == self.bot.dev_id:
                await message.reply(
                    content=f"-# {transcription}",
                    file=file,
                    mention_author=False,
                    view=ButtonView(reasoning, self.bot.dev_id)
                )
            else:
                await message.reply(
                    content=f"-# {transcription}",
                    file=file,
                    mention_author=False
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
        reasoning_list = [
            f"-# {line.strip()}" 
            for line in output.reasoning.split("\n") 
            if line.strip()
        ]
        output.reasoning = "\n\n".join(reasoning_list)
        
        if len(output.reasoning) > 2000:
            output.reasoning = output.reasoning[:1996] + " ..."

        if output.tool_args.tool_type in await self.db.get_disabled_tools(message.guild.id):
            return self.create_error_json(output.tool_args.tool_type, Exception("Tool is disabled."))
        
        # Basic tools
        if output.tool_args.tool_type == "send_message":
            if message.author.id == self.bot.dev_id:
                await message.reply(output.tool_args.content, mention_author=False, view=ButtonView(output.reasoning, self.bot.dev_id))
                return
            await message.reply(output.tool_args.content, mention_author=False)
            return
        
        if output.tool_args.tool_type == "send_voice_message":
            audio, out_ps = await self.voice_client.generate_voice(output.tool_args.content)
            if audio is None:
                return self.create_error_json(output.tool_args.tool_type, Exception("Failed to generate voice."))
            
            await self.upload_audio(message, audio, output.tool_args.content, output.reasoning)
            return
        
        if output.tool_args.tool_type == "memory_insert":
            if message.author.id == self.bot.dev_id:
                await message.reply(f"-# Calling tool: {output.tool_args.tool_type}", mention_author=False, view=ButtonView(output.reasoning, self.bot.dev_id))
            result = await self.client.store_memory(output.tool_args.memory, message.guild.id)
            return self.create_tool_return_json(output.tool_args.tool_type, result)
            
        if output.tool_args.tool_type == "memory_retrieve":
            if message.author.id == self.bot.dev_id:
                await message.reply(f"-# Calling tool: {output.tool_args.tool_type}", mention_author=False, view=ButtonView(output.reasoning, self.bot.dev_id))
            result = await self.client.retrieve_memory(output.tool_args.memory, message.guild.id)
            return self.create_tool_return_json(output.tool_args.tool_type, result)
        
        if output.tool_args.tool_type == "dice_roll":
            if message.author.id == self.bot.dev_id:
                await message.reply(f"-# Calling tool: {output.tool_args.tool_type}", mention_author=False, view=ButtonView(output.reasoning, self.bot.dev_id))
            result = random.randint(1, output.tool_args.sides)
            return self.create_tool_return_json(output.tool_args.tool_type, result)
        
        if output.tool_args.tool_type == "add_reaction":
            if message.author.id == self.bot.dev_id:
                await message.reply(f"-# Calling tool: {output.tool_args.tool_type}", mention_author=False, view=ButtonView(output.reasoning, self.bot.dev_id))
            await message.add_reaction(output.tool_args.emoji)
            return self.create_tool_return_json(output.tool_args.tool_type, "Reaction added.")
        
        if output.tool_args.tool_type == "generate_image":
            if message.author.id == self.bot.dev_id:
                await message.reply(f"-# Calling tool: {output.tool_args.tool_type}", mention_author=False, view=ButtonView(output.reasoning, self.bot.dev_id))
            image = await self.img.generate_image(output.tool_args.prompt)
            return self.create_tool_return_json(output.tool_args.tool_type, image)
        
        return self.create_error_json(output.tool_args.tool_type, Exception("Tool not found."))