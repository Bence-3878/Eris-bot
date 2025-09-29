import asyncio
from pickle import FALSE, GLOBAL

import discord                                      # Discord bot kliens
# from discord.ext import commands
import logging                                      # Naplózás
import contextlib
from dotenv import load_dotenv                      # .env betöltés
import os                                           # Környezeti változók
import random                                       # Véletlen XP
# import mysql.connector
import math                                         # Szintgörbe számításhoz
from discord import app_commands                    # SLASH parancsok támogatása
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

#####################################################import#############################################################


try:                                                # Megkíséreljük az adatbázis-kapcsolat létrehozását
    import mysql.connector                          # MySQL kliens importálása
    leveldb = mysql.connector.connect(              # Csatlakozás a MySQL adatbázishoz
        host="localhost",                           # Adatbázis szerver címe
        user="root",                                # Adatbázis felhasználónév
        password="alma",                            # Adatbázis jelszó (demó érték, élesben ne így tárold)
        database="discord_bot",                     # Használt adatbázis neve
        port=3306,                                  # MySQL port
        auth_plugin='mysql_native_password'         # Hitelesítési plugin (kompatibilitási okokból)
    )
except Exception as e:                              # Ha bármilyen hiba történik az import/csatlakozás során
    leveldb = None                                  # Állítsuk None-ra, jelezve hogy nincs DB kapcsolat
    print(f"Figyelem: az adatbázis-kapcsolat nem jött létre: {e}. A szint/xp funkciók nem lesznek elérhetőek.")
    # Figyelmeztető üzenet a konzolra

if not Path('.env').is_file():
    print("Error: .env file not found!")
    print("Please create a .env file with your bot token (DISCORD_TOKEN=your_token)")
    exit(1)

load_dotenv()                                       # .env fájl beolvasása a környezeti változókhoz
token = os.getenv('DISCORD_TOKEN')                  # A Discord bot token kiolvasása környezetből

if not token:                                       # Ha a token nincs megadva
    raise RuntimeError("DISCORD_TOKEN nincs beállítva a környezetben (.env).")
                                                    # Hibát dobunk, hogy ne induljon el a bot

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')  # Naplófájl kezelő beállítása
intents = discord.Intents.default()                 # Alapértelmezett intentek (engedélyek) létrehozása
intents.message_content = True                      # Üzenettartalom olvasásának engedélyezése (parancsokhoz szükséges)
intents.members = True                              # Tag események engedélyezése (pl. belépés)

client = discord.Client(intents=intents)            # Discord kliens példány létrehozása a megadott intentekkel
tree = app_commands.CommandTree(client)             # SLASH parancs fa a Client-hez
sess = requests.Session()

level1 = 500                                        # Kiinduló XP költség az első szinthez
levelq = 1.05                                       # Szintenkénti növekedési kvóciens (XP igény szorzója)
levels = [0,level1]
for i in range(1,100):                              # 1-től 99-ig generálunk küszöböket (összesen 100 szint körül)
    n = int(level1*math.pow(levelq,i))              # i-edik szinthez többlet XP (geometriai növekedés)
    m = levels[i] + n                               # Következő szint össz-XP küszöb (kumulált)
    levels.append(m)                                # Hozzáadás a listához

admin_id = 543856425131180036                       # Az admin fő fiókjának ID-ja

error_channel = 1416450862674477206

test = True
######################init##########################


