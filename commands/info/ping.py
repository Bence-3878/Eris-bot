# -*- coding: utf-8 -*-
# commands/ping.py
import discord
from discord import app_commands


def create_ping_command_guild(client):
    """
    Ping parancs létrehozása guild-ekhez
    
    Args:
        client: Discord Client példány
        
    Returns:
        app_commands.Command: A ping parancs
    """
    @app_commands.command(name="ping", description="Bot response time")
    async def ping_command(interaction: discord.Interaction):
        """Ping parancs - bot válaszidő mérése"""
        latency = round(client.latency * 1000)
        await interaction.response.send_message(
            f"🏓 Pong! Latency: {latency}ms",
            ephemeral=True
        )
    
    return ping_command


def create_ping_command_dm(client):
    """
    Ping parancs létrehozása DM-ekhez
    
    Args:
        client: Discord Client példány
        
    Returns:
        app_commands.Command: A ping parancs DM verzió
    """
    @app_commands.command(name="ping", description="Bot response time")
    async def ping_command_dm(interaction: discord.Interaction):
        """Ping parancs DM verzió - bot válaszidő mérése"""
        latency = round(client.latency * 1000)
        await interaction.response.send_message(
            f"🏓 Pong! Latency: {latency}ms"
        )
    
    return ping_command_dm


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
    Ping parancs regisztrálása DM-ekhez (globális)
    
    Args:
        tree: CommandTree példány
        client: Discord Client példány
    """
    ping_cmd = create_ping_command_dm(client)
    tree.add_command(ping_cmd)
    
    return ping_cmd



