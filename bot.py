# -*- coding: utf-8 -*-
# bot.py
# Discord bot fő logikája és eseménykezelői

if __name__ == '__main__':
    exit(1)

import discord
import logging
from config import config
from commands import get_all_available_commands as get_available_commands, get_all_dm_commands as get_dm_commands, \
 register_all_commands, register_all_dm_commands
from guild_settings.guild_settings import guild_settings


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
            print(f"📚 Elérhető parancsok (szerverekhez): {', '.join(get_available_commands())}")
            print(f"💬 DM parancsok: {', '.join(get_dm_commands())}\n")
            
            # FONTOS: Először töröljük az ÖSSZES parancsot (globális és guild)
            print(f"🗑️ Régi parancsok törlése...\n")
            try:
                # Globális parancsok törlése
                self.tree.clear_commands(guild=None)
                await self.tree.sync()
                print(f"   ✓ Globális parancsok törölve")

                # Minden guild parancsainak törlése
                for guild in self.client.guilds:
                    self.tree.clear_commands(guild=guild)
                    await self.tree.sync(guild=guild)
                    print(f"   ✓ {guild.name} parancsai törölve")

                print()
            except Exception as e:
                print(f"   ✗ Törlési hiba: {e}\n")

            # 1. Globális DM parancsok regisztrálása (CSAK DM-ekhez)
            print(f"🌍 Globális DM parancsok regisztrálása (CSAK privát üzenetekhez)...\n")
            try:
                dm_registered = register_all_dm_commands(self.tree, self.client)
                global_synced = await self.tree.sync()
                print(f"   ✓ {len(global_synced)} DM parancs szinkronizálva: {[c.name for c in global_synced]}")
                print(f"   💬 Ezek a parancsok CSAK privát üzenetekben működnek!\n")
            except Exception as e:
                print(f"   ✗ Globális sync hiba: {e}\n")
            
            # 2. Szerverenként regisztráljuk a parancsokat
            print(f"🔄 Szerver parancsok szinkronizálása (CSAK szervereken működnek)...\n")

            for guild in self.client.guilds:
                try:
                    # Szerver engedélyezett parancsainak lekérése
                    enabled_commands = self.guild_settings.get_guild_commands(guild.id)
                
                    print(f"📍 {guild.name} (ID: {guild.id})")
                    print(f"   Engedélyezett parancsok: {', '.join(enabled_commands)}")
                
                    # Parancsok regisztrálása erre a szerverre
                    registered = register_all_commands(
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
            print(f"🏢 Szerver parancsok: CSAK szervereken")
            print(f"💬 DM parancsok: CSAK privát üzenetekben")
            print(f"{'=' * 60}\n")

            # Státusz beállítása
            await self.client.change_presence(
                status=discord.Status.online,  # online, idle, dnd, invisible
                activity=discord.Game(name="🎮 /help paranccsal")
            )

        @self.client.event
        async def on_guild_join(guild):
            """Amikor a bot csatlakozik egy új szerverhez"""
            print(f"\n🆕 Új szerver: {guild.name} (ID: {guild.id})")
        
            # Alapértelmezett parancsok hozzáadása
            default_commands = self.guild_settings.get_guild_commands(guild.id)
            print(f"   Alapértelmezett parancsok: {', '.join(default_commands)}")
        
            # Parancsok regisztrálása és szinkronizálása
            register_all_commands(self.tree, self.client, guild, default_commands)
            await self.tree.sync(guild=guild)
        
            print(f"   ✓ Parancsok szinkronizálva\n")

    def run(self):
        """Bot indítása"""
        try:
            self.client.run(
                self.token,
                log_handler=self.handler,
                log_level=logging.DEBUG
            )
        except Exception as e:
            print(e)



# Bot példány létrehozása
bot_instance = BotInstance()