def gPX(message: discord.Message):                                         # Heurisztikus XP egy üzenetre
    # Képes üzenet detektálása (csatolmányok)
    m = 0
    if any(
            (a.content_type and a.content_type.startswith('image/')) or
            (a.filename and a.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp')))
            for a in message.attachments
    ):
        m = random.randint(10, 30)
    if message.content is None:
        return m
    n = len(message.content) + random.randint(-3, 5)
    if n > 50:
        n = 50 + random.randint(-5, 5)
    return n + m

def level(xp):                                      # XP -> szint átalakítás (legnagyobb i, ahol levels[i] <= xp)
    if xp < 0:
        return 0
    l = 0
    for i, threshold in enumerate(levels):
        if xp < threshold:
            return max(0, i - 1)
        l = i
    return l


###############################################egyszerű függvények######################################################

async def error_interaction(interaction: discord.Interaction, string: str = "", e: Exception = None, ):
    # Configure error logging
    error_handler = logging.FileHandler('error.log')
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    error_handler.setFormatter(error_formatter)
    logger = logging.getLogger('discord')
    logger.addHandler(error_handler)

    try:
        admin_user = interaction.client.get_user(admin_id) or await interaction.client.fetch_user(admin_id)
        channel = client.get_channel(error_channel)
        if admin_user is not None:
            guild_name = interaction.guild.name if interaction.guild else "DM/Ismeretlen szerver"
            channel_name = f"#{interaction.channel.name}" if (getattr(interaction, "channel", None)
                                                              and getattr(interaction.channel, "name",
                                                                          None)) else "#ismeretlen-csatorna"
            channel_id = interaction.channel.id if getattr(interaction, "channel", None) else None
            if e is None:
                error_msg = (
                    f"Parancs: {interaction.command.name}\n"
                    f"Hely: {guild_name} | {channel_name} | <#{channel_id}>\n"
                    f"Küldő: {interaction.user.mention} (ID: {interaction.user.id}) (name: {interaction.user.name})"
                )
            else:
                error_msg = (
                    f"Parancs: {interaction.command.name}\n"
                    f"Hiba: {str(e)}\n"
                    f"Hely: {guild_name} | {channel_name} | <#{channel_id}>\n"
                    f"Küldő: {interaction.user.mention} (ID: {interaction.user.id}) (name: {interaction.user.name})"
                )
            if string != "":
                error_msg = error_msg + "\nKomment: " + string
            logger.error(error_msg)
            await channel.send(error_msg)
    except Exception as dm_err:
        logger.error(f"DM error: {dm_err}")
    return

async def error_messege(message: discord.Message, string: str = "", e: Exception = None, ):
    if test:
        print("error messege2")
    # Configure error logging
    error_handler = logging.FileHandler('error.log')
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    error_handler.setFormatter(error_formatter)
    logger = logging.getLogger('discord')
    logger.addHandler(error_handler)
    if test:
        print(f"message: {message}")
    try:
        admin_user = client.get_user(admin_id) or await client.fetch_user(admin_id)
        channel = client.get_channel(error_channel)
        if test:
            print("channel")
            print(channel)
        if admin_user is not None:
            guild_name = message.guild.name if message.guild else "DM/Ismeretlen szerver"
            channel_name = f"#{message.channel.name}" if (getattr(message, "channel", None)
                                                          and getattr(message.channel, "name",
                                                                      None)) else "#ismeretlen-csatorna"
            channel_id = message.channel.id if getattr(message, "channel", None) else None
            if test:
                print("channel id")
                print(channel_id)
            if e is None:
                error_msg = (
                    f"Hely: {guild_name} | {channel_name} | <#{channel_id}>\n"
                    f"Küldő: {message.author.mention} (ID: {message.author.id}) (name: {message.author.name})"
                )
            else:
                error_msg = (
                    f"Hiba: {str(e)}\n"
                    f"Hely: {guild_name} | {channel_name} | <#{channel_id}>\n"
                    f"Küldő: {message.author.mention} (ID: {message.author.id}) (name: {message.author.name})"
                )
            if test:
                print(error_msg)

            if string != "":
                error_msg = error_msg + "\nKomment: " + string
            logger.error(error_msg)
            await channel.send(error_msg)
    except Exception as dm_err:
        logger.error(f"DM error: {dm_err}")
    return


async def other_messege(message: discord.Message):
    UwU = ["UwU", "uwu", "UWU", "uWu", "Uwu", "uwU", "uWU", "UWu",
           "OwO", "owo", "OWO", "oWo", "Owo", "owO", "OWo", "oWO",
           "TwT", "tWT", "tWT", "tWt", "twt", "tWT", "tWt", "tWT",
           "O_o", "o_o", "O_O", "o_O", "O.o", "o.O", "O.O", "o.o",
           "UwO", "uwo", "UWO", "uWo", "Uwo", "uwO", "uWO", "UWo",
           "OwU", "owu", "OWU", "oWu", "Owu", "owU", "oWU", "OWu"]

    OwO = ["OwO", "UwU", "OwU", "UwO", "O_O", "TwT"]

    if leveldb is None:  # Ha nincs DB, nem számolunk XP-t
        m = ""
        if any(uwu in message.content.lower() for uwu in UwU):
            m = OwO[random.randint(0, 6)] + ("!" * random.randint(0, 2))
        if test:
            await message.channel.send(m + "    teszt")
            await error_messege(message, "Nincs adatbázis kapcsolat.")
        else:
            await message.channel.send(m)
        return
    # Ne legyen negatív XP
    xp = gPX(message)  # XP becslés az üzenet tartalmából
    if any(uwu in message.content.lower() for uwu in UwU):
        xp += random.randint(20, 30)
        m = OwO[random.randint(0, 6)] + ("!" * random.randint(0, 4))
        await message.channel.send(m)


    cursor = leveldb.cursor()
    if message.guild is None:
        try:  # Adatbázis műveletek védett része

            # Meglévő adatok lekérdezése
            cursor.execute(
                'SELECT user_xp, level FROM server_users WHERE id = %s AND server_id = 0',
                (message.author.id,)
            )
            row = cursor.fetchone()  # Eredmény beolvasása
        except mysql.connector.Error as e:
            await error_messege(message, "Hiba az adatbázis lekérdezéssel", e)

            cursor.close()  # Kurzor lezárása
            return
        if row is None:  # Ha új felhasználó ezen a szerveren
            try:  # Beszúrás próbálkozás
                cursor.execute(
                    'INSERT INTO server_users (id, server_id, user_xp, level) VALUES (%s, 0, %s, 0)',
                    (message.author.id, xp)
                )
                leveldb.commit()  # Tranzakció véglegesítése
            except mysql.connector.Error as e:  # DB hiba esetén
                leveldb.rollback()  # Visszagörgetés
                cursor.close()  # Kurzor lezárása
                await error_messege(message, "XP rendszer hiba újelem beszúrásánál", e)

        else:  # Ha már létezik rekord
            current_xp = row[0] + xp  # Új összesített XP kiszámítása
            if current_xp < 0:
                current_xp = 0
            new_level = level(current_xp)  # Új szint meghatározása
            try:  # Frissítés és szintlépés kezelése
                # Felhasználó rekordjának frissítése
                cursor.execute(
                    'UPDATE server_users SET user_xp = %s, level = %s WHERE id = %s AND server_id = 0',
                    (current_xp, new_level, message.author.id)
                )
                leveldb.commit()  # Tranzakció véglegesítése

                # Szintlépés értesítés csak sikeres commit után
                if row[1] < new_level:

                    await message.author.send(f"Annyit beszéltél a bottal DM-ben hogy {new_level}. szintű lettél.\n"
                                                  f"Ennél értelmesebb dolgot is lehetne csinálni")



            except Exception as e:
                leveldb.rollback()  # Visszagörgetés
                cursor.close()  # Kurzor lezárása
                await error_messege(message, "Hiba XP frissítés közben", e)
                return





    else:


        async def update_server_user(message, xp, cursor, level_up_ch, level_sys):
            try:
                cursor.execute(
                    'SELECT user_xp, level, user_xp_monthly  FROM server_users WHERE id = %s AND server_id = %s',
                    (message.author.id, message.guild.id)
                )
                row = cursor.fetchone()

                if row is None:
                    await insert_new_user(message, xp, cursor)
                else:
                    await update_existing_user(message, xp, row, cursor, level_up_ch, level_sys)

            except mysql.connector.Error as e:
                await error_messege(message, f'Hiba frissítés közben: {e.msg}', e)

        async def insert_new_user(message, xp, cursor):
            try:
                cursor.execute(
                    'INSERT INTO server_users (id, server_id, user_xp, user_xp_monthly, level) VALUES (%s, %s, %s, %s, %s)',
                    (message.author.id, message.guild.id, xp, xp, 0)
                )
                leveldb.commit()
            except mysql.connector.Error as e:
                leveldb.rollback()
                await error_messege(message, f'Hiba az adatbázis beszúráskor: {e.msg}', e)

        async def update_existing_user(message, xp, row, cursor, level_up_ch, level_sys):
            current_xp = row[0] + xp
            current_xp_m = row[2] + xp
            if current_xp < 0:
                current_xp = 0
            new_level = level(current_xp)

            try:
                cursor.execute(
                    'UPDATE server_users SET user_xp = %s, user_xp_monthly = %s , level = %s WHERE id = %s AND server_id = %s',
                    (current_xp, current_xp_m, new_level, message.author.id, message.guild.id)
                )
                leveldb.commit()

                if row[1] < new_level and level_sys == 1:
                    await send_level_up_notification(message, new_level, level_up_ch)

            except mysql.connector.Error as e:
                leveldb.rollback()
                await error_messege(message, "Hiba XP frissítés közben", e)

        async def send_level_up_notification(message, new_level, level_up_ch):
            channel = client.get_channel(int(level_up_ch)) if level_up_ch else None
            try:
                await message.author.send(f"{new_level}. szintű lettél")
            except Exception:
                pass

            if channel is not None:
                await channel.send(f"{message.author.mention} {new_level}. szintű lett")
            else:
                await message.channel.send(f"{message.author.mention} {new_level}. szintű lett")

        # Főfüggvény a guild üzenetek kezelésére
        async def handle_guild_message(message, xp):
            cursor = leveldb.cursor()
            try:
                cursor.execute('SELECT level_up_ch, level_system_enabled FROM servers WHERE id = %s', (message.guild.id,))
                row1 = cursor.fetchone()
                level_up_ch, level_sys = row1
                await update_server_user(message, xp, cursor, level_up_ch, level_sys)
        
            except mysql.connector.Error as e:
                await error_messege(message, f'Hiba frissítés közben: {e.msg}', e)
            finally:
                cursor.close()

        await handle_guild_message(message, xp)
        
# Közös jogosultság ellenőrzés: csak szerveren, és csak admin vagy az admin_id
async def admin_or_owner_check(interaction: discord.Interaction) -> bool:
    if interaction.guild is None:
        raise app_commands.CheckFailure('Ez a parancs csak szerveren használható.')
    if not (interaction.user.guild_permissions.administrator or interaction.user.id == admin_id):
        raise app_commands.CheckFailure('Nincs jogosultságod ehhez a parancshoz.')
    return True

async def admin_check(interaction: discord.Interaction) -> bool:
    if not (interaction.user.id == admin_id):
        raise app_commands.CheckFailure('Nincs jogosultságod ehhez a parancshoz.')
    return True





async def monthly_job():
    if leveldb is None:
        pass
    else:
        cursor = leveldb.cursor()
        try:
            cursor.execute('SELECT id, server_id FROM server_users')
            result = cursor.fetchall()
        except mysql.connector.Error as e:
            pass

        for row in result:
            id, server_id = row
            try:
                cursor.execute('UPDATE server_users SET user_xp_monthly = 0 WHERE id = %s AND server_id = %s',
                    (id, server_id)
                )
                leveldb.commit()
            except mysql.connector.Error as e:
                pass
    if test:
        print("Monthly job finished")

async def run_monthly_at(hour: int = 0, minute: int = 0, tz = ZoneInfo("Europe/Budapest")):
    # Várjuk meg, míg a bot készen áll
    await client.wait_until_ready()
    while not client.is_closed():
        now = datetime.now(tz)
        # Következő futási idő: a legközelebbi hónap 1-je [hour:minute]
        year, month = now.year, now.month

        # Ha ma még az adott időpont előtt vagyunk és ma 1-je van, akkor ma fut
        if now.day == 1 and (now.hour, now.minute) < (hour, minute):
            target_year, target_month = year, month
        else:
            if month == 12:
                target_year, target_month = year + 1, 1
            else:
                target_year, target_month = year, month + 1

        run_at = datetime(target_year, target_month, 1, hour, minute, tzinfo=tz)
        sleep_seconds = max(1.0, (run_at - now).total_seconds())
        try:
            await asyncio.sleep(sleep_seconds)
            await monthly_job()
        except asyncio.CancelledError:
            # Leállításkor kilépünk
            break
        except Exception as e:
            # Ne álljon le a ciklus egy kivétel miatt
            print(f"[Scheduler] Hiba a havi feladat futtatása közben: {e!r}")
            # Kis várakozás, hogy ne pörögjön
            await asyncio.sleep(5)

##############################################aszinkron függvények######################################################



@tree.command(name="rule34", nsfw=True)
@app_commands.describe(search="Keresés", ephemeral="Rejtett (ephemeral) választ kérsz?")
async def rule34(interaction: discord.Interaction, search: str, ephemeral: bool = False):
    # Biztonság: futásidőben is ellenőrizzük, hogy NSFW csatorna
    if not (getattr(getattr(interaction, "channel", None), "is_nsfw", lambda: False) or isinstance(
            interaction.channel, discord.DMChannel)):
        await interaction.response.send_message(
            "Ezt a parancsot csak NSFW csatornában lehet használni.", ephemeral=True)
        return

    # Jelezzük, hogy dolgozunk (és ne küldjünk kétszer választ)
    await interaction.response.defer(ephemeral=ephemeral)


    # Kérés futtatása külön szálon, fejlécekkel
    def _fetch():
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Referer": "https://rule34.xxx/",
        }
        # a 'sess' meglévő requests.Session az alkalmazásban
        r1 = sess.get("https://rule34.xxx/", headers=headers, timeout=10)
        r2 = sess.post(
            "https://rule34.xxx/index.php?page=search",
            data={"tags": f"{search}", "commit": "Search"},
            headers=headers,
            timeout=15,
        )
        return r1.status_code, r2.status_code, r2.text

    try:
        loop = asyncio.get_running_loop()
        _, status_code, html = await loop.run_in_executor(None, _fetch)

    except Exception as e:
        # Hiba esetén értesítsük az admint és csendben térjünk vissza
        await error_interaction(interaction, "Az API nem elérhető.", e)

        # Töröljük az eredeti (ephemeral) választ, hogy a felhasználó ténylegesen ne lásson semmit
        with contextlib.suppress(Exception):
            await interaction.delete_original_response()
        return


    if status_code != 200:
        # Admin értesítése, majd rövid hibaüzenet
        await error_interaction(interaction, f"A rule34.xxx nem sikerült elérni (HTTP {status_code})")
        await interaction.followup.send("A rule34.xxx jelenleg nem elérhető.", ephemeral=True)
        return

        # HTML feldolgozása – keressünk néhány találati linket
    try:
        soup = BeautifulSoup(html, 'html.parser')
        thumbnails = soup.find_all('span', class_='thumb')

        image_links = [thumb.find('img')['src'] for thumb in thumbnails if thumb.find('img')]

        if not image_links:
            await interaction.followup.send("Nem találtam képeket.", ephemeral=True)
            return

        # Random kép kiválasztása és küldése
        random_image = random.choice(image_links)
        embed = discord.Embed(
            title=search,
            color=discord.Color.red()
        )
        embed.set_image(url=random_image)
        await interaction.followup.send(embed=embed, ephemeral=ephemeral)
    except Exception as parse_err:
        await error_interaction(interaction, f"Parsing hiba: {parse_err}", parse_err)
        await interaction.followup.send("Nem sikerült feldolgozni a találatokat.", ephemeral=True)

                                ###################nsfw###################

