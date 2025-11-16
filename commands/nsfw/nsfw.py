# -*- coding: utf-8 -*-
# 2.0.0
# nsfw.py

import discord
import os                                     
import random
from discord import app_commands, Locale


from languages.languages import language_manager


def create_nsfw_command_guild(client):
    @app_commands.command(
        name="nsfw", nsfw=True
    )
    @app_commands.describe(amount="How many images do you want?")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    async def nsfw(interaction: discord.Interaction, amount: int = 10):
        await nsfw_logic(interaction, amount)

    return nsfw

def create_nsfw_command_dm(client):
    @app_commands.command(name="nsfw", description="Bot response time")
    @app_commands.describe(amount="")
    @app_commands.allowed_installs(guilds=False, users=True)  # CSAK user install (DM)
    @app_commands.allowed_contexts(guilds=False, dms=True, private_channels=True)  # CSAK DM-ekben
    async def nsfw(interaction: discord.Interaction, amount: int = 10):
        await nsfw_logic(interaction, amount)

    return nsfw


async def nsfw_logic(interaction: discord.Interaction, amount: int = 10):
    # Biztonság: futásidőben is ellenőrizzük, hogy NSFW csatorna
    if not (getattr(getattr(interaction, "channel", None), "is_nsfw", lambda: False) or isinstance(
            interaction.channel, discord.DMChannel)):
        await interaction.response.send_message(
            "Ezt a parancsot csak NSFW csatornában lehet használni.", ephemeral=True)
        return

    # Jelezzük, hogy dolgozunk
    await interaction.response.defer(ephemeral=False)

    if amount < 1:
        amount = 1
    if amount > 10:
        amount = 10

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

        # Több random kép választása
        selected_files = random.sample(files, min(amount, len(files)))
        image_files = [discord.File(os.path.join(user_folder, f)) for f in selected_files]

        # Képek küldése egy üzenetben
        await interaction.followup.send(
            files=image_files,
            ephemeral=False
        )

    except Exception as e:
        await interaction.followup.send(f"Hiba történt: {str(e)}", ephemeral=True)


def register_nsfw_commands(tree, client, guild=None):
    cmd = create_nsfw_command_guild(client)
    cmd.default_member_permissions = discord.Permissions(send_messages=True)
    cmd.default_guild_permissions = discord.Permissions(send_messages=True)
    cmd.guild_only = True
    cmd.dm_permission = False

    cmd.description_localizations = {
        Locale.hungarian: language_manager.get_command_description("hu", cmd.name),
        Locale.american_english: language_manager.get_command_description("en", cmd.name),
        Locale.british_english: language_manager.get_command_description("en", cmd.name)
    }
    # Guild-specifikus description beállítása
    if guild:
        # Szerver nyelve alapján description módosítás
        guild_locale = str(guild.preferred_locale)
        languages = language_manager.get_all_available_languages()

        for lang in languages:
            if language_manager.discord_lang_code(lang) == guild_locale:
                cmd.description = language_manager.get_command_description(lang, cmd.name)

        mapped = language_manager.locale_mapping.get(guild_locale)
        if mapped not in languages:
            cmd.description = language_manager.get_command_description("en", cmd.name)

        tree.add_command(cmd, guild=guild)
    else:
        tree.add_command(cmd)

    return cmd

def register_nsfw_command_dm(tree, client):
    cmd = create_nsfw_command_guild(client)
    tree.add_command(cmd)  # Globális, de csak DM-ben működik
    return cmd
