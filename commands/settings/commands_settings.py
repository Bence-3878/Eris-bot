# -*- coding: utf-8 -*-
# commands_settings.py
# Szerver beállítások kezelő parancsok

import discord
from discord import app_commands
from discord.enums import Locale
from config import config
from guild_settings.guild_settings import guild_settings


def create_settings_command(client, guild_settings):
    """
    Szerver beállítások parancs létrehozása
    
    Args:
        client: A Discord bot kliens
        guild_settings: A GuildSettings példány
    
    Returns:
        app_commands.Group: A parancs csoport
    """
    
    settings_group = app_commands.Group(
        name="settings",
        description="Szerver parancsok beállításai",
        description_localizations={
            Locale.hungarian: "Szerver parancsok beállításai",
            Locale.american_english: "Server command settings",

        }
    )
    
    @settings_group.command(
        name="list",
        description="Engedélyezett parancsok listája"
    )
    @app_commands.describe()
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    async def list_commands(interaction: discord.Interaction):
        """Szerver engedélyezett parancsainak listázása"""
        
        enabled_commands = guild_settings.get_guild_commands(interaction.guild_id)
        all_commands = guild_settings.get_all_available_commands()
        
        embed = discord.Embed(
            title="📋 Szerver Parancsok",
            description=f"Beállítások a(z) **{interaction.guild.name}** szerverhez",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="✅ Engedélyezett parancsok",
            value=", ".join([f"`{cmd}`" for cmd in enabled_commands]) if enabled_commands else "Nincs",
            inline=False
        )
        
        disabled = [cmd for cmd in all_commands if cmd not in enabled_commands]
        embed.add_field(
            name="❌ Letiltott parancsok",
            value=", ".join([f"`{cmd}`" for cmd in disabled]) if disabled else "Nincs",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    @settings_group.command(
        name="enable",
        description="Parancs engedélyezése"
    )
    @app_commands.describe(command="A parancs neve")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    async def enable_command(interaction: discord.Interaction, command: str):
        """Parancs engedélyezése a szerveren"""
        
        all_commands = guild_settings.get_all_available_commands()
        
        if command not in all_commands:
            await interaction.response.send_message(
                f"❌ A(z) `{command}` parancs nem létezik!\n"
                f"Elérhető parancsok: {', '.join([f'`{cmd}`' for cmd in all_commands])}",
                ephemeral=True
            )
            return
        
        success = guild_settings.enable_command(interaction.guild_id, command)
        
        if success:
            await interaction.response.send_message(
                f"✅ A(z) `{command}` parancs sikeresen engedélyezve!",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"ℹ️ A(z) `{command}` parancs már engedélyezve van.",
                ephemeral=True
            )
    
    @settings_group.command(
        name="disable",
        description="Parancs letiltása"
    )
    @app_commands.describe(command="A parancs neve")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.bot_has_permissions(embed_links=True)
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    async def disable_command(interaction: discord.Interaction, command: str):
        """Parancs letiltása a szerveren"""
        
        all_commands = guild_settings.get_all_available_commands()
        
        if command not in all_commands:
            await interaction.response.send_message(
                f"❌ A(z) `{command}` parancs nem létezik!\n"
                f"Elérhető parancsok: {', '.join([f'`{cmd}`' for cmd in all_commands])}",
                ephemeral=True
            )
            return
        
        success = guild_settings.disable_command(interaction.guild_id, command)
        
        if success:
            await interaction.response.send_message(
                f"✅ A(z) `{command}` parancs sikeresen letiltva!",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"ℹ️ A(z) `{command}` parancs már le van tiltva.",
                ephemeral=True
            )
    
    # Lokalizációk hozzáadása
    list_commands.description_localizations = {
        Locale.hungarian: "Engedélyezett parancsok listája",
        Locale.american_english: "List enabled commands"
    }
    
    enable_command.description_localizations = {
        Locale.hungarian: "Parancs engedélyezése",
        Locale.american_english: "Enable a command"
    }
    
    disable_command.description_localizations = {
        Locale.hungarian: "Parancs letiltása",
        Locale.american_english: "Disable a command"
    }
    
    return settings_group


def register_settings_commands(tree, client, guild_settings):
    """
    Settings parancsok regisztrálása
    
    Args:
        tree: A CommandTree példány
        client: A Discord bot kliens
        guild_settings: A GuildSettings példány
    """
    settings_cmd = create_settings_command(client, guild_settings)
    tree.add_command(settings_cmd)
    print("✓ Settings parancsok regisztrálva")