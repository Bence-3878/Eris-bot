# -*- coding: utf-8 -*-
# languages.py
# Nyelvkezelés a bot számára


if __name__ == '__main__':
    exit(1)

import json
import os
from pathlib import Path


class LanguageManager:
    """Nyelvek kezelése JSON fájlokból"""

    def __init__(self, lang_dir="languages"):
        self.lang_dir = Path(lang_dir)
        self.languages = {}
        self.default_language =  "en"
        self._load_languages()

    def _load_languages(self):
        """Összes nyelvi fájl betöltése"""
        if not self.lang_dir.exists():
            print(f"⚠️ Nyelvi mappa nem található: {self.lang_dir}")
            return

        for lang_file in self.lang_dir.glob("*.json"):
            lang_code = lang_file.stem  # pl. "en", "hu"
            try:
                with open(lang_file, "r", encoding="utf-8") as f:
                    self.languages[lang_code] = json.load(f)
                print(f"✓ Nyelv betöltve: {lang_code}")
            except Exception as e:
                print(f"✗ Hiba a(z) {lang_code} betöltésekor: {e}")

    def get_text(self, lang_code, command, key, *args):
        """
        Szöveg lekérése adott nyelvből
        
        Args:
            lang_code: Nyelv kód (pl. "en", "hu")
            command: Parancs neve (pl. "ping")
            key: Kulcs a responses-ben (pl. "Pong!")
            *args: Formázási argumentumok
            
        Returns:
            str: A formázott szöveg
        """
        # Ha nincs ilyen nyelv, alapértelmezett használata
        if lang_code not in self.languages:
            lang_code = self.default_language

        try:
            text = self.languages[lang_code][self.get_categories(lang_code, command)][command]["responses"][key]
            if args:
                return text.format(*args)
            return text
        except (KeyError, IndexError) as e:
            print(f"⚠️ Hiányzó fordítás: {lang_code}/{command}/{key}")
            # Fallback az angol nyelvre
            try:
                text = self.languages[self.default_language][self.get_categories(lang_code, command)][command]["responses"][key]
                if args:
                    return text.format(*args)
                return text
            except:
                return f"[Missing translation: {key}]"

    def get_command_description(self, lang_code, command):
        """Parancs leírásának lekérése"""
        if lang_code not in self.languages:
            lang_code = self.default_language

        try:
            return self.languages[lang_code][self.get_categories(lang_code, command)][command]["description"]
        except KeyError:
            return "No description available"
        
    def get_command_usage(self, lang_code, command):
        """Parancs használi útmutató"""
        if lang_code not in self.languages:
            lang_code = self.default_language
        
        try:
            return self.languages[lang_code][self.get_categories(lang_code, command)][command]["usage"]
        except KeyError:
            return "No usage available"
        
    def get_command_examples(self, lang_code, command):
        """Parancs használi útmutató"""
        if lang_code not in self.languages:
            lang_code = self.default_language
        
        try:
            return self.languages[lang_code][self.get_categories(lang_code, command)][command]["examples"]
        except KeyError:
            return "No examples available"

    def get_category_name(self, lang_code, category):
        return self.languages[lang_code][category]["name"]

    def get_category_description(self, lang_code, category):
        return self.languages[lang_code][category]["description"]
        
    def get_all_available_languages(self):
        """
        Az összes elérhető nyelv kódjának lekérése

        Returns:
            list: Nyelv kódok listája (pl. ["en", "hu"])
        """
        return list(self.languages.keys())

    def get_all_categories(self, lang_code):
        """
        Az adott nyelvhez tartozó összes parancs kategória lekérése

        Args:
            lang_code (str): A nyelv kódja (pl. "en", "hu") amihez a kategóriákat lekérjük

        Returns:
            list: Kategória nevek listája (pl. ["info", "moderation"])

        Példák:
            >>> lang_manager = LanguageManager()
            >>> lang_manager.get_all_categories("hu")
            ["info", "moderation"]
        """

        return list(self.languages[lang_code].keys())

    def get_all_commands(self, lang_code, category):
        return list(self.languages[lang_code][category].keys())[2:]

    def get_categories(self, lang_code, command):
        categories = self.get_all_categories(lang_code)

        for category in categories:
            if command in self.get_all_commands(lang_code, category):
                return category

        return None

    def get_language_for_context(self, interaction):
        """
        Nyelv meghatározása a kontextus alapján
        
        Args:
            interaction: Discord Interaction objektum
            
        Returns:
            str: Nyelv kód
        """
        # Locale mapping (Discord locale -> bot nyelv kód)
        locale_mapping = {
            "hu": "hu",
            "en-US": "en",
            "en-GB": "en",
            #"de": "de",
            #"es-ES": "es",
            #"fr": "fr",
        }

        # 1. ELSŐDLEGES: Felhasználó nyelve (interaction.locale)
        #    Ez a felhasználó Discord kliens nyelvbeállítása
        user_locale = str(interaction.locale)
        user_lang = locale_mapping.get(user_locale, None)

        if user_lang and user_lang in self.languages:
            return user_lang

        # 2. MÁSODLAGOS: Ha szerveren vagyunk, szerver nyelve
        if interaction.guild is not None:
            guild_locale = str(interaction.guild.preferred_locale)
            guild_lang = locale_mapping.get(guild_locale, None)

            if guild_lang and guild_lang in self.languages:
                return guild_lang

        # 3. ALAPÉRTELMEZETT: angol
        return self.default_language

# Globális language_manager példány létrehozása
language_manager = LanguageManager()