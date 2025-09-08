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
    database="discord_bot",
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



@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith('?help'):
        pass
    elif message.content.startswith('?level'):
        cursor = leveldb.cursor()
        cursor.execute(
            'SELECT * FROM server_users WHERE id = %s AND server_id = %s',
            (message.author.id, message.guild.id)
        )
        result = cursor.fetchone()
        if result is None:
            await message.channel.send('Még nincs adatod ebben a szerverben.')
            return
        await message.channel.send('szintje: ' + str(result[2]) +'\n'
                                   + 'ennyi xp kell a következő szinthez: '
                                   + str(result[1]-levels[result[2]]) + '/' + str(levels[result[2]+1]-levels[result[2]])
                                   + '\nösszes xp: ' + str(result[1]))


    elif message.content.startswith('?top'):
        cursor = leveldb.cursor()
        cursor.execute('SELECT * FROM server_users ORDER BY user_xp DESC LIMIT 10;')
        result = cursor.fetchall()
        embed = discord.Embed(
            title="top lista",
            description="a legtöbb üzenet küldő emberek listája",
            color=discord.Color.blue()
        )

        for row in result:
            embed.add_field(
                name='<@' + str(row[0]) + '>',
                value=row[1],
                inline=False
            )

        await message.channel.send(embed=embed)


    elif message.content.startswith('?test'):
        await message.channel.send('test')


    else:
        xp = gPX(message.content)
        cursor = leveldb.cursor()
        cursor.execute(
            'SELECT user_xp, level FROM server_users WHERE id = %s AND server_id = %s',
            (message.author.id, message.guild.id)
        )
        result = cursor.fetchall()
        await message.channel.send(str(len(result)))
        if (len(result) == 0):
            await message.channel.send('a')
            try:
                cursor.execute(
                    'INSERT INTO server_users (id, user_xp, level, server_id) VALUES (%s, %s, %s, %s)',
                    (message.author.id, xp, 0, message.guild.id)
                )
                leveldb.commit()
                await message.channel.send('z')
            except mysql.connector.Error as e:
                leveldb.rollback()
                await message.channel.send(f'Hiba az adatbázis beszúráskor: {e.msg}')
        elif (len(result) == 1):
            await message.channel.send('b')
            currenXP = result[0][0] + xp
            try:
                if result[0][1] < level(currenXP):
                    channel = client.get_channel(1414239240195149875)
                    await channel.send(f"{message.author.mention}  {level(currenXP)}.szintű lett")
                    await message.author.send(str(level(currenXP)) + '.szintű lett')
                cursor.execute(
                    'UPDATE server_users SET user_xp = %s, level = %s WHERE id = %s AND server_id = %s',
                    (currenXP, level(currenXP), message.author.id, message.guild.id)
                )
                leveldb.commit()
            except mysql.connector.Error as e:
                leveldb.rollback()
                await message.channel.send(f'Hiba frissítés közben: {e.msg}')

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

    cursor = leveldb.cursor()
    cursor.execute('INSERT INTO servers (id, welcome_ch, level_up_ch, level_sys) '
                   'VALUES ('+str(guild.id)+', NULL, NULL, false)')
    leveldb.commit()





@client.event
async def on_member_join(member):
    channel = client.get_channel(1411685718740303872)
    await channel.send(f"Üdvözöllek {member.mention} ezen a szerveren!")




client.run(token, log_handler=handler, log_level=logging.DEBUG)