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

level1 = 500                                        # Kiinduló XP költség az első szinthez
levelq = 1.04                                       # Szintenkénti növekedési kvóciens (XP igény szorzója)
levels = [0,level1]
for i in range(1,100):                              # 1-től 99-ig generálunk küszöböket (összesen 100 szint körül)
    n = int(level1*math.pow(levelq,i))              # i-edik szinthez többlet XP (geometriai növekedés)
    m = levels[i] + n                               # Következő szint össz-XP küszöb (kumulált)
    levels.append(m)                                # Hozzáadás a listához

admin_id = 543856425131180036                       # Az admin fő fiókjának ID-ja

sess = requests.Session()

 
#####################################################init###############################################################


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



async def other_messege(message: discord.Message):
    if leveldb is None:  # Ha nincs DB, nem számolunk XP-t
        return
    # DM-ek kizárása – szerverhez nem kötött üzenetnél nincs guild/id
    if message.guild is None:
        return
    # Ne legyen negatív XP
    xp = gPX(message)  # XP becslés az üzenet tartalmából
    cursor = leveldb.cursor()
    if message in "UwU" | "uwu" | "UwU!" | "uwu!" | "UwU!!" | "uwu!!":
        xp += random.randint(20, 30)
        await message.channel.send(f"UwU!")


    try:  # Adatbázis műveletek védett része
        # Szerver beállítások lekérdezése: csak a szükséges oszlopok
        cursor.execute('SELECT level_up_ch, level_sys FROM servers WHERE id = %s', (message.guild.id,))
        row1 = cursor.fetchone()
        # Ha nincs szerver rekord, vagy ki van kapcsolva a szint rendszer, kilépünk
        if not row1:
            return
        level_up_ch, level_sys = row1


        # Meglévő adatok lekérdezése
        cursor.execute(
            'SELECT user_xp, level FROM server_users WHERE id = %s AND server_id = %s',
            (message.author.id, message.guild.id)
        )
        row = cursor.fetchone()  # Eredmény beolvasása


        if row is None:  # Ha új felhasználó ezen a szerveren
            try:  # Beszúrás próbálkozás
                cursor.execute(
                    'INSERT INTO server_users (id, server_id, user_xp, level) VALUES (%s, %s, %s, %s)',
                    (message.author.id, message.guild.id, xp, 0)
                )
                leveldb.commit()  # Tranzakció véglegesítése
            except mysql.connector.Error as e:  # DB hiba esetén
                leveldb.rollback()  # Visszagörgetés
                await message.channel.send(f'Hiba az adatbázis beszúráskor: {e.msg}')  # Hibaüzenet
                try:
                    admin_user = message.client.get_user(admin_id) or await message.client.fetch_user(admin_id)
                    if admin_user is not None:
                        guild_name = message.guild.name if message.guild else "DM/Ismeretlen szerver"
                        channel_name = f"#{message.channel.name}" if (getattr(message, "channel", None)
                                                                          and getattr(message.channel, "name",
                                                                                      None)) else "#ismeretlen-csatorna"
                        await admin_user.send(
                            f"XP rendszer hiba újelem beszúrásánál\n"
                            f"Váratlan hiba történt: {str(e)}"
                            f"Hely: {guild_name} | {channel_name}\n"
                            f"Küldő: {message.user} (ID: {message.user.id})"
                        )
                except Exception as dm_err:
                    print(f"Nem sikerült DM-et küldeni az adminnak: {dm_err}")

        else:  # Ha már létezik rekord
            current_xp = row[0] + xp  # Új összesített XP kiszámítása
            if current_xp < 0:
                current_xp = 0
            new_level = level(current_xp)  # Új szint meghatározása
            try:  # Frissítés és szintlépés kezelése
                # Felhasználó rekordjának frissítése
                cursor.execute(
                    'UPDATE server_users SET user_xp = %s, level = %s WHERE id = %s AND server_id = %s',
                    (current_xp, new_level, message.author.id, message.guild.id)
                )
                leveldb.commit()  # Tranzakció véglegesítése

                # Szintlépés értesítés csak sikeres commit után
                if row[1] < new_level and row1[1] == 1:
                    channel = client.get_channel(int(level_up_ch)) if level_up_ch else None
                    try:
                        await message.author.send(f"{new_level}. szintű lettél")

                    except Exception:
                        pass
                    if channel is not None:
                        await channel.send(f"{message.author.mention} {new_level}. szintű lett")
                    else:
                        await message.channel.send(f"{message.author.mention} {new_level}. szintű lett")
            except mysql.connector.Error as e:
                leveldb.rollback()  # Visszagörgetés
                try:
                    admin_user = message.client.get_user(admin_id) or await message.client.fetch_user(admin_id)
                    if admin_user is not None:
                        guild_name = message.guild.name if message.guild else "DM/Ismeretlen szerver"
                        channel_name = f"#{message.channel.name}" if (getattr(message, "channel", None)
                                                                          and getattr(message.channel, "name",
                                                                                      None)) else "#ismeretlen-csatorna"
                        await admin_user.send(
                            f"Hiba XP frissítés közben\n"
                            f"Váratlan hiba történt: {str(e)}"
                            f"Hely: {guild_name} | {channel_name}\n"
                            f"Küldő: {message.user} (ID: {message.user.id})"
                        )
                except Exception as dm_err:
                    print(f"Nem sikerült DM-et küldeni az adminnak: {dm_err}")

                
    except mysql.connector.Error as e:
        await message.channel.send(f'Hiba frissítés közben: {e.msg}')

    finally:  # Mindig lefut
        cursor.close()  # Kurzor lezárása

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
        try:
            admin_user = interaction.client.get_user(admin_id) or await interaction.client.fetch_user(admin_id)
            if admin_user is not None:
                guild_name = interaction.guild.name if interaction.guild else "DM/Ismeretlen szerver"
                channel_name = f"#{interaction.channel.name}" if (getattr(interaction, "channel", None)
                                                                  and getattr(interaction.channel, "name",
                                                                              None)) else "#ismeretlen-csatorna"
                await admin_user.send(
                    f"Parancs: {interaction.command.name}\n"
                    f"Váratlan hiba történt: {str(e)}\n"
                    f"Hely: {guild_name} | {channel_name}\n"
                    f"Küldő: {interaction.user} (ID: {interaction.user.id})"
                )
        except Exception as dm_err:
            print(f"Nem sikerült DM-et küldeni az adminnak: {dm_err}")

        # Töröljük az eredeti (ephemeral) választ, hogy a felhasználó ténylegesen ne lásson semmit
        with contextlib.suppress(Exception):
            await interaction.delete_original_response()
        return


    if status_code != 200:
        # Admin értesítése, majd rövid hibaüzenet
        try:
            admin_user = interaction.client.get_user(admin_id) or await interaction.client.fetch_user(admin_id)
            if admin_user is not None:
                guild_name = interaction.guild.name if interaction.guild else "DM/Ismeretlen szerver"
                channel_name = f"#{interaction.channel.name}" if (getattr(interaction, "channel", None)
                                                                  and getattr(interaction.channel, "name",
                                                                              None)) else "#ismeretlen-csatorna"
                await admin_user.send(
                    f"Parancs: {interaction.command.name}\n"
                    f"A rule34.xxx nem sikerült elérni (HTTP {status_code})\n"
                    f"Hely: {guild_name} | {channel_name}\n"
                    f"Küldő: {interaction.user.mention} (ID: {interaction.user.id}) (name: {interaction.user.name})"
                )
        except Exception as dm_err:
            print(f"Nem sikerült DM-et küldeni az adminnak: {dm_err}")
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
        print(f"Parsing hiba: {parse_err}")
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
        try:
            admin_user = interaction.client.get_user(admin_id) or await interaction.client.fetch_user(admin_id)
            if admin_user is not None:
                guild_name = interaction.guild.name if interaction.guild else "DM/Ismeretlen szerver"
                channel_name = f"#{interaction.channel.name}" if (getattr(interaction, "channel", None)
                                                                  and getattr(interaction.channel, "name",
                                                                              None)) else "#ismeretlen-csatorna"
                await admin_user.send(
                    f"Parancs: {interaction.command.name}\n"
                    f"Adatbázis hiba: {e.msg}"
                    f"Hely: {guild_name} | {channel_name}\n"
                    f"Küldő: {interaction.user} (ID: {interaction.user.id})"
                )
        except Exception as dm_err:
            print(f"Nem sikerült DM-et küldeni az adminnak: {dm_err}")

        # Töröljük az eredeti (ephemeral) választ, hogy a felhasználó ténylegesen ne lásson semmit
        with contextlib.suppress(Exception):
            await interaction.delete_original_response()
        return 
    except Exception as e:
        await interaction.response.defer(ephemeral=True)
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

