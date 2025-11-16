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
    @app_commands.describe(text="üzenet", channel="melyik csatornába?")  # Lokalizációhoz
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    async def send_server_command(interaction: discord.Interaction, text: str, channel: discord.TextChannel = None):
        """Show available commands and their descriptions on servers"""

        await interaction.response.defer(ephemeral=True)

        if channel is None:
            channel = interaction.channel

        try:
            # Ellenőrizzük, hogy van-e jogosultságunk webhook létrehozására
            if not channel.permissions_for(interaction.guild.me).manage_webhooks:
                await interaction.response.send_message("❌ Nincs jogosultságom webhook létrehozására ebben a csatornában!", ephemeral=True)
                return

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
                    avatar=await interaction.guild.me.avatar.read() if interaction.guild.me.avatar else None
                )


            # Üzenet küldése a webhokon keresztül
            await webhook.send(
                content=text,
                username=interaction.user.display_name,
                avatar_url=interaction.user.display_avatar.url
            )

            await interaction.followup.send(f"✅ Üzenet elküldve a {channel.mention} csatornába!", ephemeral=True)

        except discord.Forbidden:
            await interaction.response.send_message("❌ Nincs jogosultságom ehhez a művelethez!", ephemeral=True)
        except Exception as e:
            await error(interaction, "send_server_command", e)
            await interaction.response.send_message(f"❌ Hiba történt")

    return send_server_command

def register_server_commands(tree, client, guild=None):
    ping_cmd = create_send_server(client)

    # Guild-specifikus description beállítása
    if guild:
        # Szerver nyelve alapján description módosítás
        guild_locale = str(guild.preferred_locale)

        if guild_locale == "hu":
            ping_cmd.description = language_manager.get_command_description("hu", "ping")
        else:
            ping_cmd.description = language_manager.get_command_description("en", "ping")

        tree.add_command(ping_cmd, guild=guild)
    else:
        tree.add_command(ping_cmd)

    return ping_cmd
