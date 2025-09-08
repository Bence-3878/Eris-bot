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
    import mysql.connector  # később kell a típusokhoz is
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
    # xp -> szint (max olyan i, hogy levels[i] <= xp)
    if xp < 0:
        return 0
    l = 0
    for i, threshold in enumerate(levels):
        if xp < threshold:
            return max(0, i - 1)
        l = i
    return l
# ... existing code ...

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith('?help'):
        pass


    elif message.content.startswith('?level'):
        if leveldb is None:
            await message.channel.send('Az adatbázis nem érhető el, a szint funkció ideiglenesen nem működik.')
            return
        cursor = leveldb.cursor()
        try:
            cursor.execute(
                'SELECT id, user_xp, level FROM server_users WHERE id = %s AND server_id = %s',
                (message.author.id, message.guild.id)
            )
            result = cursor.fetchone()
        finally:
            cursor.close()
        if result is None:
            await message.channel.send('Még nincs adatod ebben a szerverben.')
            return
        await message.channel.send('szintje: ' + str(result[2]) +'\n'
                                   + 'ennyi xp kell a következő szinthez: '
                                   + str(result[1]-levels[result[2]]) + '/' + str(levels[result[2]+1]-levels[result[2]])
                                   + '\nösszes xp: ' + str(result[1]))

    elif message.content.startswith('?top'):
        if leveldb is None:
            await message.channel.send('Az adatbázis nem érhető el, a toplista ideiglenesen nem működik.')
            return
        cursor = leveldb.cursor()
        try:
            cursor.execute(
                'SELECT id, user_xp FROM server_users WHERE server_id = %s ORDER BY user_xp DESC LIMIT 10',
                (message.guild.id,)
            )
            result = cursor.fetchall()
        finally:
            cursor.close()
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
        if leveldb is None:
            return
        xp = gPX(message.content)
        cursor = leveldb.cursor()
        try:
            cursor.execute(
                'SELECT user_xp, level FROM server_users WHERE id = %s AND server_id = %s',
                (message.author.id, message.guild.id)
            )
            row = cursor.fetchone()
            if row is None:
                try:
                    cursor.execute(
                        'INSERT INTO server_users (id, user_xp, level, server_id) VALUES (%s, %s, %s, %s)',
                        (message.author.id, xp, 0, message.guild.id)
                    )
                    leveldb.commit()
                except mysql.connector.Error as e:
                    leveldb.rollback()
                    await message.channel.send(f'Hiba az adatbázis beszúráskor: {e.msg}')
            else:
                current_xp = row[0] + xp
                new_level = level(current_xp)
                try:
                    if row[1] < new_level:
                        channel = client.get_channel(1414239240195149875)
                        if channel is not None:
                            await channel.send(f"{message.author.mention} {new_level}. szintű lett")
                        try:
                            await message.author.send(f"{new_level}. szintű lettél")
                        except Exception:
                            pass
                    cursor.execute(
                        'UPDATE server_users SET user_xp = %s, level = %s WHERE id = %s AND server_id = %s',
                        (current_xp, new_level, message.author.id, message.guild.id)
                    )
                    leveldb.commit()
                except mysql.connector.Error as e:
                    leveldb.rollback()
                    await message.channel.send(f'Hiba frissítés közben: {e.msg}')
        finally:
            cursor.close()


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
        try:
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


if not token:
    raise RuntimeError("DISCORD_TOKEN nincs beállítva a környezetben (.env).")



client.run(token, log_handler=handler, log_level=logging.DEBUG)