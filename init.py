import discord
from discord.utils import get
import os                                           # Környezeti változók
from dotenv import load_dotenv                      # .env betöltés
from pathlib import Path                            # Fájl elérési útvonalak kezelése

def setup(bot):
    if not Path('.env').is_file():
        print("Error: .env file not found!")
        print("Please create a .env file with your bot token (DISCORD_TOKEN=your_token)")
        raise SystemExit

    load_dotenv()                                       # .env fájl beolvasása a környezeti változókhoz
    token = os.getenv('DISCORD_TOKEN')                  # A Discord bot token kiolvasása környezetből

    if not token:                                       # Ha a token nincs megadva
        raise RuntimeError("DISCORD_TOKEN nincs beállítva a környezetben (.env).")

