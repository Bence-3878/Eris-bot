import discord
import logging
from dotenv import load_dotenv
import os
import random
import math


#####################################################import#############################################################


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


load_dotenv()                                       # .env fájl beolvasása a környezeti változókhoz
token = os.getenv('DISCORD_TOKEN')                  # A Discord bot token kiolvasása környezetből

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')  # Naplófájl kezelő beállítása
intents = discord.Intents.default()                 # Alapértelmezett intentek (engedélyek) létrehozása
intents.message_content = True                      # Üzenettartalom olvasásának engedélyezése (parancsokhoz szükséges)
intents.members = True                              # Tag események engedélyezése (pl. belépés)

client = discord.Client(intents=intents)            # Discord kliens példány létrehozása a megadott intentekkel

level1 = 100                                        # Kiinduló XP költség az első szinthez
levelq = 1.05                                       # Szintenkénti növekedési kvóciens (XP igény szorzója)
levels = [0,level1]
for i in range(1,100):                              # 1-től 99-ig generálunk küszöböket (összesen 100 szint körül)
    n = int(level1*math.pow(levelq,i))              # i-edik szinthez többlet XP (geometriai növekedés)
    m = levels[i] + n                               # Következő szint össz-XP küszöb (kumulált)
    levels.append(m)                                # Hozzáadás a listához

admin_id = 543856425131180036                       # Az admin fő fiókjának ID-ja


#####################################################init###############################################################


def gPX(s):
    n = len(s) + random.randint(-3, 5)
    if n > 50:
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





###############################################egyszerű függvények######################################################


async def send_help(message: discord.Message):
    try:
        await message.channel.send('még fejlesztés alatt')
    except discord.Forbidden:
        pass
    except discord.HTTPException:
        pass

async def send_level(message: discord.Message):
    if leveldb is None:  # Ha nincs adatbázis kapcsolat
        await message.channel.send('Az adatbázis nem érhető el, a szint funkció ideiglenesen nem működik.')
        # Visszajelzés a felhasználónak
        return
    cursor = leveldb.cursor()  # Kurzor nyitása lekérdezéshez
    try:  # Próbáljuk lefuttatni a lekérdezést
        cursor.execute(  # Lekérdezés: felhasználó XP és szint adott szerveren
            'SELECT id, user_xp, level FROM server_users WHERE id = %s AND server_id = %s',
            (message.author.id, message.guild.id)
        )
        result = cursor.fetchone()  # Egyetlen sor beolvasása
    finally:  # Mindig lefut, hiba esetén is
        cursor.close()  # Kuren lezárása erőforrás-felszabadítás miatt
    if result is None:  # Ha nincs adat a felhasználóról
        await message.channel.send('Még nincs adatod ebben a szerverben.')  # Tájékoztatás
        return
    try:
        await message.channel.send('szintje: ' + str(result[2]) + '\n'  # Üzenet a szintről
                                   + 'ennyi xp kell a következő szinthez: '  # Kiegészítő információ
                                   + str(result[1] - levels[result[2]]) + '/' + str(
            levels[result[2] + 1] - levels[result[2]])
                                   + '\nösszes xp: ' + str(result[1]))  # Összesített XP kijelzése
    except discord.Forbidden:
        pass  # Nincs jogosultság reakcióhoz/íráshoz
    except discord.HTTPException:
        pass  # Discord API hiba esetén csendben továbblépünk

async def send_test(message: discord.Message):
    try:
        await message.channel.send('test')
    except discord.Forbidden:
        pass
    except discord.HTTPException:
        pass

