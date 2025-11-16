# -*- coding: utf-8 -*-
# commands/avater.py
# Avatar parancs

if __name__ == '__main__':
    exit(1)

import discord
from discord import app_commands, Locale
from languages.languages import language_manager


def create_avatar_command(client):
    """Slash parancs: /avatar"""

    @app_commands.command(
        name="avater",
        description="Show user avatar"
    )
    @app_commands.describe(user="The user whose avatar you want to see")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def avatar_command(interaction: discord.Interaction, user: discord.User = None):
        """Show user avatar"""
        if user is None:
            user = interaction.user
        
        await send_avatar_message(interaction, user)
    
    return avatar_command


def create_avatar_context_menu(client):
    """Context Menu parancs: Jobb klikk felhasználóra -> Alkalmazások"""
    
    @app_commands.context_menu(name="Show Avatar")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def avatar_context(interaction: discord.Interaction, user: discord.User):
        """Profilkép megjelenítése context menu-ből"""
        await send_avatar_message(interaction, user)
    
    # Lokalizált nevek
    avatar_context.name_localizations = {
        Locale.hungarian: "Profilkép mutatása",
        Locale.american_english: "Show Avatar",
        Locale.british_english: "Show Avatar"
    }
    
    return avatar_context


async def send_avatar_message(interaction: discord.Interaction, user: discord.User):
    """Közös logika az avatar üzenet küldéséhez"""
    lang_code = language_manager.get_language_for_context(interaction)
    
    if user.avatar.url == user.display_avatar.url:
        msg = language_manager.get_text(lang_code, "avatar", "global",
                                        user.display_name, user.avatar.url)
    else:
        msg = language_manager.get_text(lang_code, "avatar", "guild",
                                        user.display_name, user.avatar.url,
                                        user.display_avatar.url)
    await interaction.response.send_message(msg)


def register_avatar_command(tree, client, guild=None):
    """Slash parancs regisztrálása"""
    avatar_cmd = create_avatar_command(client)
    
    # Guild-specifikus description beállítása
    if guild:
        guild_locale = str(guild.preferred_locale)

        if guild_locale == "hu":
            avatar_cmd.description = language_manager.get_command_description("hu", "avatar")
        else:
            avatar_cmd.description = language_manager.get_command_description("en", "avatar")

    tree.add_command(avatar_cmd, guild=guild)
    
    # Context menu is regisztrálása
    avatar_ctx = create_avatar_context_menu(client)
    tree.add_command(avatar_ctx, guild=guild)

    return avatar_cmd