@xp_group.command(name="remove", description="XP elvétele egy felhasználótól (admin).")
@app_commands.describe(user="A felhasználó, akitől XP-t veszel el.", amount="Mennyit vonjunk le (pozitív egész).")
@app_commands.guild_only()
@app_commands.check(admin_or_owner_check)
async def xp_remove(interaction: discord.Interaction, user: discord.Member, amount: int):
    if leveldb is None:
        await interaction.response.send_message('Az adatbázis nem érhető el.', ephemeral=True)
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
        f'{user.mention} XP-je beállítva: {new_xp} (szint: {new_level})', ephemeral=True
    )

# Regisztráljuk a csoportot a parancsfához
tree.add_command(xp_group)



@tree.command(name="top")
async def top_command(interaction: discord.Interaction):
    if leveldb is None:  # DB nélkül nem megy
        await interaction.channel.send('Az adatbázis nem érhető el, a toplista ideiglenesen nem működik.')  # Visszajelzés
        return
    cursor = leveldb.cursor()  # Kurzor nyitása
    try:  # Védett DB művelet
        cursor.execute(  # Legjobb 10 felhasználó XP szerint adott szerveren
            'SELECT id, user_xp FROM server_users WHERE server_id = %s ORDER BY user_xp DESC LIMIT 10',
            (interaction.guild.id,)
        )
        result = cursor.fetchall()  # Minden sor beolvasása
    except mysql.connector.Error as e:
        await interaction.response.defer(ephemeral=True)
        try:
            admin_user = interaction.client.get_user(admin_id) or await interaction.client.fetch_user(admin_id)
            if admin_user is not None:
                guild_name = interaction.guild.name if interaction.guild else "DM/Ismeretlen szerver"
                channel_name = f"#{interaction.channel.name}" if (getattr(interaction, "channel", None)
                                                                  and getattr(interaction.channel, "name",
                                                                              None)) else "#ismeretlen-csatorna"
                await admin_user.send(
                    f"Parancs: {interaction.command.name}\n"
                    f"Adatbázis hiba: {e.msg}"
                    f"Hely: {guild_name} | {channel_name}\n"
                    f"Küldő: {interaction.user} (ID: {interaction.user.id})"
                )
        except Exception as dm_err:
            print(f"Nem sikerült DM-et küldeni az adminnak: {dm_err}")

        # Töröljük az eredeti (ephemeral) választ, hogy a felhasználó ténylegesen ne lásson semmit
        with contextlib.suppress(Exception):
            await interaction.delete_original_response()
        return 
    except Exception as e:
        await interaction.response.defer(ephemeral=True)
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

    await interaction.followup.send(embed=embed,ephemeral=True)  # Embed küldése a csatornára

