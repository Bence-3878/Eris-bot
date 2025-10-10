import discord
from discord.utils import get
import os                                           # Környezeti változók
from dotenv import load_dotenv                      # .env betöltés
from pathlib import Path                            # Fájl elérési útvonalak kezelése
import  logging
from discord import app_commands                    # SLASH parancsok
import requests                                     # HTTP kérések
from logging.handlers import RotatingFileHandler    # Naplózás forgó fájlokkal
from logging import Formatter
from discord.ext import commands

if not Path('.env').is_file():
    print("Error: .env file not found!")
    print("Please create a .env file with your bot token (DISCORD_TOKEN=your_token)")
    raise SystemExit

load_dotenv()  # .env fájl beolvasása a környezeti változókhoz
token = os.getenv('DISCORD_TOKEN')  # A Discord bot token kiolvasása környezetből

if not token:  # Ha a token nincs megadva
    raise RuntimeError("DISCORD_TOKEN nincs beállítva a környezetben (.env).")
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')  # Naplófájl kezelő beállítása

# Modul-szintű logger, egyszeri konfigurációval (duplikált handlerek elkerülése)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not any(isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", None) and str(h.baseFilename).endswith("error.log")
           for h in logger.handlers):
    _err_handler = logging.FileHandler('error.log', encoding='utf-8')
    _err_handler.setLevel(logging.ERROR)
    _err_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(_err_handler)
intents = discord.Intents.default()                 # Alapértelmezett intentek (engedélyek) létrehozása
intents.message_content = True                      # Üzenettartalom olvasásának engedélyezése (parancsokhoz szükséges)
intents.members = True                              # Tag események engedélyezése (pl. belépés)

client = discord.Client(intents=intents)            # Discord kliens példány létrehozása a megadott intentekkel
tree = app_commands.CommandTree(client)             # SLASH parancs fa a Client-hez
sess = requests.Session()
sess.headers.update({'User-Agent': 'Mozilla/5.0'})  # Egyedi User-Agent fejléc hozzáadása az HTTP kérésekhez.,

