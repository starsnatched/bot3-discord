import discord
from discord import Interaction as I
from discord import app_commands
from discord.ext import commands

from services.infer import OpenAI, Ollama
from utils.discord_utils import DiscordUtils
from utils.models import ReasoningModel
from services.database import DatabaseService
from utils.get_prompt import generate_system_prompt

from typing import Optional, Dict
from decouple import config
import json
import logging
import asyncio

class AI(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.dc_utils = DiscordUtils(bot=bot)
        self.db = DatabaseService()
        self.logger = logging.getLogger(__name__)
        self.ongoing_tasks: Dict[int, asyncio.Task] = {}
        self._get_client()
        
    def _get_client(self):
        if self.bot.backend == 'openai':
            self.client = OpenAI()
        elif self.bot.backend == 'ollama':
            self.client = Ollama()
        else:
            raise ValueError("Invalid backend type.")

    async def cog_load(self):
        await self.db.init_db()

    def create_message_json(self, message: discord.Message) -> str:
        if message.reference and len(message.reference.resolved.content) > 30:
            message.reference.resolved.content = message.reference.resolved.content[:30] + "..."
            
        return json.dumps({
            "message_type": "user_message",
            "user_name": message.author.display_name,
            "user_id": message.author.id,
            "content": message.content,
            "reference_user_id": message.reference.resolved.author.id if message.reference else None,
            "reference": message.reference.resolved.content if message.reference else None,
            "timestamp": message.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }, indent=4)

    def create_error_json(self, tool_type: str, error: Exception) -> str:
        return json.dumps({
            "message_type": "error_message",
            "tool_type": tool_type,
            "content": str(error)
        }, indent=4)

    async def process_ai_response(self, message: discord.Message, response: ReasoningModel) -> Optional[str]:
        try:
            return_json = await self.dc_utils.handle_tools(message, response)
            return return_json
        except Exception as e:
            self.logger.error(f"Error processing AI response: {e}")
            return self.create_error_json(response.tool_args.tool_type, e)

    async def generate_response(self, channel_id: int, system_prompt: str) -> ReasoningModel:
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(await self.db.get_channel_history(channel_id))
        
        response = await self.client.generate_response(messages)
        
        return response

    async def handle_message(self, message: discord.Message):
        channel_id = message.channel.id
        
        if channel_id in self.ongoing_tasks:
            self.ongoing_tasks[channel_id].cancel()
            try:
                await self.ongoing_tasks[channel_id]
            except asyncio.CancelledError:
                pass
            
        try:
            system_prompt = generate_system_prompt(self.bot, message.channel)
            message_json = self.create_message_json(message)
            await self.db.add_message(message.channel.id, "user", message_json, message.attachments[0].url if message.attachments else None)

            async def process_message():
                try:
                    while True:
                        response = await self.generate_response(message.channel.id, system_prompt)
                        return_json = await self.process_ai_response(message, response)
                        
                        del response.reasoning
                        await self.db.add_message(
                            message.channel.id,
                            "assistant", 
                            json.dumps(response.model_dump(), indent=4),
                            None
                        )
                            
                        if response.tool_args.tool_type == "send_message" and not response.tool_args.call_another_tool:
                            break

                        if return_json:
                            await self.db.add_message(message.channel.id, "user", return_json, None)
                        else:
                            break
                        
                finally:
                    if channel_id in self.ongoing_tasks:
                        del self.ongoing_tasks[channel_id]

            task = asyncio.create_task(process_message())
            self.ongoing_tasks[channel_id] = task
            
            try:
                await task
            except asyncio.CancelledError:
                self.logger.info(f"Task cancelled for channel {channel_id}")
            except Exception as e:
                self.logger.error(f"Error in handle_message: {e}", exc_info=True)
                await message.reply("-# An error occurred while processing your message.", mention_author=False)

        except Exception as e:
            self.logger.error(f"Error in handle_message: {e}", exc_info=True)
            await message.reply("-# An error occurred while processing your message.", mention_author=False)

    @app_commands.command(description="Clears the chat history.")
    async def reset(self, i: I):
        await i.response.defer()
        
        if i.user.guild_permissions.manage_messages or i.user.id == self.bot.owner_id:
            await self.db.clear_channel_history(i.channel_id)
            
            await i.followup.send("-# Channel history cleared.")
            
        else:
            await i.followup.send("-# You do not have permission to use this command!")
            
    @app_commands.command(description="Toggles the AI on or off in the current channel.")
    async def toggle(self, i: I):
        await i.response.defer()
        
        if i.user.guild_permissions.manage_messages or i.user.id == self.bot.owner_id:
            if i.channel_id in self.db.get_enabled_channels():
                await self.db.remove_enabled_channel(i.channel_id)
                await i.followup.send("-# AI disabled in this channel.")
                
            else:
                await self.db.remove_disabled_channel(i.channel_id)
                await self.db.add_enabled_channel(i.channel_id)
                await i.followup.send("-# AI enabled in this channel.")
                
        else:
            await i.followup.send("-# You do not have permission to use this command!")
            
    @app_commands.command(description="Disables the AI in the current channel.")
    async def disable(self, i: I):
        await i.response.defer()
        
        if i.user.guild_permissions.manage_messages or i.user.id == self.bot.owner_id:
            if i.channel_id in self.db.get_disabled_channels():
                await i.followup.send("-# AI is already disabled in this channel.")
                return
            
            await self.db.remove_enabled_channel(i.channel_id)
            await self.db.add_disabled_channel(i.channel_id)
            await i.followup.send("-# AI disabled in this channel.")
            
        else:
            await i.followup.send("-# You do not have permission to use this command!")
            
    @app_commands.command(description="Enables the AI in the current channel.")
    async def enable(self, i: I):
        await i.response.defer()
        
        if i.user.guild_permissions.manage_messages or i.user.id == self.bot.owner_id:
            if i.channel_id in self.db.get_enabled_channels():
                await i.followup.send("-# AI is already enabled in this channel.")
                return
            
            await self.db.remove_disabled_channel(i.channel_id)
            await self.db.add_enabled_channel(i.channel_id)
            await i.followup.send("-# AI enabled in this channel.")
            
        else:
            await i.followup.send("-# You do not have permission to use this command!")
            
    @app_commands.command(description="Displays the current AI status in the channel.")
    async def status(self, i: I):
        await i.response.defer()
        
        if i.channel_id in self.db.get_enabled_channels() and i.channel_id not in self.db.get_disabled_channels():
            await i.followup.send("-# AI is currently enabled in this channel.")
        elif i.channel_id not in self.db.get_enabled_channels() and i.channel_id not in self.db.get_disabled_channels():
            await i.followup.send("-# AI is currently set to respond to pings.")
        elif i.channel_id in self.db.get_disabled_channels():
            await i.followup.send("-# AI is currently disabled in this channel.")
        else:
            await i.followup.send("-# An unknown logic occured.")
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.guild is None:
            return
        if message.channel.id in self.db.get_disabled_channels():
            return
        if not self.bot.user.mentioned_in(message) and message.channel.id not in await self.db.get_enabled_channels():
            return
        if not message.content:
            message.content = "[EMPTY MESSAGE]"
        if message.attachments and message.attachments[0].size > 20_000_000:
            await message.reply("-# File size exceeds 20MB. Please upload a smaller file.", mention_author=False)
            return
        if message.attachments and "image/" not in message.attachments[0].content_type:
            await message.reply("-# Only image files are supported.", mention_author=False)
            return
        
        await self.handle_message(message)
        
async def setup(bot: commands.Bot):
    await bot.add_cog(AI(bot))