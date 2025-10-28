import discord
# -*- coding: utf-8 -*-
# config.py
# Konfiguráció és inicializáció

import discord
from discord import app_commands
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from pathlib import Path
import requests


class Config:
    """Bot konfiguráció központi kezelője"""
    
    def __init__(self):
        self._load_env()
        self._setup_logging()
        self._setup_client()
        self._setup_session()
    
    def _load_env(self):
        """Környezeti változók betöltése"""
        if not Path('.env').is_file():
            print("Error: .env file not found!")
            print("No .env file found. Creating one...")
            with open('.env', 'w') as f:
                f.write('DISCORD_TOKEN=your_token')
            print("Created .env file. Please edit it with your bot token.")
            raise SystemExit

        
        load_dotenv()
        self.token = os.getenv('DISCORD_TOKEN')
        
        if not self.token:
            raise RuntimeError("DISCORD_TOKEN nincs beállítva a környezetben (.env).")

        if self.token == "your_token":
            print("Please edit it with your bot token.")
            raise SystemExit
    
    def _setup_logging(self):
        """Naplózás beállítása"""
        self.handler = logging.FileHandler(
            filename='discord.log',
            encoding='utf-8',
            mode='w'
        )
        
        # Modul-szintű logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Error log handler hozzáadása (ha még nincs)
        if not any(
            isinstance(h, logging.FileHandler) and 
            getattr(h, "baseFilename", None) and 
            str(h.baseFilename).endswith("error.log")
            for h in self.logger.handlers
        ):
            err_handler = logging.FileHandler('error.log', encoding='utf-8')
            err_handler.setLevel(logging.ERROR)
            err_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            self.logger.addHandler(err_handler)
    
    def _setup_client(self):
        """Discord kliens beállítása"""
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        self.client = discord.Client(intents=intents)
        self.tree = app_commands.CommandTree(self.client)
    
    def _setup_session(self):
        """HTTP session beállítása"""
        self.sess = requests.Session()
        self.sess.headers.update({'User-Agent': 'Mozilla/5.0'})


# Globális config példány
config = Config()

# Exportált változók a kompatibilitás miatt
client = config.client
tree = config.tree
token = config.token
handler = config.handler
logger = config.logger
sess = config.sess
error_channel = 1432687370339352659

