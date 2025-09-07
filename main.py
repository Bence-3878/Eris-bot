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
levels = [0,level1]
for i in range(1,100):
    n = int(level1*math.pow(levelq,i))
    m = levels[i] + n
    levels.append(m)

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
    l=0
    for level in levels:
        if level > xp:
            return l-1
        l += 1
    return 0

def levelup(level):
    print("level up")


@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith('?help'):
        pass
    elif message.content.startswith('?level'):
        cursor = leveldb.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ' + str(message.author.id,))
        result = cursor.fetchone()
        await message.channel.send('szintje: ' + str(result[2]) +'\n'
                                   + 'ennyi xp kell a következő szinthez: '
                                   + str(result[1]-levels[result[2]]) + '/' + str(levels[result[2]+1]-levels[result[2]])
                                   + '\nösszes xp: ' + str(result[1]))
    else:
        xp = gPX(message.content)
        cursor = leveldb.cursor()
        cursor.execute('SELECT user_xp, level FROM users WHERE id = ' + str(message.author.id,))
        result = cursor.fetchall()
        if (len(result) == 0):
            cursor.execute('INSERT INTO users VALUES (' + str(message.author.id) + ',' + str(xp) + ',0)')
            leveldb.commit()
        elif (len(result) == 1):
            currenXP = result[0][0] + xp
            if result[0][1] < level(currenXP):
                levelup(result[0][1])
            cursor.execute(
                'UPDATE users SET user_xp = ' + str(currenXP) + ',level = ' +
            str(level(currenXP)) + ' WHERE id = ' + str(message.author.id, ))
            leveldb.commit()





@client.event
async def on_member_join(member):
    channel = client.get_channel(1411685718740303872)
    await channel.send(f"Üdvözöllek {member.mention} ezen a szerveren!")




client.run(token, log_handler=handler, log_level=logging.DEBUG)