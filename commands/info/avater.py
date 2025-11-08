# -*- coding: utf-8 -*-
# commands/avater.py
# Avatar parancs

if __name__ == '__main__':
    exit(1)

import discord
from discord import app_commands, Locale
from languages.languages import language_manager


def create_avatar_command(client):
    """
    """

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
        if user.avatar.url == user.display_avatar.url:
            msg = language_manager.get_text(language_manager.get_language_for_context(interaction), "avatar", "global",
                                            user.display_name, user.avatar.url)
        else:
            msg = language_manager.get_text(language_manager.get_language_for_context(interaction), "avatar", "guild",
                                            user.display_name, user.avatar.url,
                                            user.display_avatar.url)
        await interaction.response.send_message(msg)
    
    return avatar_command


def register_avatar_command(tree, client, guild=None):
    help_cmd = create_avatar_command(client)
    
    # Guild-specifikus description beállítása
    if guild:
        # Szerver nyelve alapján description módosítás
        guild_locale = str(guild.preferred_locale)

        if guild_locale == "hu":
            help_cmd.description = language_manager.get_command_description("hu", "avatar")
        else:
            help_cmd.description = language_manager.get_command_description("en", "avatar")

    tree.add_command(help_cmd, guild=guild)

    return help_cmd




