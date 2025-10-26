import discord
from discord import app_commands




# -*- coding: utf-8 -*-
# commands/ping.py
# Ping parancs

import discord
from discord import app_commands


def create_ping_command_guild(client):
    """
    Ping parancs guild-ekhez (szerverekhez)
    
    Returns:
        app_commands.Command: A parancs objektum
    """
    
    @app_commands.command(name="ping", description="Bot válaszideje")
    @app_commands.allowed_installs(guilds=True, users=False)  # CSAK guild-ekben
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)  # CSAK guild-ekben
    async def ping(interaction: discord.Interaction):
        """Válaszidő mérése szervereken"""
        latency_ms = round(client.latency * 1000)
        
        await interaction.response.send_message(
            f"🏓 Pong a(z) **{interaction.guild.name}** szerveren!\n"
            f"⏱️ Válaszidő: **{latency_ms} ms**"
        )
    
    return ping


def create_ping_command_dm(client):
    """
    Ping parancs DM-ekhez (privát üzenetekhez)
    
    Returns:
        app_commands.Command: A parancs objektum
    """
    
    @app_commands.command(name="ping", description="Bot válaszideje")
    @app_commands.allowed_installs(guilds=False, users=True)  # CSAK user install (DM)
    @app_commands.allowed_contexts(guilds=False, dms=True, private_channels=True)  # CSAK DM-ekben
    async def ping(interaction: discord.Interaction):
        """Válaszidő mérése DM-ben"""
        latency_ms = round(client.latency * 1000)
        
        await interaction.response.send_message(
            f"🏓 Pong **privát üzenetben**!\n"
            f"⏱️ Válaszidő: **{latency_ms} ms**\n\n"
            f"💡 *Ez a parancs csak privát üzenetekben érhető el.*"
        )
    
    return ping


def register_ping_command(tree, client, guild=None):
    """
    Ping parancs regisztrálása guild-ekhez
    
    Args:
        tree: CommandTree példány
        client: Discord Client példány
        guild: A szerver, ahova regisztrálni kell
    """
    ping_cmd = create_ping_command_guild(client)
    
    if guild:
        # Guild-specifikus regisztráció
        tree.add_command(ping_cmd, guild=guild)
    else:
        # Globális regisztráció (de ez nem lesz használva)
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