# XP parancscsoport: /xp show|add|remove|set
xp_group = app_commands.Group(name="xp", description="XP és szint műveletek")

@xp_group.command(name="show", description="Megmutatja a szintedet és XP-det (vagy egy megadott felhasználóét).")
@app_commands.describe(user="Opcionális: válassz felhasználót, akinek az adatait lekérdezed.")
async def xp_show(interaction: discord.Interaction, user: discord.Member | None = None):
    if leveldb is None:
        await interaction.response.send_message(
            'Az adatbázis nem érhető el, a szint funkció ideiglenesen nem működik.',
            ephemeral=True
        )
        await error_interaction(interaction, "Az adatbázis nem érhető el.")
        return
    if interaction.guild is None:
        await interaction.response.send_message('Ez a parancs csak szerveren használható.', ephemeral=True)
        return

    target = user or interaction.user
    cursor = leveldb.cursor()
    try:
        cursor.execute(
            'SELECT user_xp FROM server_users WHERE id = %s AND server_id = %s',
            (target.id, interaction.guild.id)
        )
        result = cursor.fetchone()
    except mysql.connector.Error as e:
        await interaction.response.defer(ephemeral=True)
        await error_interaction(interaction, f"Adatbázis hiba: {e.msg}", e)

        # Töröljük az eredeti (ephemeral) választ, hogy a felhasználó ténylegesen ne lásson semmit
        with contextlib.suppress(Exception):
            await interaction.delete_original_response()
        return
    except Exception as e:
        await interaction.response.defer(ephemeral=True)
        await error_interaction(interaction, e)

        # Töröljük az eredeti (ephemeral) választ, hogy a felhasználó ténylegesen ne lásson semmit
        with contextlib.suppress(Exception):
            await interaction.delete_original_response()
        return
    finally:
        cursor.close()

    if result is None:
        await interaction.response.send_message(
            f'{target.mention} még nem rendelkezik adatokkal ezen a szerveren.',
            ephemeral=True
        )
        return

    total_xp = int(result[0])

    await interaction.response.send_message(
        f'Összes XP: {total_xp}',
        ephemeral=True
    )