async def send_top(message: discord.Message):
    if leveldb is None:  # DB nélkül nem megy
        await message.channel.send('Az adatbázis nem érhető el, a toplista ideiglenesen nem működik.')  # Visszajelzés
        return
    cursor = leveldb.cursor()  # Kurzor nyitása
    try:  # Védett DB művelet
        cursor.execute(  # Legjobb 10 felhasználó XP szerint adott szerveren
            'SELECT id, user_xp FROM server_users WHERE server_id = %s ORDER BY user_xp DESC LIMIT 10',
            (message.guild.id,)
        )
        result = cursor.fetchall()  # Minden sor beolvasása
    finally:  # Mindig lefut
        cursor.close()  # Kurzor zárása
    embed = discord.Embed(  # Beágyazott üzenet létrehozása
        title="top lista",  # Cím
        description="a legtöbb üzenet küldő emberek listája",  # Leírás (XP proxyként)
        color=discord.Color.blue()  # Szín beállítása
    )

    rank = 1  # Kezdő rangszám
    for row in result:  # Végigmegyünk a lekérdezett sorokon
        embed.add_field(  # Új mező hozzáadása az embedhez
            name=f'#{rank} <@{row[0]}>',  # Helyezés és felhasználó megemlítése
            value=str(row[1]),  # XP érték megjelenítése
            inline=False  # Mezők külön sorban
        )
        rank += 1  # Rang növelése

    await message.channel.send(embed=embed)  # Embed küldése a csatornára

async def admin_test(message: discord.Message):
    pass

async def other_messege(message: discord.Message):
    if leveldb is None:  # Ha nincs DB, nem számolunk XP-t
        return
    xp = gPX(message.content)  # XP becslés az üzenet tartalmából
    cursor = leveldb.cursor()

    try:  # Adatbázis műveletek védett része
        cursor.execute('select * from servers where id = %s', (message.guild.id))
        row1 = cursor.fetchone()
        cursor.execute(  # Meglévő adatok lekérdezése
            'SELECT user_xp, level FROM server_users WHERE id = %s AND server_id = %s',
            (message.author.id, message.guild.id)
        )
        row = cursor.fetchone()  # Eredmény beolvasása
        if row is None:  # Ha új felhasználó ezen a szerveren
            try:  # Beszúrás próbálkozás
                cursor.execute(  # Új rekord létrehozása kezdő értékekkel
                    'INSERT INTO server_users (id, server_id, user_xp, level) VALUES (%s, %s, %s, %s)',
                    (message.author.id, message.guild.id, xp, 0)
                )
                leveldb.commit()  # Tranzakció véglegesítése
            except mysql.connector.Error as e:  # DB hiba esetén
                leveldb.rollback()  # Visszagörgetés
                await message.channel.send(f'Hiba az adatbázis beszúráskor: {e.msg}')  # Hibaüzenet
        else:  # Ha már létezik rekord
            current_xp = row[0] + xp  # Új összesített XP kiszámítása
            new_level = level(current_xp)  # Új szint meghatározása
            try:  # Frissítés és szintlépés kezelése
                if row[1] < new_level:  # Ha szintet lépett a felhasználó
                    channel = client.get_channel(row1[2])  # Kijelölt szintlépés csatorna lekérése (ID alapján)
                    if channel is not None:  # Ha a csatorna elérhető
                        await channel.send(f"{message.author.mention} {new_level}. szintű lett")  # Publikus gratuláció
                    if row1[3] == 1:
                        try:  # Privát üzenet küldése
                            await message.author.send(f"{new_level}. szintű lettél")  # DM értesítés
                        except Exception:  # Ha nem sikerül DM-et küldeni (pl. tiltva)
                            pass  # Néma elnyelés
                cursor.execute(  # Felhasználó rekordjának frissítése
                    'UPDATE server_users SET user_xp = %s, level = %s WHERE id = %s AND server_id = %s',
                    (current_xp, new_level, message.author.id, message.guild.id)
                )
                leveldb.commit()  # Tranzakció véglegesítése
            except mysql.connector.Error as e:  # Frissítési hiba esetén
                leveldb.rollback()  # Visszagörgetés
                await message.channel.send(f'Hiba frissítés közben: {e.msg}')  # Hibaüzenet
    finally:  # Mindig lefut
        cursor.close()  # Kurzor lezárása


##############################################aszinkron függvények######################################################