# SLASH parancs: /level [user]
@tree.command(name="level", description="Megmutatja a szintedet és XP-det (vagy egy megadott felhasználóét).")
@app_commands.describe(user="Opcionális: válassz felhasználót, akinek az adatait lekérdezed.")
async def slash_level(interaction: discord.Interaction, user: discord.Member | None = None):
    if leveldb is None:
        await interaction.response.send_message(
            'Az adatbázis nem érhető el, a szint funkció ideiglenesen nem működik.',
            ephemeral=True
        )
        return
    if interaction.guild is None:
        await interaction.response.send_message('Ez a parancs csak szerveren használható.', ephemeral=True)
        return

    target = user or interaction.user
    cursor = leveldb.cursor()
    try:
        cursor.execute(
            'SELECT id, user_xp, level FROM server_users WHERE id = %s AND server_id = %s',
            (target.id, interaction.guild.id)
        )
        result = cursor.fetchone()
    except mysql.connector.Error as e:
        await interaction.response.defer(ephemeral=True)
        try:
            admin_user = interaction.client.get_user(admin_id) or await interaction.client.fetch_user(admin_id)
            if admin_user is not None:
                guild_name = interaction.guild.name if interaction.guild else "DM/Ismeretlen szerver"
                channel_name = f"#{interaction.channel.name}" if (getattr(interaction, "channel", None)
                                                                  and getattr(interaction.channel, "name",
                                                                              None)) else "#ismeretlen-csatorna"
                await admin_user.send(
                    f"Parancs: {interaction.command.name}\n"
                    f"Adatbázis hiba: {e.msg}\n"
                    f"Hely: {guild_name} | {channel_name}\n"
                    f"Küldő: {interaction.user} (ID: {interaction.user.id})"
                )
        except Exception as dm_err:
            print(f"Nem sikerült DM-et küldeni az adminnak: {dm_err}")

        # Töröljük az eredeti (ephemeral) választ, hogy a felhasználó ténylegesen ne lásson semmit
        with contextlib.suppress(Exception):
            await interaction.delete_original_response()
        return 
    except Exception as e:
        await interaction.response.defer(ephemeral=True)
        try:
            admin_user = interaction.client.get_user(admin_id) or await interaction.client.fetch_user(admin_id)
            if admin_user is not None:
                guild_name = interaction.guild.name if interaction.guild else "DM/Ismeretlen szerver"
                channel_name = f"#{interaction.channel.name}" if (getattr(interaction, "channel", None)
                                                                  and getattr(interaction.channel, "name",
                                                                              None)) else "#ismeretlen-csatorna"
                await admin_user.send(
                    f"Parancs: {interaction.command.name}\n"
                    f"Váratlan hiba történt: {str(e)}\n"
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

    if result is None:
        await interaction.response.send_message(
            f'{target.mention} még nem rendelkezik adatokkal ezen a szerveren.',
            ephemeral=True
        )
        return

    lvl = int(result[2])
    total_xp = int(result[1])
    # Szint progressz
    if lvl + 1 < len(levels):
        have = total_xp - levels[lvl]
        need = levels[lvl + 1] - levels[lvl]
    else:
        have = 0
        need = 0

    await interaction.response.send_message(
        f'{target.mention} szintje: {lvl}\n'
        f'Következő szinthez: {have}/{need}\n'
        f'Összes XP: {total_xp}'
    )

# SLASH parancs: /global_level [user]
@tree.command(name="global_level", description="Megmutatja a szintedet és XP-det (vagy egy megadott felhasználóét).")
@app_commands.describe(user="Opcionális: válassz felhasználót, akinek az adatait lekérdezed.")
async def slash_global_level(interaction: discord.Interaction, user: discord.Member | None = None):
    if leveldb is None:
        await interaction.response.send_message(
            'Az adatbázis nem érhető el, a szint funkció ideiglenesen nem működik.',
            ephemeral=True
        )
        return

    target = user or interaction.user
    cursor = leveldb.cursor()
    try:
        cursor.execute(
            'SELECT COALESCE(SUM(su.user_xp), 0) AS total_xp FROM server_users su WHERE su.id = %s;',
            (target.id,)
        )
        result = cursor.fetchone()
    except mysql.connector.Error as e:
        await interaction.response.defer(ephemeral=True)
        try:
            admin_user = interaction.client.get_user(admin_id) or await interaction.client.fetch_user(admin_id)
            if admin_user is not None:
                guild_name = interaction.guild.name if interaction.guild else "DM/Ismeretlen szerver"
                channel_name = f"#{interaction.channel.name}" if (getattr(interaction, "channel", None)
                                                                  and getattr(interaction.channel, "name",
                                                                              None)) else "#ismeretlen-csatorna"
                await admin_user.send(
                    f"Parancs: {interaction.command.name}\n"
                    f"Adatbázis hiba: {e.msg}\n"
                    f"Hely: {guild_name} | {channel_name}\n"
                    f"Küldő: {interaction.user} (ID: {interaction.user.id})"
                )
        except Exception as dm_err:
            print(f"Nem sikerült DM-et küldeni az adminnak: {dm_err}")

        # Töröljük az eredeti (ephemeral) választ, hogy a felhasználó ténylegesen ne lásson semmit
        with contextlib.suppress(Exception):
            await interaction.delete_original_response()
        return
    except Exception as e:
        await interaction.response.defer(ephemeral=True)
        try:
            admin_user = interaction.client.get_user(admin_id) or await interaction.client.fetch_user(admin_id)
            if admin_user is not None:
                guild_name = interaction.guild.name if interaction.guild else "DM/Ismeretlen szerver"
                channel_name = f"#{interaction.channel.name}" if (getattr(interaction, "channel", None)
                                                                  and getattr(interaction.channel, "name",
                                                                              None)) else "#ismeretlen-csatorna"
                await admin_user.send(
                    f"Parancs: {interaction.command.name}\n"
                    f"Váratlan hiba történt: {str(e)}\n"
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


    total_xp = int(result[0])
    lvl = level(total_xp)
    # Szint progressz
    if lvl + 1 < len(levels):
        have = total_xp - levels[lvl]
        need = levels[lvl + 1] - levels[lvl]
    else:
        have = 0
        need = 0

    await interaction.response.send_message(
        f'{target.mention} szintje: {lvl}\n'
        f'Következő szinthez: {have}/{need}\n'
        f'Összes XP: {total_xp}'
    )

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
async def send_server(interaction: discord.Interaction, text: str, channel: discord.TextChannel, user: discord.Member | None = None):
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
"""

@tree.command(name="help", description="Parancs súgó megjelenítése")
async def slash_help(interaction: discord.Interaction):
    try:
        await interaction.response.send_message(HELP_MESSAGE)
    except discord.HTTPException:
        await interaction.response.defer(ephemeral=True)
        try:
            admin_user = interaction.client.get_user(admin_id) or await interaction.client.fetch_user(admin_id)
            if admin_user is not None:
                guild_name = interaction.guild.name if interaction.guild else "DM/Ismeretlen szerver"
                channel_name = f"#{interaction.channel.name}" if (getattr(interaction, "channel", None) 
                                                                  and getattr(interaction.channel, "name", None)) else "#ismeretlen-csatorna"
                await admin_user.send(
                    f"Parancs: {interaction.command.name}\n"
                    f"Hiba történt a súgó megjelenítésekor.\n"
                    f"Hely: {guild_name} | {channel_name}\n"
                    f"Küldő: {interaction.user} (ID: {interaction.user.id})"
                )
        except Exception as dm_err:
            print(f"Nem sikerült DM-et küldeni az adminnak: {dm_err}")

        # Töröljük az eredeti (ephemeral) választ, hogy a felhasználó ténylegesen ne lásson semmit
        with contextlib.suppress(Exception):
            await interaction.delete_original_response()


                                   ###################????###################

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
        # Globális parancsok listázása
        try:
            global_cmds = await tree.fetch_commands()
            print(f"Globális parancsok: {[c.name for c in global_cmds]}")
        except Exception as fe:
            print(f"Globális parancsok lekérése sikertelen: {fe}")
    except Exception as e:
        print(f"Slash parancs szinkronizáció hiba: {e}")

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
                    f"Parancs: {member.guild.me.guild_permissions.administrator} | {member.guild.me.guild_permissions.manage_guild}"
                    f"Új ember lépet be a szerverre"
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
