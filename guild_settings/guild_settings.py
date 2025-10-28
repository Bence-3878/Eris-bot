# -*- coding: utf-8 -*-
# guild_settings.py
# Szerver-specifikus parancs beállítások kezelése

import json
from pathlib import Path


class GuildSettings:
    """Szerver-specifikus beállítások kezelője"""
    
    def __init__(self, settings_file='guild_settings.json'):
        self.settings_file = Path(settings_file)
        self.settings = self._load_settings()
    
    def _load_settings(self):
        """Beállítások betöltése fájlból"""
        global default_settings
        if not self.settings_file.exists():
            # Alapértelmezett beállítások létrehozása
            default_settings = {
                "default_commands": ["ping","help"],  # Alapértelmezett parancsok minden új szerveren
                "guilds": {}
            }
            self._save_settings(default_settings)
            return default_settings
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Hiba a beállítások betöltésekor: {e}")
            return default_settings
    
    def _save_settings(self, settings=None):
        """Beállítások mentése fájlba"""
        if settings is None:
            settings = self.settings
        
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Hiba a beállítások mentésekor: {e}")
    
    def get_guild_commands(self, guild_id):
        """
        Szerver engedélyezett parancsainak lekérése
        
        Args:
            guild_id: A szerver ID-ja (int vagy str)
            
        Returns:
            list: Engedélyezett parancsok listája
        """
        guild_id = str(guild_id)
        
        if guild_id not in self.settings["guilds"]:
            # Ha nincs még beállítva, használja az alapértelmezett parancsokat
            return self.settings.get("default_commands", ["ping"])
        
        return self.settings["guilds"][guild_id].get("enabled_commands", ["ping"])
    
    def set_guild_commands(self, guild_id, commands):
        """
        Szerver parancsainak beállítása
        
        Args:
            guild_id: A szerver ID-ja
            commands: Parancsok listája (pl. ["ping"])
        """
        guild_id = str(guild_id)
        
        if guild_id not in self.settings["guilds"]:
            self.settings["guilds"][guild_id] = {}
        
        self.settings["guilds"][guild_id]["enabled_commands"] = commands
        self._save_settings()
        
        print(f"✓ Szerver {guild_id} parancsai frissítve: {commands}")
    
    def enable_command(self, guild_id, command_name):
        """Parancs engedélyezése egy szerveren"""
        guild_id = str(guild_id)
        current_commands = self.get_guild_commands(guild_id)
        
        if command_name not in current_commands:
            current_commands.append(command_name)
            self.set_guild_commands(guild_id, current_commands)
            return True
        return False
    
    def disable_command(self, guild_id, command_name):
        """Parancs letiltása egy szerveren"""
        guild_id = str(guild_id)
        current_commands = self.get_guild_commands(guild_id)
        
        if command_name in current_commands:
            current_commands.remove(command_name)
            self.set_guild_commands(guild_id, current_commands)
            return True
        return False
    
    def get_all_available_commands(self):
        """Összes elérhető parancs listája"""
        return ["ping", "help"]  # Bővíthető ahogy jönnek az új parancsok


# Globális példány
guild_settings = GuildSettings()