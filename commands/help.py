# -*- coding: utf-8 -*-
# commands/ping.py
# Ping parancs

import discord
from discord import app_commands, Locale
from languages.languages import language_manager

def create_help_command_guild(client):
    """
    Help parancs guild-ekhez (szerverekhez)
    Returns:
        app_commands.Command: A parancs objektum
    """
    @app_commands.command(
        name="help",
        description="Show available commands and their descriptions"
    )
    @app_commands.describe()  # Lokalizációhoz
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    async def help_command(interaction: discord.Interaction):
        """Show available commands and their descriptions on servers"""
        # Nyelv meghatározása a szerver alapján
        lang = language_manager.get_language_for_context(interaction)
        
        # Parancsok és leírások összegyűjtése
        commands_list = [
            (command.name, language_manager.get_command_description(lang, command.name))
            for command in interaction.client.tree.get_commands()
        ]

        help_text = "\n".join(f"{name}: {description}" for name, description in commands_list)

        await interaction.response.send_message(
            help_text
        )
    
    # Lokalizált leírások hozzáadása
    help_command.description_localizations = {
        Locale.hungarian: "Elérhető parancsok és leírásuk megjelenítése",
        Locale.american_english: "Show available commands and their descriptions",
        Locale.british_english: "Show available commands and their descriptions"
    }
    
    return help_command

def create_help_command_dm(client):
    """
    Help parancs DM-ekhez (privát üzenetekhez)
    Returns:
        app_commands.Command: A parancs objektum
    """
    @app_commands.command(name="help", description="Show available commands and their descriptions")
    @app_commands.allowed_installs(guilds=False, users=True)  # CSAK user install (DM)
    @app_commands.allowed_contexts(guilds=False, dms=True, private_channels=True)  # CSAK DM-ekben
    async def help_command(interaction: discord.Interaction):
        """Show available commands and their descriptions in DMs (always in English)"""
        
        # Parancsok és leírások összegyűjtése
        commands_list = [
            (command.name, command.description)
            for command in interaction.client.tree.get_commands()
        ]

        help_text = "\n".join(f"{name}: {description}" for name, description in commands_list)

        await interaction.response.send_message(
            help_text
        )
    
    return help_command

def register_help_command(tree, client, guild):
    """
    Help parancs regisztrálása guild-ekhez (szerverekhez)
    """
    help_cmd = create_help_command_guild(client)
    tree.add_command(help_cmd, guild=guild) 
    return help_cmd

def register_help_command_dm(tree, client):
    """
    Help parancs regisztrálása DM-ekhez (privát üzenetekhez)
    """
    help_cmd = create_help_command_dm(client)
    tree.add_command(help_cmd) 
    return help_cmd