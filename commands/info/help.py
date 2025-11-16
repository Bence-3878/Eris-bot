# -*- coding: utf-8 -*-
# commands/help.py
# Help parancs

if __name__ == '__main__':
    exit(1)

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
        name="help"
    )
    @app_commands.describe()  # Lokalizációhoz
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    async def help_command(interaction: discord.Interaction):
        """Show available commands and their descriptions on servers"""

        await help_logic(client,interaction)


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

        await help_logic(client,interaction)

    return help_command

async def help_logic(client, interaction: discord.Interaction):

    await interaction.response.defer(ephemeral=False)

    # Nyelv meghatározása a szerver alapján
    lang_code = language_manager.get_language_for_context(interaction)
    commands_categories = language_manager.get_all_categories(lang_code)

    embed = discord.Embed(
        title=language_manager.get_text(lang_code, "help", "title")
    )

    for category in commands_categories:
        embed.add_field(
            name=language_manager.get_category_name(lang_code, category),
            value=language_manager.get_category_description(lang_code, category),
            inline=False
        )

    # Add navigation buttons
    view = discord.ui.View()
    for category in commands_categories:
        button = discord.ui.Button(
            label=language_manager.get_category_name(lang_code, category),
            style=discord.ButtonStyle.primary,
            custom_id=f"help_{category}"
        )

        async def button_callback(interaction: discord.Interaction):
            category = interaction.data["custom_id"].split("_")[1]
            category_embed = discord.Embed(
                title=language_manager.get_category_name(lang_code, category),
                description=language_manager.get_category_description(lang_code, category)
            )
            command_list = language_manager.get_all_commands(lang_code, category)

            # Create new view with back button
            category_view = discord.ui.View()

            for command in command_list:
                category_embed.add_field(
                    name=command,
                    value=language_manager.get_command_description(lang_code, command),
                    inline=False
                )

                # Add button for each command
                command_button = discord.ui.Button(
                    label=command,
                    style=discord.ButtonStyle.secondary,
                    custom_id=f"command_{category}_{command}"
                )

                async def command_callback(cmd_interaction: discord.Interaction):
                    cmd = cmd_interaction.data["custom_id"].split("_")[2]
                    cat = cmd_interaction.data["custom_id"].split("_")[1]

                    command_embed = discord.Embed(
                        title=cmd,
                        description=language_manager.get_command_description(lang_code, cmd)
                    )

                    # Add usage information
                    command_embed.add_field(
                        name=language_manager.get_text(lang_code, "help", "usage"),
                        value=language_manager.get_command_usage(lang_code, cmd),
                        inline=False
                    )

                    # Add examples if available
                    examples = language_manager.get_command_examples(lang_code, cmd)
                    if examples:
                        command_embed.add_field(
                            name=language_manager.get_text(lang_code, "help", "examples"),
                            value="\n".join(examples),
                            inline=False
                        )

                    # Create view with back button to category
                    command_view = discord.ui.View()
                    command_back = discord.ui.Button(
                        label=language_manager.get_text(lang_code, "help", "back"),
                        style=discord.ButtonStyle.secondary,
                        custom_id=f"help_{cat}"
                    )

                    async def command_back_callback(back_int: discord.Interaction):
                        await button_callback(back_int)

                    command_back.callback = command_back_callback
                    command_view.add_item(command_back)

                    await cmd_interaction.response.edit_message(
                        embed=command_embed,
                        view=command_view
                    )

                command_button.callback = command_callback
                category_view.add_item(command_button)

            back_button = discord.ui.Button(
                label=language_manager.get_text(lang_code, "help", "back"),
                style=discord.ButtonStyle.secondary,
                custom_id="help_back"
            )

            async def back_callback(back_interaction: discord.Interaction):
                await back_interaction.response.edit_message(embed=embed, view=view)

            back_button.callback = back_callback
            category_view.add_item(back_button)

            await interaction.response.edit_message(embed=category_embed, view=category_view)

        button.callback = button_callback
        view.add_item(button)

    await interaction.followup.send(embed=embed, view=view)


def register_help_command(tree, client, guild):
    """
    Help parancs regisztrálása guild-ekhez (szerverekhez)
    """
    help_cmd = create_help_command_guild(client)# Guild-specifikus description beállítása
    if guild:
        # Szerver nyelve alapján description módosítás
        guild_locale = str(guild.preferred_locale)

        if guild_locale == "hu":
            help_cmd.description = language_manager.get_command_description("hu", "help")
        else:
            help_cmd.description = language_manager.get_command_description("en", "help")

        tree.add_command(help_cmd, guild=guild)
    else:
        tree.add_command(help_cmd)

    return help_cmd

def register_help_command_dm(tree, client):
    """
    Help parancs regisztrálása DM-ekhez (privát üzenetekhez)
    """
    help_cmd = create_help_command_dm(client)
    tree.add_command(help_cmd)
    return help_cmd