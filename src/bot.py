from __future__ import annotations

import sys
import logging
from pathlib import Path
import coloredlogs

import discord
from discord.ext import commands
from decouple import config

class Bot(commands.Bot):
    def __init__(self) -> None:
        self._setup_logging()
        self.backend = config('BACKEND_TYPE', default='openai')
        self.server_name = "Euphoria"
        self.bot_name = "bot3"
        self.persona = config("PERSONA", default="A deep thinker named bot3.")
        self.dev_id = config('DEV_ID', cast=int)
        self._log_startup()
        
        super().__init__(
            command_prefix=':',
            intents=discord.Intents.all(),
            case_insensitive=True,
            description=f"{self.bot_name} - An experimental deep thinker."
        )
        
    def _log_startup(self) -> None:
        self.logger.info(f'Starting {self.bot_name}...')
        self.logger.info(f'Backend type: {self.backend}')
        self.logger.info(f'Developer ID: {self.dev_id}')

    def _setup_logging(self) -> None:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        self.logger = logging.getLogger(__name__)
        coloredlogs.install(level='INFO', logger=self.logger)

    async def setup_hook(self) -> None:
        await self._load_extensions()

    async def _load_extensions(self) -> None:
        cogs_dir = Path('./src/cogs')
        
        if not cogs_dir.exists():
            self.logger.error(f'Cogs directory not found: {cogs_dir}')
            return

        for cog_file in cogs_dir.glob('*.py'):
            if cog_file.name == '__init__.py':
                continue

            try:
                await self.load_extension(f'cogs.{cog_file.stem}')
                self.logger.info(f'Loaded extension: {cog_file.stem}')
            except Exception as e:
                self.logger.error(f'Failed to load {cog_file.stem}: {e}')

        try:
            synced = await self.tree.sync()
            self.logger.info(f'Synced {len(synced)} application commands')
        except discord.HTTPException as e:
            self.logger.error(f'Failed to sync commands: {e}')

    async def on_ready(self) -> None:
        await self._set_presence()
        
        self.logger.info(f'Bot is ready! Logged in as {self.user} (ID: {self.user.id})')

    async def _set_presence(self) -> None:
        await self.change_presence(
            status=discord.Status.idle,
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name="with my thoughts"
            )
        )

def main() -> None:
    bot = Bot()
    token = config('DISCORD_TOKEN')

    if not token:
        bot.logger.critical('No Discord token provided in configuration')
        sys.exit(1)

    try:
        bot.run(token, log_handler=None)
    except discord.LoginFailure:
        bot.logger.critical('Invalid Discord token provided')
        sys.exit(1)
    except Exception as e:
        bot.logger.critical(f'Failed to start bot: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main()