@xp_group.command(name="add", description="XP hozzáadása egy felhasználónak (admin).")
@app_commands.describe(user="A felhasználó, akinek XP-t adsz.", amount="Mennyit adjunk hozzá (pozitív egész).")
@app_commands.guild_only()
@app_commands.check(admin_or_owner_check)
async def xp_add(interaction: discord.Interaction, user: discord.Member, amount: int):
    if leveldb is None:
        await interaction.response.send_message('Az adatbázis nem érhető el.', ephemeral=True)
        await error_interaction(interaction, "Az adatbázis nem érhető el.")
        return
    # Jogosultság és guild ellenőrzés dekorátorokkal megoldva
    if amount <= 0:
        await interaction.response.send_message('Az amount legyen pozitív egész.', ephemeral=True)
        return

    cursor = leveldb.cursor()
    try:
        cursor.execute(
            'SELECT user_xp FROM server_users WHERE id = %s AND server_id = %s',
            (user.id, interaction.guild.id)
        )
        row = cursor.fetchone()

        if row is None:
            new_xp = amount
            new_level = level(new_xp)
            cursor.execute(
                'INSERT INTO server_users (id, server_id, user_xp, level) VALUES (%s, %s, %s, %s)',
                (user.id, interaction.guild.id, new_xp, new_level)
            )
        else:
            current_xp = int(row[0])
            new_xp = current_xp + amount
            new_level = level(new_xp)
            cursor.execute(
                'UPDATE server_users SET user_xp = %s, level = %s WHERE id = %s AND server_id = %s',
                (new_xp, new_level, user.id, interaction.guild.id)
            )
        leveldb.commit()
    except Exception as e:
        leveldb.rollback()
        await interaction.response.defer(ephemeral=True)
        await error_interaction(interaction, e)

        # Töröljük az eredeti (ephemeral) választ, hogy a felhasználó ténylegesen ne lásson semmit
        with contextlib.suppress(Exception):
            await interaction.delete_original_response()
        return
    finally:
        cursor.close()

    await interaction.response.send_message(
        f'{user.mention} új XP-je: {new_xp} (szint: {new_level})', ephemeral=True
    )

@xp_group.command(name="remove", description="XP elvétele egy felhasználótól (admin).")
@app_commands.describe(user="A felhasználó, akitől XP-t veszel el.", amount="Mennyit vonjunk le (pozitív egész).")
@app_commands.guild_only()
@app_commands.check(admin_or_owner_check)
async def xp_remove(interaction: discord.Interaction, user: discord.Member, amount: int):
    if leveldb is None:
        await interaction.response.send_message('Az adatbázis nem érhető el.', ephemeral=True)
        await error_interaction(interaction, "Az adatbázis nem érhető el.")
        return
    # Jogosultság és guild ellenőrzés dekorátorokkal megoldva
    if amount <= 0:
        await interaction.response.send_message('Az amount legyen pozitív egész.', ephemeral=True)
        return

    cursor = leveldb.cursor()
    try:
        cursor.execute(
            'SELECT user_xp FROM server_users WHERE id = %s AND server_id = %s',
            (user.id, interaction.guild.id)
        )
        row = cursor.fetchone()
        if row is None:
            await interaction.response.send_message('Nincs adat ehhez a felhasználóhoz ezen a szerveren.', ephemeral=True)
            return

        current_xp = int(row[0])
        new_xp = max(0, current_xp - amount)
        new_level = level(new_xp)
        cursor.execute(
            'UPDATE server_users SET user_xp = %s, level = %s WHERE id = %s AND server_id = %s',
            (new_xp, new_level, user.id, interaction.guild.id)
        )
        leveldb.commit()
    except Exception as e:
        leveldb.rollback()
        await interaction.response.defer(ephemeral=True)
        await error_interaction(interaction, e)
        try:
            admin_user = interaction.client.get_user(admin_id) or await interaction.client.fetch_user(admin_id)
            if admin_user is not None:
                guild_name = interaction.guild.name if interaction.guild else "DM/Ismeretlen szerver"
                channel_name = f"#{interaction.channel.name}" if (getattr(interaction, "channel", None)
                                                                  and getattr(interaction.channel, "name",
                                                                              None)) else "#ismeretlen-csatorna"
                await admin_user.send(
                    f"Parancs: {interaction.command.name}\n"
                    f"Váratlan hiba történt: {str(e)}"
                    f"Hely: {guild_name} | {channel_name}\n"
                    f"Küldő: {interaction.user} (ID: {interaction.user.id})"
                )
        except Exception as dm_err:
            print(f"Nem sikerült DM-et küldeni az adminnak: {dm_err}")

        # Töröljük az eredeti (ephemeral) választ, hogy a felhasználó ténylegesen ne lásson semmit
        with contextlib.suppress(Exception):
            await interaction.delete_original_response()
        return
    finally:
        cursor.close()

    await interaction.response.send_message(
        f'{user.mention} új XP-je: {new_xp} (szint: {new_level})', ephemeral=True
    )

@xp_group.command(name="set", description="XP közvetlen beállítása (admin).")
@app_commands.describe(user="A felhasználó, akinek beállítod az XP-t.",
                       amount="Az új XP érték (0 vagy pozitív egész).")
