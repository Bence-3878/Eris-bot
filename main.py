import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import random
import mysql.connector
import math

######################import##########################

leveldb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="alma",
    database="levels",
    port=3306,
    auth_plugin='mysql_native_password'
)

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)

level1 = 100
levelq = 1.05
levels = []
for i in range(100):
    levels.append(int(level1*math.pow(levelq,i)))
######################init##########################

@client.event
async def on_ready():
    print(client.user.name)
    print(client.user.id)
    print(leveldb)
    print(discord.__version__)

def gPX(s):
    n = len(s)
    n = n + random.randint(-3, 5)
    if n>50:
        n = 50 + random.randint(-5, 5)
    return n

def level(xp):
    level = math.int(math.log(xp/level1, levelq))
    if level > 0:
        return level
    else:
        return 0


@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith('?help'):
        pass
    elif message.content.startswith('?level'):
        print('a')
        cursor = leveldb.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ' + str(message.author.id,))
        result = cursor.fetchone()
        message.channel.send('szint:' + str(result[0][0]))
    else:
        xp = gPX(message.content)
        cursor = leveldb.cursor()
        cursor.execute('SELECT user_xp FROM users WHERE id = ' + str(message.author.id,))
        result = cursor.fetchall()
        if (len(result) == 0):
            cursor.execute('INSERT INTO users VALUES (' + str(message.author.id) + ',' + str(xp) + ',0)')
            leveldb.commit()
        elif (len(result) == 1):
            currenXP = result[0][0] + xp
            cursor.execute('UPDATE users SET user_xp = ' + currenXP + 'level = ' + level(currenXP) +
                                                    ' WHERE id = ' + str(message.author.id,))
            leveldb.commit()





@client.event
async def on_member_join(member):
    channel = client.get_channel(1411685718740303872)
    await channel.send(f"Üdvözöllek {member.mention} ezen a szerveren!")




client.run(token, log_handler=handler, log_level=logging.DEBUG)