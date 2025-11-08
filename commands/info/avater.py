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
        name="avater"
    )
    @app_commands.describe()  # Lokalizációhoz
    @app_commands.describe(user="")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def avatar_command(interaction: discord.Interaction):
        """Show user avatar"""
        if interaction.user.avatar.url == interaction.user.display_avatar.url:
            msg = language_manager.get_text(language_manager.get_language_for_context(interaction), "avater", "global"
                                            ,interaction.user.display_name, interaction.user.avatar.url)
        else:
            msg = language_manager.get_text(language_manager.get_language_for_context(interaction), "avater", "guild",
                                            interaction.user.display_name, interaction.user.avatar.url,
                                            interaction.user.display_avatar.url)
        await interaction.response.send_message(msg)

def register_avatar_command(tree, client, guild=None):
    help_cmd = create_avatar_command(client)# Guild-specifikus description beállítása

    # Szerver nyelve alapján description módosítás
    guild_locale = str(guild.preferred_locale)

    if guild_locale == "hu":
        help_cmd.description = language_manager.get_command_description("hu", "help")
    else:
        help_cmd.description = language_manager.get_command_description("en", "help")

    tree.add_command(help_cmd, guild=guild)

    return help_cmd




