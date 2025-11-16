# -*- coding: utf-8 -*-
# 2.0.0
# nsfw.py

import discord
import os                                     
import random
from discord import app_commands

def create_ping_command_guild(client):
    @app_commands.command(
        name="nsfw", nsfw=True
    )
    @app_commands.describe()  # Lokalizációhoz
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    async def ping(interaction: discord.Interaction):
        await nsfw_logic(interaction)

def create_ping_command_dm(client):
    """
    Ping parancs DM-ekhez (privát üzenetekhez)

    Returns:
        app_commands.Command: A parancs objektum
    """

    @app_commands.command(name="ping", description="Bot response time")
    @app_commands.allowed_installs(guilds=False, users=True)  # CSAK user install (DM)
    @app_commands.allowed_contexts(guilds=False, dms=True, private_channels=True)  # CSAK DM-ekben
    async def ping(interaction: discord.Interaction):
        await nsfw_logic(interaction)

async def nsfw_logic(interaction: discord.Interaction):
    # Biztonság: futásidőben is ellenőrizzük, hogy NSFW csatorna
    if not (getattr(getattr(interaction, "channel", None), "is_nsfw", lambda: False) or isinstance(
            interaction.channel, discord.DMChannel)):
        await interaction.response.send_message(
            "Ezt a parancsot csak NSFW csatornában lehet használni.", ephemeral=True)
        return

    # Jelezzük, hogy dolgozunk
    await interaction.response.defer(ephemeral=False)

    target = interaction.user
    user_folder = f"/home/bence/Hentai"

    # Ellenőrizzük/létrehozzuk a mappát
    if not os.path.exists(user_folder):
        try:
            os.makedirs(user_folder)
        except Exception as e:
            await interaction.followup.send("Hiba történt a mappa létrehozásakor", ephemeral=True)
            return

    # Képek listázása
    try:
        files = [f for f in os.listdir(user_folder)
                 if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]

        if not files:
            await interaction.followup.send("Nincs kép a mappában", ephemeral=True)
            return

        # Random kép választása
        image_path = os.path.join(user_folder, random.choice(files))

        # Kép küldése
        await interaction.followup.send(
            file=discord.File(image_path),
            ephemeral=False
        )

    except Exception as e:
        await interaction.followup.send(f"Hiba történt: {str(e)}", ephemeral=True)

