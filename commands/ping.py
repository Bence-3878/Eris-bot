import discord
from discord import app_commands




# -*- coding: utf-8 -*-
# commands/ping.py
# Ping parancs

import discord
from discord import app_commands


def create_ping_command(client):
    """
    Ping parancs létrehozása (guild-specifikus verzióhoz)
    
    Returns:
        app_commands.Command: A parancs objektum
    """
    
    @app_commands.command(name="ping", description="Bot válaszideje")
    async def ping(interaction: discord.Interaction):
        """Válaszidő mérése"""
        latency_ms = round(client.latency * 1000)
        await interaction.response.send_message(
            f"Pong! Válaszidő: {latency_ms} ms"
        )
    
    return ping


def register_ping_command(tree, client, guild=None):
    """
    Ping parancs regisztrálása
    
    Args:
        tree: CommandTree példány
        client: Discord Client példány
        guild: Ha megadod, akkor csak erre a guild-re regisztrálja
    """
    ping_cmd = create_ping_command(client)
    
    if guild:
        # Guild-specifikus regisztráció
        tree.add_command(ping_cmd, guild=guild)
    else:
        # Globális regisztráció
        tree.add_command(ping_cmd)
    
    return ping_cmd
