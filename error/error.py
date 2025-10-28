# -*- coding: utf-8 -*-
# error.py
# hiba jelentés

import discord
from discord import app_commands
from discord.ext import commands
from config import config, logger, client
import contextlib



async def error(message: discord.Message | None = None, interaction: discord.Interaction | None = None,
                string: str | None = None , exception: Exception = None):


    error_channel = config.error_channel
    try:
        channel = client.get_channel(error_channel)
        if channel is None:
            with contextlib.suppress(Exception):
                channel = await client.fetch_channel(error_channel)
        error_msg = ""
        if message is not None:
            guild_name = message.guild.name if message.guild else "DM/Ismeretlen szerver"
            channel_name = f"#{message.channel.name}" if (getattr(message, "channel", None)
                                                      and getattr(message.channel, "name",
                                                                  None)) else "#ismeretlen-csatorna"
            channel_mention = getattr(getattr(message, "channel", None), "mention", "#ismeretlen-csatorna")
            error_msg +=f"Hely: {guild_name} | {channel_name} | {channel_mention}\n"
            error_msg += f"Küldő: {message.author.mention} (ID: {message.author.id}) (name: {message.author.name})\n"
        if interaction is not None:
            guild_name = interaction.guild.name if interaction.guild else "DM/Ismeretlen szerver"
            channel_name = f"#{interaction.channel.name}" if (getattr(interaction, "channel", None)
                                                              and getattr(interaction.channel, "name",
                                                                          None)) else "#ismeretlen-csatorna"
            channel_mention = getattr(getattr(interaction, "channel", None), "mention", "#ismeretlen-csatorna")
            error_msg += f"Parancs: {getattr(getattr(interaction, 'command', None), 'name', 'ismeretlen')}\n"
            error_msg += f"Hely: {guild_name} | {channel_name} | {channel_mention}\n"
            error_msg += f"Küldő: {interaction.user.mention} (ID: {interaction.user.id}) (name: {interaction.user.name})\n"
        if exception is not None:
            if hasattr(exception, "msg"):
                error_msg += f"Adatbázis hiba: {exception.msg}\n"

            if hasattr(exception, "errno"):
                error_msg += f"Hibakód: {exception.errno}\n"

            if hasattr(exception, "sqlstate"):
                error_msg += f"SQL állapot: {exception.sqlstate}\n"

            if hasattr(exception, "args"):
                error_msg += f"Hiba: {str(exception.args)}\n"

            if hasattr(exception, "params"):
                error_msg += f"Paraméterek: {str(exception.params)}\n"

            if hasattr(exception, "query"):
                error_msg += f"Lekérdezés: {str(exception.query)}\n"
            error_msg += f"Hiba típusa: {type(exception).__name__}\n"
            error_msg += f"Részletes hiba: {str(exception)}\n"

        if string:
                error_msg += f"Komment: {string}"

        if len(error_msg) > 2000:
                error_msg = error_msg[:1990] + "…"

        logger.error(error_msg, exc_info=exception)

        with contextlib.suppress(Exception):
            await channel.send(error_msg)
    except Exception as e:
        logger.error(f"Error: {e}")