@app_commands.guild_only()
@app_commands.check(admin_or_owner_check)
async def xp_set(interaction: discord.Interaction, user: discord.Member, amount: int):
    if leveldb is None:
        await interaction.response.send_message('Az adatbázis nem érhető el.', ephemeral=True)
        await error_interaction(interaction, "Az adatbázis nem érhető el.")
        return
    # Jogosultság és guild ellenőrzés dekorátorokkal megoldva
    if amount < 0:
        await interaction.response.send_message('Az amount nem lehet negatív.', ephemeral=True)
        return

    new_xp = amount
    new_level = level(new_xp)
    cursor = leveldb.cursor()
    try:
        cursor.execute(
            'SELECT 1 FROM server_users WHERE id = %s AND server_id = %s',
            (user.id, interaction.guild.id)
        )
        exists = cursor.fetchone() is not None
        if exists:
            cursor.execute(
                'UPDATE server_users SET user_xp = %s, level = %s WHERE id = %s AND server_id = %s',
                (new_xp, new_level, user.id, interaction.guild.id)
            )
        else:
            cursor.execute(
                'INSERT INTO server_users (id, server_id, user_xp, level) VALUES (%s, %s, %s, %s)',
                (user.id, interaction.guild.id, new_xp, new_level)
            )
        leveldb.commit()
    except Exception as e:
        leveldb.rollback()
        await interaction.response.defer(ephemeral=True)
        await error_interaction(interaction, e)

        # Töröljük az eredeti (ephemeral) választ, hogy a felhasználó ténylegesen ne lásson semmit
        with contextlib.suppress(Exception):
            await interaction.delete_original_response()
        return
    finally:
        cursor.close()

    await interaction.response.send_message(
        f'{user.mention} XP-je beállítva: {new_xp} (szint: {new_level})', ephemeral=True
    )

# Regisztráljuk a csoportot a parancsfához
tree.add_command(xp_group)



@tree.command(name="top")
@app_commands.describe(monthly="Az aktuális havi xp szintszerinti toplista." ,globalis="Globális toplista.")
async def top_command(interaction: discord.Interaction, monthly: bool = False, globalis: bool = False):
    if leveldb is None:  # DB nélkül nem megy
        await error_interaction(interaction, "Az adatbázis nem érhető el.")
        await interaction.response.send_message('Az adatbázis nem érhető el,'
            ' a toplista ideiglenesen nem működik.'  ,ephemeral=True)  # Visszajelzés

        return
    await interaction.response.defer(ephemeral=False)
    cursor = leveldb.cursor()  # Kurzor nyitása
    try:  # Védett DB művelet
        if globalis:
            if monthly:
                cursor.execute(  # Legjobb 10 felhasználó XP szerint adott szerveren
                    'SELECT id, SUM(user_xp_monthly) AS total_xp FROM server_users GROUP BY id ORDER BY total_xp DESC LIMIT 10'
                )
            else:
                cursor.execute(  # Legjobb 10 felhasználó XP szerint adott szerveren
                    'SELECT id, SUM(user_xp) AS total_xp FROM server_users GROUP BY id ORDER BY total_xp DESC LIMIT 10'
                )
        else:
            if monthly:
                cursor.execute(  # Legjobb 10 felhasználó XP szerint adott szerveren
                    'SELECT id, user_xp_monthly FROM server_users WHERE server_id = %s ORDER BY user_xp DESC LIMIT 10',
                    (interaction.guild.id,)
                )
            else:
                cursor.execute(  # Legjobb 10 felhasználó XP szerint adott szerveren
                    'SELECT id, user_xp FROM server_users WHERE server_id = %s ORDER BY user_xp DESC LIMIT 10',
                    (interaction.guild.id,)
                )
        result = cursor.fetchall()  # Minden sor beolvasása
    except mysql.connector.Error as e:
        await error_interaction(interaction, f"Adatbázis hiba: {e.msg}", e)


        # Töröljük az eredeti (ephemeral) választ, hogy a felhasználó ténylegesen ne lásson semmit
        with contextlib.suppress(Exception):
            await interaction.delete_original_response()
        return
    except Exception as e:
        await error_interaction(interaction, e)


        # Töröljük az eredeti (ephemeral) választ, hogy a felhasználó ténylegesen ne lásson semmit
        with contextlib.suppress(Exception):
            await interaction.delete_original_response()
        return
    finally:  # Mindig lefut
        cursor.close()  # Kurzor zárása
    if test:
        print(result)

    embed = discord.Embed(
        title="Top 10 Felhasználó",
        description="A legtöbb XP-vel rendelkező felhasználók",
        color=discord.Color.blue()
    )

    rank = 1
    for row in result:
        user_id = row[0]
        xp = row[1]
        try:
            user = interaction.guild.get_member(user_id) or await interaction.guild.fetch_member(user_id)
            user_name = user.mention if user else f"<@{user_id}>"
        except:
            user_name = f"<@{user_id}>"

        embed.add_field(
            name=f'#{rank}',
            value=f"{user_name} - {xp:,} XP",
            inline=False
        )
        rank += 1

    await interaction.followup.send(embed=embed, ephemeral=False)


@tree.command(name="rank", description="Megjeleníti a felhasználó rangját (helyezését) az XP alapján.")
@app_commands.describe(user="Opcionális: válassz felhasználót, akinek az adatait lekérdezed.",
                       monthly="Az aktuális havi xp szint.")
async def rank_command(interaction: discord.Interaction, user: discord.Member | None = None, monthly: bool = False):
    if leveldb is None:
        await interaction.response.send_message(
            'Az adatbázis nem érhető el, a rang funkció ideiglenesen nem működik.',
            ephemeral=True
        )
        error_interaction(interaction,"Az adatbázis nem érhető el.")
        return
    await interaction.response.defer(ephemeral=True)

    target = user or interaction.user
    cursor = leveldb.cursor()
    try:
        if interaction.guild is None:
            cursor.execute(
                'SELECT id, user_xp, level FROM server_users WHERE server_id = 0 ORDER BY user_xp DESC'
            )
        else:
            if monthly:
                cursor.execute(
                    'SELECT id, user_xp_monthly, level FROM server_users WHERE server_id = %s ORDER BY user_xp DESC',
                    (interaction.guild.id,)
                )
            else:
                cursor.execute(
                    'SELECT id, user_xp, level FROM server_users WHERE server_id = %s ORDER BY user_xp DESC',
                    (interaction.guild.id,)
                )
        result = cursor.fetchall()
    except Exception as e:
        error_interaction(interaction,"Hiba a rang lekérése közben" ,e)
        with contextlib.suppress(Exception):
            await interaction.delete_original_response()
        return
    finally:
        cursor.close()
    rank = 0
    talalat = False
    for row in result:
        rank += 1
        if row[0] == target.id:
            talalat = True
            break
    if not talalat:
        await interaction.followup.send(
            f'{target.mention} még nem rendelkezik adatokkal ezen a szerveren.',
            ephemeral=True
        )
        return

    lvl = int(result[rank-1][2])
    total_xp = int(result[rank-1][1])
    have = total_xp - levels[lvl]
    need = levels[lvl + 1] - levels[lvl]

    m = (f'{target.mention} szintje: {lvl}\n'
        f'Következő szinthez: {have}/{need}\n'
        f'Összes XP: {total_xp}         #{rank}')
    try:
        await interaction.followup.send(
            m, ephemeral=False
        )
    except Exception as e:
        await error_interaction(interaction, "Rank üzenetet nem lehet elküldeni", e)

