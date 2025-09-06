import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import random
import mysql.connector

leveldb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="alma",
    database="leveldb",
    port=3306
)

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True


client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(client.user.name)
    print(client.user.id)

def px(s):
    n = len(s)
    n = n + random.randint(-3, 5)
    if n>50:
        n = 50 + random.randint(-5, 5)
    return n


@client.event
async def on_message(message):
    if message.author.bot:
        return






client.run(token, log_handler=handler, log_level=logging.DEBUG)