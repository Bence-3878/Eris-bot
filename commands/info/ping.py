# -*- coding: utf-8 -*-
# commands/ping.py
# Ping parancs

import discord
from discord import app_commands, Locale
from languages.languages import language_manager


def create_ping_command_guild(client):
    """
    Ping parancs guild-ekhez (szerverekhez)
    Returns:
        app_commands.Command: A parancs objektum
    """
    @app_commands.command(
        name="ping",
        description="Bot response time"
    )
    @app_commands.describe()  # Lokalizációhoz
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    async def ping(interaction: discord.Interaction):
        """Válaszidő mérése szervereken"""

        # Nyelv meghatározása a szerver alapján
        await ping_logic(client, interaction, language_manager.get_language_for_context(interaction))
    
    # Lokalizált leírások hozzáadása
    ping.description_localizations = {
        Locale.hungarian: "Bot válaszideje",
        Locale.american_english: "Bot response time",
        Locale.british_english: "Bot response time"
    }
    
    return ping


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
        """Válaszidő mérése DM-ben (mindig angolul)"""
        # DM esetén mindig angol
        await ping_logic(client, interaction, "en")
    
    # Lokalizált leírások hozzáadása
    ping.description_localizations = {
        Locale.hungarian: "Bot válaszideje",
        Locale.american_english: "Bot response time",
        Locale.british_english: "Bot response time"
    }
    
    return ping

async def ping_logic(client, interaction: discord.Interaction, lang_code: str):
    latency_ms = round(client.latency * 1000)

    # Fordítások lekérése
    pong_text = language_manager.get_text(lang_code, "ping", "Pong!")
    bot_latency_text = language_manager.get_text(lang_code, "ping", "Bot Latency", latency_ms)

    await interaction.response.send_message(
        f"{pong_text}\n{bot_latency_text}"
    )


def register_ping_command(tree, client, guild=None):
    """
    Ping parancs regisztrálása guild-ekhez
    
    Args:
        tree: CommandTree példány
        client: Discord Client példány
        guild: A szerver, ahova regisztrálni kell
    """
    ping_cmd = create_ping_command_guild(client)
    
    # Guild-specifikus description beállítása
    if guild:
        # Szerver nyelve alapján description módosítás
        guild_locale = str(guild.preferred_locale)
        
        if guild_locale == "hu":
            ping_cmd.description = "Bot válaszideje"
        else:
            ping_cmd.description = "Bot response time"
        
        tree.add_command(ping_cmd, guild=guild)
    else:
        tree.add_command(ping_cmd)
    
    return ping_cmd


def register_ping_command_dm(tree, client):
    """
    Ping parancs regisztrálása DM-ekhez (globálisan)
    
    Args:
        tree: CommandTree példány
        client: Discord Client példány
    """
    ping_cmd = create_ping_command_dm(client)
    tree.add_command(ping_cmd)  # Globális, de csak DM-ben működik
    return ping_cmd
