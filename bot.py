# -*- coding: utf-8 -*-
# bot.py
# Discord bot fő logikája és eseménykezelői

import discord
import logging
from config import config
from commands import register_commands_for_guild, get_available_commands
from guild_settings import guild_settings


class BotInstance:
    """Discord bot példány kezelője"""

    def __init__(self):
        self.client = config.client
        self.tree = config.tree
        self.token = config.token
        self.handler = config.handler
        self.guild_settings = guild_settings
    
        # Események beállítása
        self._setup_events()
    
    def _setup_events(self):
        """Eseménykezelők regisztrálása"""
    
        @self.client.event
        async def on_ready():
            """Bot indulási esemény"""
            print(f"\n{'=' * 60}")
            print(f"🤖 {self.client.user.name}")
            print(f"📋 ID: {self.client.user.id}")
            print(f"📦 Discord.py verzió: {discord.__version__}")
            print(f"{'=' * 60}\n")

            print(f"📚 Elérhető parancsok: {', '.join(get_available_commands())}\n")
            print(f"🔄 Parancsok szinkronizálása szerverenként...\n")

            # Szerverenként regisztráljuk a parancsokat
            for guild in self.client.guilds:
                try:
                    # Szerver engedélyezett parancsainak lekérése
                    enabled_commands = self.guild_settings.get_guild_commands(guild.id)
                    
                    print(f"📍 {guild.name} (ID: {guild.id})")
                    print(f"   Engedélyezett parancsok: {', '.join(enabled_commands)}")
                    
                    # Parancsok regisztrálása erre a szerverre
                    registered = register_commands_for_guild(
                        self.tree, 
                        self.client, 
                        guild, 
                        enabled_commands
                    )
                    
                    # Szinkronizálás
                    synced = await self.tree.sync(guild=guild)
                    
                    if synced:
                        print(f"   ✓ {len(synced)} parancs szinkronizálva: {[c.name for c in synced]}")
                    else:
                        print(f"   ⚠️ Nem sikerült szinkronizálni")
                    
                except Exception as e:
                    print(f"   ✗ Hiba: {e}")
                
                print()  # Üres sor a szeparáláshoz
        
            print(f"{'=' * 60}")
            print(f"✅ Bot aktív: {self.client.user}")
            print(f"{'=' * 60}\n")
        
        @self.client.event
        async def on_guild_join(guild):
            """Amikor a bot csatlakozik egy új szerverhez"""
            print(f"\n🆕 Új szerver: {guild.name} (ID: {guild.id})")
            
            # Alapértelmezett parancsok hozzáadása
            default_commands = self.guild_settings.get_guild_commands(guild.id)
            print(f"   Alapértelmezett parancsok: {', '.join(default_commands)}")
            
            # Parancsok regisztrálása és szinkronizálása
            register_commands_for_guild(self.tree, self.client, guild, default_commands)
            await self.tree.sync(guild=guild)
            
            print(f"   ✓ Parancsok szinkronizálva\n")

    def run(self):
        """Bot indítása"""
        self.client.run(
            self.token,
            log_handler=self.handler,
            log_level=logging.DEBUG
        )


# Bot példány létrehozása
bot_instance = BotInstance()