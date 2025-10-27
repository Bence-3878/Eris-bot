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
        await interaction.response.defer(ephemeral=False)
        # Nyelv meghatározása a szerver alapján
        lang = language_manager.get_language_for_context(interaction)

        commands_categories = language_manager.get_all_categories(lang)

        embed = discord.Embed(
            title=language_manager.get_text(lang, "help", "title")
        )

        for category in commands_categories:
            embed.add_field(
                name=language_manager.get_category_name(lang, category),
                value=language_manager.get_category_description(lang, category),
                inline=False
            )

        # Add navigation buttons
        view = discord.ui.View()
        for category in commands_categories:
            button = discord.ui.Button(
                label=language_manager.get_category_name(lang, category),
                style=discord.ButtonStyle.primary,
                custom_id=f"help_{category}"
            )

            async def button_callback(interaction: discord.Interaction):
                category = interaction.data["custom_id"].split("_")[1]
                category_embed = discord.Embed(
                    title=language_manager.get_category_name(lang, category),
                    description=language_manager.get_category_description(lang, category)
                )
                command_list = language_manager.get_all_commands(lang, category)

                for command in command_list:
                    category_embed.add_field(
                        name=command,
                        value=language_manager.get_command_description(lang, command),
                        inline=False
                    )
                await interaction.response.edit_message(embed=category_embed)

            button.callback = button_callback
            view.add_item(button)

        await interaction.followup.send(embed=embed, view=view)

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
        await interaction.response.defer(ephemeral=False)
        
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