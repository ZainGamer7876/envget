from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from core import checks
from core.models import getLogger, PermissionLevel

if TYPE_CHECKING:
    from bot import ModmailBot

logger = getLogger(__name__)

class EnvReader(commands.Cog):
    """
    A plugin that lists the contents of the `.env` file in the bot's directory.
    """

    def __init__(self, bot: ModmailBot):
        self.bot: ModmailBot = bot

    @commands.command(name="showenv")
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def show_env(self, ctx: commands.Context):
        """
        Command to display the contents of the `.env` file.
        Accessible only by Administrators.
        """
        env_path = Path(__file__).parent.parent / ".env"

        # Check if the .env file exists
        if not env_path.exists():
            await ctx.send("`.env` file not found.")
            return

        # Read the contents of the .env file
        try:
            with open(env_path, "r") as f:
                env_contents = f.read()
            
            # Send the content in chunks if too long for one message
            if len(env_contents) > 2000:
                for chunk in [env_contents[i:i+2000] for i in range(0, len(env_contents), 2000)]:
                    await ctx.send(f"```env\n{chunk}```")
            else:
                await ctx.send(f"```env\n{env_contents}```")

        except Exception as e:
            logger.error(f"Failed to read .env file: {e}")
            await ctx.send("An error occurred while reading the `.env` file.")

async def setup(bot: ModmailBot) -> None:
    await bot.add_cog(EnvReader(bot))
