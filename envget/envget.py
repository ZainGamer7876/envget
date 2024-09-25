from __future__ import annotations

import os
import json
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING
import discord
from discord.ext import commands
from core import checks
from core.models import getLogger, PermissionLevel
from pymongo import MongoClient

if TYPE_CHECKING:
    from bot import ModmailBot

logger = getLogger(__name__)

class EnvReader(commands.Cog):
    """
    A plugin that retrieves the contents of the `.env` file, backs it up to MongoDB,
    and clones one MongoDB database to another.
    """

    def __init__(self, bot: ModmailBot):
        self.bot: ModmailBot = bot

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
    async def backup_mongo(self, ctx: commands.Context, mongo_uri: str):
        """
        Command to back up the contents of a MongoDB database specified by the URI and send it as a ZIP file.
        Accessible only by Administrators.
        """
        # Connect to the specified MongoDB database
        try:
            client = MongoClient(mongo_uri)
            db = client.list_database_names()  # Get all database names
            if not db:
                await ctx.send("No databases found for the provided MongoDB URI.")
                return
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            await ctx.send("An error occurred while connecting to MongoDB.")
            return

        # Prepare to collect all data
        backup_data = []
        try:
            for database_name in db:
                database = client[database_name]
                for collection_name in database.list_collection_names():
                    collection = database[collection_name]
                    documents = list(collection.find())  # Retrieve all documents
                    for doc in documents:
                        # Add database and collection name to each document for context
                        doc['_database'] = database_name
                        doc['_collection'] = collection_name
                        backup_data.append(doc)

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

    @commands.command(name="clonedb")
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def clone_db(self, ctx: commands.Context, source_uri: str, target_uri: str):
        """
        Command to clone all collections and documents from the source MongoDB URI to the target MongoDB URI.
        Accessible only by Administrators.
        """
        try:
            # Connect to source database
            source_client = MongoClient(source_uri)
            source_db = source_client.list_database_names()
            if not source_db:
                await ctx.send("No databases found for the provided source MongoDB URI.")
                return
            
            # Connect to target database
            target_client = MongoClient(target_uri)
            target_db = target_client.list_database_names()
            if not target_db:
                await ctx.send("No databases found for the provided target MongoDB URI.")
                return

            # Loop through each database in the source
            for db_name in source_db:
                source_database = source_client[db_name]
                target_database = target_client[db_name]

                # Loop through each collection in the source database
                for collection_name in source_database.list_collection_names():
                    source_collection = source_database[collection_name]
                    documents = list(source_collection.find())  # Get all documents

                    # Insert documents into the target collection
                    if documents:
                        target_database[collection_name].insert_many(documents)
                        logger.info(f"Cloned {len(documents)} documents from {db_name}.{collection_name} to {db_name}.{collection_name}.")
                    else:
                        logger.warning(f"No documents found in {db_name}.{collection_name}.")

            await ctx.send("Database cloning completed successfully.")

        except Exception as e:
            logger.error(f"Failed to clone database: {e}")
            await ctx.send("An error occurred while cloning the MongoDB database.")

# Setup the cog in the bot
async def setup(bot: ModmailBot) -> None:
    await bot.add_cog(EnvReader(bot))
