from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING
import discord
from discord.ext import commands
from core import checks
from core.models import getLogger, PermissionLevel
from pymongo import MongoClient
import zipfile

if TYPE_CHECKING:
    from bot import ModmailBot

logger = getLogger(__name__)

class EnvReader(commands.Cog):
    """
    A plugin that retrieves the contents of the `.env` file and backs it up to MongoDB.
    """

    def __init__(self, bot: ModmailBot):
        self.bot: ModmailBot = bot
        self.mongo_uri = "mongodb+srv://akmodm:aegisadmin123@modmail.okdwktk.mongodb.net"
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client['env_backup']  # Change to your desired database name
        self.collection = self.db['backups']  # Change to your desired collection name

    @commands.command(name="getenv")
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def getenv(self, ctx: commands.Context):
        """
        Command to send the contents of the `.env` file as a ZIP file.
        Accessible only by Administrators.
        """
        # Set the path to the .env file in /home/container/AKModMail
        env_path = Path("/home/container/AKModMail/.env")

        # Log the path for debugging
        logger.info(f"Looking for .env file at: {env_path}")

        # Check if the .env file exists
        if not env_path.exists():
            await ctx.send("`.env` file not found in `/home/container/AKModMail/`.")
            return

        # Create a ZIP file containing the .env file
        zip_filename = "/home/container/AKModMail/env_backup.zip"
        try:
            with zipfile.ZipFile(zip_filename, 'w') as zipf:
                zipf.write(env_path, arcname=".env")  # Use arcname to store just the filename
            logger.info("ZIP file created successfully.")

            # Send the ZIP file to Discord
            with open(zip_filename, 'rb') as zip_file:
                await ctx.send(file=discord.File(zip_file, filename='env_backup.zip'))
            
            logger.info("ZIP file sent successfully.")

        except Exception as e:
            logger.error(f"Failed to create or send ZIP file: {e}")
            await ctx.send("An error occurred while creating or sending the ZIP file.")

    @commands.command(name="backupmongo")
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def backup_mongo(self, ctx: commands.Context):
        """
        Command to back up the contents of the `.env` file to MongoDB.
        Accessible only by Administrators.
        """
        # Set the path to the .env file in /home/container/AKModMail
        env_path = Path("/home/container/AKModMail/.env")

        # Log the path for debugging
        logger.info(f"Looking for .env file at: {env_path}")

        # Check if the .env file exists
        if not env_path.exists():
            await ctx.send("`.env` file not found in `/home/container/AKModMail/`.")
            return

        # Read the contents of the .env file
        try:
            with open(env_path, "r") as f:
                env_contents = f.read()

            # Backup the contents to MongoDB
            backup_data = {
                "content": env_contents,
                "backup_time": discord.utils.utcnow()  # Use the current UTC time
            }
            self.collection.insert_one(backup_data)
            logger.info("Backup to MongoDB successful.")

            await ctx.send("`.env` file backed up to MongoDB successfully.")

        except Exception as e:
            logger.error(f"Failed to read .env file or back it up: {e}")
            await ctx.send("An error occurred while backing up the `.env` file to MongoDB.")

# Setup the cog in the bot
async def setup(bot: ModmailBot) -> None:
    await bot.add_cog(EnvReader(bot))