@tree.command(name="global_rank", description="Megjeleníti a felhasználó rangját (helyezését) az XP alapján.")
@app_commands.describe(user="Opcionális: válassz felhasználót, akinek az adatait lekérdezed.")
async def global_rank_command(interaction: discord.Interaction, user: discord.Member | None = None):
    if leveldb is None:
        await interaction.response.send_message(
            'Az adatbázis nem érhető el, a rang funkció ideiglenesen nem működik.',
            ephemeral=True
        )
        error_interaction(interaction,"Az adatbázis nem érhető el.")
        return
    await interaction.response.defer(ephemeral=True)

    target = user or interaction.user
    cursor = leveldb.cursor()
    try:
        # Globális rang: összegezzük az XP-t minden szerverről ugyanahhoz az id-hoz
        cursor.execute(
            'SELECT id, SUM(user_xp) AS total_xp '
            'FROM server_users '
            'GROUP BY id '
            'ORDER BY total_xp DESC'
        )
        result = cursor.fetchall()
    except Exception as e:
        error_interaction(interaction,"Hiba a rang lekérése közben" ,e)
        with contextlib.suppress(Exception):
            await interaction.delete_original_response()
        return
    finally:
        cursor.close()
    rank = 0
    talalat = False
    for row in result:
        rank += 1
        if row[0] == target.id:
            talalat = True
            break
    if not talalat:
        await interaction.followup.send(
            f'{target.mention} még nem rendelkezik globális adatokkal.',
            ephemeral=True
        )
        return

    total_xp = int(result[rank-1][1])
    lvl = level(total_xp)
    # Szint progressz
    if lvl + 1 < len(levels):
        have = total_xp - levels[lvl]
        need = levels[lvl + 1] - levels[lvl]
    else:
        have = 0
        need = 0

    m = (f'{target.mention} globális szintje: {lvl}\n'
        f'Következő szinthez: {have}/{need}\n'
        f'Összes (globális) XP: {total_xp}         #{rank}')
    try:
        await interaction.followup.send(
            m, ephemeral=False
        )
    except Exception as e:
        await error_interaction(interaction, "Rank üzenetet nem lehet elküldeni", e)




