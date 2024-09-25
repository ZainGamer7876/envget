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
import json

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
        Command to back up the contents of the MongoDB database and send it as a ZIP file.
        Accessible only by Administrators.
        """
        # Retrieve data from MongoDB
        backup_data = []
        try:
            for document in self.collection.find():  # Retrieve documents from the MongoDB collection
                backup_data.append(document)

            if not backup_data:
                await ctx.send("No data found in MongoDB to back up.")
                return

            # Create a JSON file from the backup data
            json_filename = "/home/container/AKModMail/mongo_backup.json"
            with open(json_filename, 'w') as json_file:
                json.dump(backup_data, json_file, default=str)  # Use default=str to handle ObjectId and other non-serializable types

            # Create a ZIP file containing the JSON backup
            zip_filename = "/home/container/AKModMail/mongo_backup.zip"
            with zipfile.ZipFile(zip_filename, 'w') as zipf:
                zipf.write(json_filename, arcname='mongo_backup.json')  # Store only the filename in the ZIP
            
            logger.info("MongoDB backup ZIP file created successfully.")

            # Send the ZIP file to Discord
            with open(zip_filename, 'rb') as zip_file:
                await ctx.send(file=discord.File(zip_file, filename='mongo_backup.zip'))
            
            logger.info("MongoDB backup ZIP file sent successfully.")

        except Exception as e:
            logger.error(f"Failed to back up MongoDB data: {e}")
            await ctx.send("An error occurred while backing up the MongoDB data.")

# Setup the cog in the bot
async def setup(bot: ModmailBot) -> None:
    await bot.add_cog(EnvReader(bot))
