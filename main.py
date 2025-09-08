import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import random
import mysql.connector
import math

######################import##########################

try:
    import mysql.connector
    leveldb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="alma",
        database="discord_bot",
        port=3306,
        auth_plugin='mysql_native_password'
    )
except Exception as e:
    leveldb = None
    print(f"Figyelem: az adatbázis-kapcsolat nem jött létre: {e}. A szint/xp funkciók nem lesznek elérhetőek.")

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

admin_id = 543856425131180036

######################init##########################

def gPX(s):
    n = len(s)
    n = n + random.randint(-3, 5)
    if n>50:
        n = 50 + random.randint(-5, 5)
    return n


def level(xp):
    if xp < 0:
        return 0
    l = 0
    for i, threshold in enumerate(levels):
        if xp < threshold:
            return max(0, i - 1)
        l = i
    return l

@client.event
async def on_message(message):
    if message.author.bot:
        return
    return



# Esemény: a bot bekerül egy új szerverre
@client.event
async def on_guild_join(guild: discord.Guild):
    # Itt futtasd a saját "parancsod" (setup/inicializálás) logikát
    # Példa: üzenet küldése egy alkalmas csatornába
    channel = guild.system_channel
    if channel is None:
        for ch in guild.text_channels:
            if ch.permissions_for(guild.me).send_messages:
                channel = ch
                break

    if channel is not None:
        await channel.send("Szia! Köszönöm a meghívást. Készen állok a használatra. Írd be: ?help")

    if leveldb is not None:
        cursor = leveldb.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ' + str(message.author.id,))
        result = cursor.fetchone()
        await message.channel.send('szintje: ' + str(level(result[1])))
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
                channel = client.get_channel(1411688050785783828)
                await channel.send(f"{message.author.mention}  {level(currenXP)}.szintű lett")
            cursor.execute(
                'INSERT INTO servers (id, welcome_ch, level_up_ch, level_sys) VALUES (%s, %s, %s, %s)',
                (guild.id, None, None, False)
            )
            leveldb.commit()
        finally:
            cursor.close()


@client.event
async def on_member_join(member):
    channel = client.get_channel(1411685718740303872)
    if channel is not None:
        await channel.send(f"Üdvözöllek {member.mention} ezen a szerveren!")


@client.event
async def on_member_join(member):
    channel = client.get_channel(1411685718740303872)
    if channel is not None:
        await channel.send(f"Üdvözöllek {member.mention} ezen a szerveren!")


if not token:
    raise RuntimeError("DISCORD_TOKEN nincs beállítva a környezetben (.env).")



client.run(token, log_handler=handler, log_level=logging.DEBUG)