# -*- coding: utf-8 -*-
# commands/ping.py
# Ping parancs

if __name__ == '__main__':
    exit(1)
    

import discord
from discord import app_commands, Locale
from languages.languages import language_manager


def create_ping_command(client):
    """
    Univerzális ping parancs - működik szervereken ÉS DM-ben
    """
    @app_commands.command(
        name="ping"
    )
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def ping(interaction: discord.Interaction):
        """Válaszidő mérése"""
        
        # Nyelv meghatározása
        if interaction.guild is None:
            lang_code = "en"
        else:
            lang_code = language_manager.get_language_for_context(interaction)

        latency_ms = round(client.latency * 1000)

        # Fordítások lekérése
        pong_text = language_manager.get_text(lang_code, "ping", "Pong!")
        bot_latency_text = language_manager.get_text(lang_code, "ping", "Bot Latency", latency_ms)

        await interaction.response.send_message(
            f"{pong_text}\n{bot_latency_text}"
        )
    
    # Lokalizált leírások - MINDEN támogatott nyelvre
    ping.description_localizations = {
        Locale.hungarian: "Bot válaszideje",
        Locale.american_english: "Bot response time",
        Locale.british_english: "Bot response time",
        ## További nyelvek hozzáadása szükség esetén
        #Locale.german: "Bot-Antwortzeit",
        #Locale.spanish: "Tiempo de respuesta del bot",
        #Locale.french: "Temps de réponse du bot",
    }
    
    return ping



def register_ping_command(tree, client, guild=None):
    """
    Ping parancs regisztrálása
    """
    ping_cmd = create_ping_command(client)
    
    if guild:
        tree.add_command(ping_cmd, guild=guild)
    else:
        tree.add_command(ping_cmd)  # Globális
    
    return ping_cmd

