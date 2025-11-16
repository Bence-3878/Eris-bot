#!/usr/bin/env python
# -*- coding: utf-8 -*-
# webhook.py
import discord
import requests
import json
import config
import database
from discord import app_commands, Locale

from commands.info import register_avatar_command
from languages.languages import language_manager
from error.error import error

def create_send_server(client):

    @app_commands.command(
        name="send_server"
    )
    @app_commands.describe(
        text=app_commands.locale_str(
            "message",
            **{
                "hu": "üzenet",
                "en-US": "message",
                "en-GB": "message",
            }
        ),
        channel=app_commands.locale_str(
            "which channel?",
            **{
                "hu": "melyik csatornába?",
                "en-US": "which channel?",
                "en-GB": "which channel?",
            }
        ),
    )
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    async def send_server_command(interaction: discord.Interaction, text: str, channel: discord.TextChannel = None):
        """Show available commands and their descriptions on servers"""

        await interaction.response.defer(ephemeral=True)

        if channel is None:
            channel = interaction.channel

        leng_code = language_manager.get_language_for_context(interaction)

        try:

            # Ellenőrizzük, hogy van-e jogosultságunk webhook létrehozására
            if not channel.permissions_for(interaction.guild.me).manage_webhooks:
                await interaction.followup.send(
                    language_manager.get_text(leng_code, "server", "webhook_no_perm"),
                    ephemeral=True
                )
                return

            if not channel.permissions_for(interaction.user).send_messages:
                await interaction.followup.send(
                    language_manager.get_text(leng_code, "server", "messages_no_perm"),
                    ephemeral=True
                )

            if len(text) > 2000:
                text = text[:2000]

            # Webhook létrehozása vagy meglévő használata
            webhooks = await channel.webhooks()
            webhook = None

            # Keresünk egy már létező webhookot a bot számára
            for wh in webhooks:
                if wh.user == interaction.guild.me:
                    webhook = wh
                    break

            # Ha nincs, létrehozunk egy újat
            if webhook is None:
                webhook = await channel.create_webhook(
                    name=interaction.guild.me.display_name,
                    avatar=await interaction.guild.me.avatar.read()
                    if interaction.guild.me.avatar
                    else None
                )

            # Üzenet küldése a webhookon keresztül
            await webhook.send(
                content=text,
                username=interaction.user.display_name,
                avatar_url=interaction.user.display_avatar.url
            )

            await interaction.followup.send(
                language_manager.get_text(leng_code, "server", "successful", channel.mention),
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.followup.send(
                language_manager.get_text(leng_code, "server", "Forbidden_error"),
                ephemeral=True
            )
        except Exception as e:
            await error(interaction, language_manager.get_text(leng_code, "server", "Error"), e)
            await interaction.followup.send()

    return send_server_command

def register_server_commands(tree, client, guild=None):
    cmd = create_send_server(client)
    cmd.default_member_permissions = discord.Permissions(send_messages=True)
    cmd.default_guild_permissions = discord.Permissions(send_messages=True)
    cmd.guild_only = True
    cmd.dm_permission = False

    cmd.description_localizations = {
        Locale.hungarian: language_manager.get_command_description("hu", cmd.name),
        Locale.american_english: language_manager.get_command_description("en", cmd.name),
        Locale.british_english: language_manager.get_command_description("en", cmd.name)
    }
    # Guild-specifikus description beállítása
    if guild:
        # Szerver nyelve alapján description módosítás
        guild_locale = str(guild.preferred_locale)
        languages = language_manager.get_all_available_languages()

        for lang in languages:
            if language_manager.discord_lang_code(lang) == guild_locale:
                cmd.description = language_manager.get_command_description(lang, cmd.name)

        mapped = language_manager.locale_mapping.get(guild_locale)
        if mapped not in languages:
            cmd.description = language_manager.get_command_description("en", cmd.name)

        tree.add_command(cmd, guild=guild)
    else:
        tree.add_command(cmd)

    return cmd