@tree.command(name="levels-recalculated")
async def levels_recalculated(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    cursor = None
    try:
        cursor = leveldb.cursor()
        # Csak a szükséges oszlopokat kérdezzük le (feltételezve, hogy xp az oszlop neve)
        cursor.execute('SELECT id, server_id, user_xp FROM server_users')
        result = cursor.fetchall()
        for row in result:
            cursor.execute(
                'UPDATE server_users SET level = %s WHERE id = %s AND server_id = %s',
                (level(row[2]), row[0], row[1])
            )
        # Módosítások véglegesítése
        leveldb.commit()
        await interaction.followup.send("Szintek újraszámolva.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Hiba: {str(e)}", ephemeral=True)
        return
    finally:
        if cursor is not None:
            cursor.close()
                            ###################szint rendszer###################
            
    

@tree.command(name="test", description="Random teszt funkció. Probáld ki ha mered.")
@app_commands.describe(text="üzenet")
async def slash_test(interaction: discord.Interaction, text: str):
    # A slash opciót paraméterként kapjuk meg
    print(text)

#@tree.command(name="set_welcome_channel", description="")
#async def slash_set_welcome_channel(interaction: discord.Interaction):
#    pass

@tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    """Displays bot latency"""
    await interaction.response.send_message(f"Pong! Bot latency: {round(client.latency * 1000)}ms")


send_group = app_commands.Group(name="send", description="üzenet")

@send_group.command(name="dm")
@app_commands.describe(text="üzenet", user="kinek küldjem?")
async def send_dm(interaction: discord.Interaction, text: str, user: discord.Member):
    try:
        # Először válaszolunk az interakcióra hogy ne időzzön ki
        await interaction.response.defer(ephemeral=True)

        # Megpróbáljuk elküldeni a DM-et
        await user.send("{} külde az alábbi üzenetet: {}".format(interaction.user.mention, text))

        # Sikeres küldés visszajelzése
        await interaction.followup.send(
            f"Üzenet sikeresen elküldve {user.mention} részére!",
            ephemeral=True
        )

    except discord.Forbidden:
        # Ha a felhasználó letiltotta a DM-eket
        await interaction.followup.send(
            f"Nem tudtam üzenetet küldeni {user.mention} részére - "
            "valószínűleg letiltotta a DM-eket.",
            ephemeral=True
        )

    except Exception as e:
        # Egyéb hibák esetén
        try:
            admin_user = interaction.client.get_user(admin_id) or await interaction.client.fetch_user(admin_id)
            if admin_user:
                guild_name = interaction.guild.name if interaction.guild else "DM/Ismeretlen szerver"
                channel_name = (f"#{interaction.channel.name}"
                                if (getattr(interaction, "channel", None) and
                                    getattr(interaction.channel, "name", None))
                                else "#ismeretlen-csatorna")
                await admin_user.send(
                    f"DM küldési hiba:\n"
                    f"Hiba: {str(e)}\n"
                    f"Hely: {guild_name} | {channel_name}\n"
                    f"Küldő: {interaction.user} (ID: {interaction.user.id})\n"
                    f"Címzett: {user} (ID: {user.id})"
                )
        except Exception as dm_err:
            print(f"Nem sikerült DM-et küldeni az adminnak: {dm_err}")

        await interaction.followup.send(
            "Váratlan hiba történt az üzenet küldése közben.",
            ephemeral=True
        )

@send_group.command(name="server")
@app_commands.describe(text="üzenet", channel="melyik csatornába?", user="kinek küldjem?")
async def send_server(interaction: discord.Interaction, text: str, 
                      channel: discord.TextChannel, user: discord.Member | None = None):
    try:
        # Először válaszolunk az interakcióra hogy ne időzzön ki
        await interaction.response.defer(ephemeral=True)

        # Megpróbáljuk elküldeni az üzenetet a szerverre
        await channel.send(f"{user.mention} {text}")

        # Sikeres küldés visszajelzése
        await interaction.followup.send(
            f"Üzenet sikeresen elküldve {user.mention} részére!",
            ephemeral=True
        )


    except discord.Forbidden:
        # Ha nincs jogosultság az üzenet küldésére
        await interaction.followup.send(
            f"Nem tudtam elküldeni az üzenetet a {channel.mention} csatornába - "
            "nincs megfelelő jogosultságom.",
            ephemeral=True
        )

    except Exception as e:
        # Egyéb hibák esetén
        try:
            admin_user = interaction.client.get_user(admin_id) or await interaction.client.fetch_user(admin_id)
            if admin_user:
                guild_name = interaction.guild.name if interaction.guild else "DM/Ismeretlen szerver"
                channel_name = (f"#{interaction.channel.name}"
                                if (getattr(interaction, "channel", None) and
                                    getattr(interaction.channel, "name", None))
                                else "#ismeretlen-csatorna")
                await admin_user.send(
                    f"Szerver üzenet küldési hiba:\n"
                    f"Hiba: {str(e)}\n"
                    f"Hely: {guild_name} | {channel_name}\n"
                    f"Küldő: {interaction.user} (ID: {interaction.user.id})\n"
                    f"Címzett: {user} (ID: {user.id})\n"
                    f"Célcsatorna: {channel.name} (ID: {channel.id})"
                )
        except Exception as dm_err:
            print(f"Nem sikerült DM-et küldeni az adminnak: {dm_err}")

        await interaction.followup.send(
            "Váratlan hiba történt az üzenet küldése közben.",
            ephemeral=True
        )

tree.add_command(send_group)



# Help message constant
HELP_MESSAGE = """**Bot Parancsok**
*Alap parancsok:*
• `/help` - Ezt a súgót jeleníti meg
• `/level [felhasználó]` - Megmutatja a szinted és XP-d (vagy másét)
• `/global_level [felhasználó]` - Teljes XP állapot lekérdezése
• `/test <üzenet>` - Random teszt funkció 
• `/ping` - Bot késleltetés mutatása

*XP parancsok:*
• `/xp show [felhasználó]` - XP állapot lekérdezése 
• `/xp add <felhasználó> <mennyiség>` - XP hozzáadása (admin)
• `/xp remove <felhasználó> <mennyiség>` - XP levonása (admin)
• `/xp set <felhasználó> <mennyiség>` - XP beállítása (admin)
• `/top` - Toplista megjelenítése

*Üzenet parancsok:*
• `/send dm <üzenet> <felhasználó>` - Privát üzenet küldése
• `/send server <üzenet> <csatorna> [felhasználó]` - Üzenet küldése szerver csatornába

*FŐADMIN parancsok:*
• `/sql <text>` - sql lekérdezés (bot admin)
• `/poweroff` - bot leállítás (bot admin)
• `/reboot` - bot újraindítás (bot admin)
• `/update` - bot frissítés (bot admin)
"""

HELP_MESSAGE_NSFW = """
*NSFW parancsok*
• `/rule34` - nsfw kép generálás (NSFWcsatornában)
"""

@tree.command(name="help", description="Parancs súgó megjelenítése")
async def slash_help(interaction: discord.Interaction):
    try:
        if not interaction.channel.is_nsfw() and not isinstance(interaction.channel, discord.DMChannel):
            if test:
                print(HELP_MESSAGE)
            await interaction.response.send_message(HELP_MESSAGE)
        else:
            if test:
                print(HELP_MESSAGE_NSFW)
            await interaction.response.send_message(HELP_MESSAGE + HELP_MESSAGE_NSFW)
    except discord.HTTPException:
        await interaction.response.defer(ephemeral=True)
        await error_interaction(interaction, "Hiba történt a súgó megjelenítésekor.")

        # Töröljük az eredeti (ephemeral) választ, hogy a felhasználó ténylegesen ne lásson semmit
        with contextlib.suppress(Exception):
            await interaction.delete_original_response()


                                   ###################????###################


@tree.command(name="static", description="Bot statisztikák lekérése")
async def static(interaction: discord.Interaction):
    try:
        # Összesítés a szerverekről
        total_servers = len(client.guilds)
        total_members = sum(g.member_count for g in client.guilds)
        online_members = sum(1 for g in client.guilds for m in g.members if m.status != discord.Status.offline)

        # Eredmény formázása és küldése
        stats = (f"**Bot Statisztikák**\n"
                 f"• Szerverek száma: {total_servers}\n"
                 f"• Összes felhasználó: {total_members}\n"
                 f"• Online felhasználók: {online_members}")

        await interaction.response.send_message(stats, ephemeral=True)

    except Exception as e:
        await error_interaction(interaction, "Hiba a statisztikák lekérésekor", e)
        await interaction.response.send_message("Hiba történt a statisztikák lekérésekor", ephemeral=True)


@tree.command(name="sql")
@app_commands.check(admin_check)
@app_commands.describe(text="hivás")
async def sql(interaction: discord.Interaction, text: str):
    if leveldb is None:
        await interaction.response.send_message(
            'Az adatbázis nem érhető el, a szint funkció ideiglenesen nem működik.',
            ephemeral=True
        )
        return
    cursor = leveldb.cursor()
    try:
        cursor.execute(text)
        result = cursor.fetchone()
    except mysql.connector.Error as e:
        await interaction.response.send_message(
            f'Hiba a SQL-bevitelben: {e.msg}',
            ephemeral=True
        )
        return
    except Exception as e:
        await interaction.response.send_message(
            f'{e}',
            ephemeral=True
        )
        return
    finally:
        cursor.close()
    if result is None:
        await interaction.response.send_message(
            "üres lekérés",
            ephemeral=True
        )
    await interaction.response.send_message(
        str(result),
        ephemeral=True
    )

@tree.command(name="poweroff")
@app_commands.check(admin_check)
async def poweroff(interaction: discord.Interaction):
    await interaction.response.send_message(
        "égveled"
    )
    if leveldb:
        leveldb.close()  # Adatbázis kapcsolat lezárása

    print("Bot leállítás kezdeményezve...")
    await client.close()  # Discord kapcsolat tiszta lezárása
    os.system("poweroff")

@tree.command(name="reboot")
@app_commands.check(admin_check)
async def reboot(interaction: discord.Interaction):
    await interaction.response.send_message(
        "mindjárt jövök"
    )
    if leveldb:
        leveldb.close()  # Adatbázis kapcsolat lezárása

    print("Bot leállítás kezdeményezve...")
    await client.close()  # Discord kapcsolat tiszta lezárása
    os.system("reboot")

@tree.command(name="update")
@app_commands.check(admin_check)
async def update(interaction: discord.Interaction):
    await interaction.response.send_message(
        "mindjárt jövök"
    )
    if leveldb:
        leveldb.close()  # Adatbázis kapcsolat lezárása
    print("Bot leállítás kezdeményezve...")
    await client.close()  # Discord kapcsolat tiszta lezárása
    print(os.system("git pull"))
    os.system("nohup python3 main.py &")


##################################################SLASH függvények######################################################

@client.event                                       # Eseménykezelő regisztrálása a klienshez
async def on_ready():                               # Akkor fut, amikor a bot sikeresen csatlakozott és készen áll
    print(client.user.name)                         # Bot felhasználó nevének kiírása
    print(client.user.id)                           # Bot felhasználó azonosítójának kiírása
    print(leveldb)                                  # DB kapcsolat objektum kiírása (debug)
    print(discord.__version__)                      # discord.py verzió kiírása
    # SLASH parancsok szinkronizálása (globálisan)
    try:
        await tree.sync()
        print("Slash parancsok szinkronizálva.")
        # Extra: per-guild szinkronizáció és ellenőrzés
        for g in client.guilds:
            try:
                cmds = await tree.sync(guild=g)
                print(f"Per-guild sync kész: {g.name} ({g.id}). Parancsok: {[c.name for c in cmds]}")
            except Exception as ge:
                print(f"Per-guild sync hiba {g.name} ({g.id}): {ge}")

            cursor = leveldb.cursor()
            try:
                cursor.execute('SELECT * FROM servers WHERE id = %s', (g.id,))
                row1 = cursor.fetchone()

                if row1 is None:
                    cursor.execute(
                    'INSERT INTO servers (id) VALUES (%s)',
                    (g.id,))
                    leveldb.commit()
            except Exception as e:
                pass
        try:
            cursor.execute('SELECT * FROM servers WHERE id = %s', (0,))
            row1 = cursor.fetchone()

            if row1 is None:
                cursor.execute(
                'INSERT INTO servers (id) VALUES (0)')
                leveldb.commit()
        except Exception as e:
            pass

        # Globális parancsok listázása
        try:
            global_cmds = await tree.fetch_commands()
            print(f"Globális parancsok: {[c.name for c in global_cmds]}")
        except Exception as fe:
            print(f"Globális parancsok lekérése sikertelen: {fe}")
    except Exception as e:
        print(f"Slash parancs szinkronizáció hiba: {e}")

    # Havi ütemezett feladat indítása: minden hónap 1-jén 00:00 (Európa/Budapest időzóna)
    #asyncio.create_task(run_monthly_at(hour=0, minute=0, tz=ZoneInfo("Europe/Budapest")))
    asyncio.create_task(run_monthly_at(tz=ZoneInfo("Europe/Budapest")))

@client.event                                       # Üzenetekre reagáló eseménykezelő
async def on_message(message):                      # Minden bejövő üzenetre lefut (DM és szerver)
    if message.author.bot:                          # Ha az üzenet küldője bot
        return                                      # Ne reagáljunk botokra, elkerülve a végtelen loopokat

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
        await channel.send("Szia! Köszönöm a meghívást. Készen állok a használatra.")  # Üdvözlő üzenet

    if leveldb is not None:                         # Ha az adatbázis elérhető
        cursor = leveldb.cursor()                   # Kurzor nyitása
        try:                                        # Védett DB művelet
            cursor.execute(                         # Szerver bejegyzés létrehozása inicializáló értékekkel
                'INSERT INTO servers (id, welcome_ch, level_up_ch, level_sys) VALUES (%s, %s, %s, %s)',
                (guild.id, None, None, False)
            )
            leveldb.commit()                        # Tranzakció véglegesítése
        except mysql.connector.Error as e:
            try:
                admin_user = guild.get_user(admin_id) or await guild.client.fetch_user(admin_id)
                if admin_user is not None:
                    guild_name = guild.name if guild else "DM/Ismeretlen szerver"
                    await admin_user.send(
                        f"Parancs: {guild.me.guild_permissions.administrator} | {guild.me.guild_permissions.manage_guild}"
                        f"Új szervere belépés"
                        f"Adatbázis hiba: {e.msg}\n"
                        f"Hely: {guild_name} (ID {guild.id})\n"
                        f"Hibakód: {e.errno}\n"
                        f"SQL állapot: {e.sqlstate}\n"
                        f"Részletes hiba: {str(e)}"
                    )
            except Exception as dm_err:
                print(f"Nem sikerült DM-et küldeni az adminnak: {dm_err}")
            return
        except Exception as e:
            try:
                admin_user = guild.get_user(admin_id) or await guild.client.fetch_user(admin_id)
                if admin_user is not None:
                    guild_name = guild.name if guild else "DM/Ismeretlen szerver"
                    await admin_user.send(
                        f"Parancs: {guild.me.guild_permissions.administrator} | {guild.me.guild_permissions.manage_guild}"
                        f"Új szervere belépés"
                        f"Váratlan hiba történt: {str(e)}\n"
                        f"Hely: {guild_name} (ID {guild.id})\n"
                        f"Hiba típusa: {type(e).__name__}\n"
                        f"Hiba részletek: {repr(e)}"
                    )
            except Exception as dm_err:
                print(f"Nem sikerült DM-et küldeni az adminnak: {dm_err}")
            return
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
    except Exception as e:
        cursor.close()
        try:
            admin_user = client.get_user(admin_id) or await client.fetch_user(admin_id)
            if admin_user is not None:
                guild_name = member.guild.name if member.guild else "Ismeretlen szerver"
                await admin_user.send(
                    f"Parancs: {member.guild.me.guild_permissions.administrator} | "
                    f"{member.guild.me.guild_permissions.manage_guild}\n"
                    f"Új ember lépet be a szerverre\n"
                    f"Hiba történt új tag csatlakozásakor: {str(e)}\n"
                    f"Szerver: {guild_name} (ID: {member.guild.id})\n"
                    f"Tag: {member} (ID: {member.id})"
                )
        except Exception as dm_err:
            print(f"Nem sikerült DM-et küldeni az adminnak: {dm_err}")
        return
    finally:
        cursor.close()
    if channel is not None:                         # Ha csatorna létezik és elérhető
        await channel.send(f"Üdvözöllek {member.mention} ezen a szerveren!")  # Üdvözlő üzenet az új tagnak

@client.event
async def on_member_remove(member):
    pass


# Globális hiba-kezelő a dekorátorok CheckFailure üzeneteihez
@tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        try:
            await interaction.response.send_message(str(error), ephemeral=True)
        except discord.InteractionResponded:
            await interaction.followup.send(str(error), ephemeral=True)


client.run(token, log_handler=handler, log_level=logging.DEBUG)
                                                # Bot futtatása a megadott tokennel és naplózási beállításokkal