@client.event                                       # Eseménykezelő regisztrálása a klienshez
async def on_ready():                               # Akkor fut, amikor a bot sikeresen csatlakozott és készen áll
    print(client.user.name)                         # Bot felhasználó nevének kiírása
    print(client.user.id)                           # Bot felhasználó azonosítójának kiírása
    print(leveldb)                                  # DB kapcsolat objektum kiírása (debug)
    print(discord.__version__)                      # discord.py verzió kiírása

@client.event                                       # Üzenetekre reagáló eseménykezelő
async def on_message(message):                      # Minden bejövő üzenetre lefut (DM és szerver)
    if message.author.bot:                          # Ha az üzenet küldője bot
        return                                      # Ne reagáljunk botokra, elkerülve a végtelen loopokat

    # Képes üzenet detektálása (csatolmányok)
    if any(
        (a.content_type and a.content_type.startswith('image/')) or
        (a.filename and a.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp')))
        for a in message.attachments
    ):
        pass

    elif message.content.startswith('?help'):
        await send_help(message)

    elif message.content.startswith('?level'):      # Szint lekérdezése parancs
        await send_level(message)

    elif message.content.startswith('?top'):        # Toplista parancs
        await send_top(message)

    elif message.content.startswith('?test'):       # Teszt parancs
        await send_test(message)

    else:                                           # Minden más üzenet esetén XP kezelés
        await other_messege(message)

# Esemény: a bot bekerül egy új szerverre  # Kommentezett szekciócím
@client.event                                       # Eseménykezelő regisztráció
async def on_guild_join(guild: discord.Guild):      # Akkor fut, amikor a bot egy szerverhez csatlakozik
    # Itt futtasd a saját "parancsod" (setup/inicializálás) logikát  # Útmutató komment
    # Példa: üzenet küldése egy alkalmas csatornába  # Példa leírás
    channel = guild.system_channel                  # Alap csatorna lekérése (ha van)
    if channel is None:                             # Ha nincs rendszer csatorna
        for ch in guild.text_channels:              # Végigmegyünk a szöveges csatornákon
            if ch.permissions_for(guild.me).send_messages:  # Ha a bot írhat ide
                channel = ch                        # Ezt választjuk csatornának
                break                               # Megállunk az első megfelelőnél

    if channel is not None:                         # Ha találtunk alkalmas csatornát
        await channel.send("Szia! Köszönöm a meghívást. Készen állok a használatra. Írd be: ?help")  # Üdvözlő üzenet

    if leveldb is not None:                         # Ha az adatbázis elérhető
        cursor = leveldb.cursor()                   # Kurzor nyitása
        try:                                        # Védett DB művelet
            cursor.execute(                         # Szerver bejegyzés létrehozása inicializáló értékekkel
                'INSERT INTO servers (id, welcome_ch, level_up_ch, level_sys) VALUES (%s, %s, %s, %s)',
                (guild.id, None, None, False)
            )
            leveldb.commit()                        # Tranzakció véglegesítése
        finally:                                    # Mindig lefut
            cursor.close()                          # Kurzor zárása


@client.event                                       # Eseménykezelő regisztráció
async def on_member_join(member):                   # Akkor fut, amikor új tag csatlakozik egy szerverhez
    if leveldb is None:
        return
    channel = None
    cursor = leveldb.cursor()
    try:
        cursor.execute('SELECT welcome_ch FROM servers WHERE id = %s', (member.guild.id,))
        row = cursor.fetchone()
        if row and row[0]:
            channel = client.get_channel(int(row[0]))
    except Exception:
        cursor.close()
        return
    finally:
        cursor.close()
    if channel is not None:                         # Ha csatorna létezik és elérhető
        await channel.send(f"Üdvözöllek {member.mention} ezen a szerveren!")  # Üdvözlő üzenet az új tagnak

@client.event
async def on_member_remove(member):
    pass

if not token:                                       # Ha a token nincs megadva
    raise RuntimeError("DISCORD_TOKEN nincs beállítva a környezetben (.env).")  # Hibát dobunk, hogy ne induljon el a bot

client.run(token, log_handler=handler, log_level=logging.DEBUG)  # Bot futtatása a megadott tokennel és naplózási beállításokkal
