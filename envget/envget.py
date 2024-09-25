from __future__ import annotations

import os
import zipfile
from pathlib import Path
import shutil
import discord
from discord.ext import commands
from pymongo import MongoClient, errors
import json
import asyncio

from core import checks
from core.models import getLogger, PermissionLevel

logger = getLogger(__name__)

class EnvMongoManager(commands.Cog):
    """
    A plugin that manages the .env file and MongoDB backups.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="getenv")
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def getenv(self, ctx: commands.Context):
        """
        Command to display the contents of the `.env` file.
        Accessible only by Administrators.
        """
        env_path = Path("/home/container/AKModMail/.env")

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
                for chunk in [env_contents[i:i + 2000] for i in range(0, len(env_contents), 2000)]:
                    await ctx.send(f"```env\n{chunk}```")
            else:
                await ctx.send(f"```env\n{env_contents}```")

        except Exception as e:
            logger.error(f"Failed to read .env file: {e}")
            await ctx.send("An error occurred while reading the `.env` file.")

    @commands.command(name="backupmongo")
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def backupmongo(self, ctx: commands.Context, mongo_uri: str):
        """
        Command to backup MongoDB contents and send as a zip file.
        Usage: .backupmongo <mongo_uri>
        """
        await ctx.send("Starting MongoDB backup...")

        try:
            client = MongoClient(mongo_uri)
            db_names = client.list_database_names()

            # Create a zip file for backup
            zip_filename = "mongodb_backup.zip"
            with zipfile.ZipFile(zip_filename, 'w') as zipf:
                for db_name in db_names:
                    db = client[db_name]
                    collection_names = db.list_collection_names()
                    for collection_name in collection_names:
                        documents = db[collection_name].find()
                        with open(f"{collection_name}.json", "w") as json_file:
                            json.dump(list(documents), json_file)
                        zipf.write(f"{collection_name}.json")
                        os.remove(f"{collection_name}.json")  # Remove the json file after zipping

            await ctx.send(file=discord.File(zip_filename))
            os.remove(zip_filename)  # Clean up the zip file after sending

        except errors.ConfigurationError:
            await ctx.send("Configuration Error: Please check your MongoDB URI format.")
            logger.error("Configuration Error: Invalid MongoDB URI.")
        except errors.OperationFailure as e:
            if "authentication failed" in str(e):
                await ctx.send("Authentication Error: Please check your MongoDB username and password.")
                logger.error("Authentication Error: %s", e)
            else:
                await ctx.send(f"Operation Failed: {str(e)}")
                logger.error("Operation Failure: %s", e)
        except Exception as e:
            await ctx.send("An error occurred while backing up MongoDB.")
            logger.error(f"An unexpected error occurred: {e}")

    @commands.command(name="clonedb")
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def clonedb(self, ctx: commands.Context, uri1: str, uri2: str):
        """
        Command to clone data from one MongoDB database to another.
        Usage: .clonedb <source_uri> <destination_uri>
        """
        await ctx.send("Cloning database...")

        try:
            source_client = MongoClient(uri1)
            destination_client = MongoClient(uri2)

            source_db_names = source_client.list_database_names()
            for db_name in source_db_names:
                source_db = source_client[db_name]
                destination_db = destination_client[db_name]

                # Clone each collection
                for collection_name in source_db.list_collection_names():
                    source_collection = source_db[collection_name]
                    documents = source_collection.find()
                    destination_db[collection_name].insert_many(documents)

            await ctx.send("Database cloned successfully.")
            logger.info("Database cloned from %s to %s", uri1, uri2)

        except errors.ConfigurationError:
            await ctx.send("Configuration Error: Please check your MongoDB URI format.")
            logger.error("Configuration Error: Invalid MongoDB URI.")
        except errors.OperationFailure as e:
            if "authentication failed" in str(e):
                await ctx.send("Authentication Error: Please check your MongoDB username and password.")
                logger.error("Authentication Error: %s", e)
            else:
                await ctx.send(f"Operation Failed: {str(e)}")
                logger.error("Operation Failure: %s", e)
        except Exception as e:
            await ctx.send("An error occurred while cloning the database.")
            logger.error(f"An unexpected error occurred: {e}")

async def setup(bot):
    await bot.add_cog(EnvMongoManager(bot))
