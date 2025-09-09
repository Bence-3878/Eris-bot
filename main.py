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


load_dotenv()                                       # .env fájl beolvasása a környezeti változókhoz
token = os.getenv('DISCORD_TOKEN')                  # A Discord bot token kiolvasása környezetből

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')  # Naplófájl kezelő beállítása
intents = discord.Intents.default()                 # Alapértelmezett intentek (engedélyek) létrehozása
intents.message_content = True                      # Üzenettartalom olvasásának engedélyezése (parancsokhoz szükséges)
intents.members = True                              # Tag események engedélyezése (pl. belépés)

client = discord.Client(intents=intents)            # Discord kliens példány létrehozása a megadott intentekkel
tree = app_commands.CommandTree(client)             # SLASH parancs fa a Client-hez

level1 = 100                                        # Kiinduló XP költség az első szinthez
levelq = 1.05                                       # Szintenkénti növekedési kvóciens (XP igény szorzója)
levels = [0,level1]
for i in range(1,100):                              # 1-től 99-ig generálunk küszöböket (összesen 100 szint körül)
    n = int(level1*math.pow(levelq,i))              # i-edik szinthez többlet XP (geometriai növekedés)
    m = levels[i] + n                               # Következő szint össz-XP küszöb (kumulált)
    levels.append(m)                                # Hozzáadás a listához

admin_id = 543856425131180036                       # Az admin fő fiókjának ID-ja
 
 
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
                if row[1] < new_level:
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
                await message.channel.send(f'Hiba frissítés közben: {e.msg}')  # Hibaüzenet
    except mysql.connector.Error as e:
        await message.channel.send(f'Hiba frissítés közben: {e.msg}')

    finally:  # Mindig lefut
        cursor.close()  # Kurzor lezárása


##############################################aszinkron függvények######################################################

# XP parancscsoport: /xp show|add|remove|set
xp_group = app_commands.Group(name="xp", description="XP és szint műveletek")

# Közös jogosultság ellenőrzés: csak szerveren, és csak admin vagy az admin_id
async def admin_or_owner_check(interaction: discord.Interaction) -> bool:
    if interaction.guild is None:
        raise app_commands.CheckFailure('Ez a parancs csak szerveren használható.')
    if not (interaction.user.guild_permissions.administrator or interaction.user.id == admin_id):
        raise app_commands.CheckFailure('Nincs jogosultságod ehhez a parancshoz.')
    return True

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

    await interaction.channel.send(embed=embed)  # Embed küldése a csatornára

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
        await interaction.response.send_message(f'Hiba: {e}', ephemeral=True)
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
        await interaction.response.send_message(f'Hiba: {e}', ephemeral=True)
        return
    finally:
        cursor.close()

    await interaction.response.send_message(
        f'{user.mention} új XP-je: {new_xp} (szint: {new_level})', ephemeral=True
    )

@xp_group.command(name="set", description="XP közvetlen beállítása (admin).")
@app_commands.describe(user="A felhasználó, akinek beállítod az XP-t.", amount="Az új XP érték (0 vagy pozitív egész).")
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
        await interaction.response.send_message(f'Hiba: {e}', ephemeral=True)
        return
    finally:
        cursor.close()

    await interaction.response.send_message(
        f'{user.mention} XP-je beállítva: {new_xp} (szint: {new_level})', ephemeral=True
    )

# Regisztráljuk a csoportot a parancsfához
tree.add_command(xp_group)

# Globális hiba-kezelő a dekorátorok CheckFailure üzeneteihez
@tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        try:
            await interaction.response.send_message(str(error), ephemeral=True)
        except discord.InteractionResponded:
            await interaction.followup.send(str(error), ephemeral=True)

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

@tree.command(name="test", description="Random teszt funkció. Probáld ki ha mered.")
@app_commands.describe(text="üzenet")
async def slash_test(interaction: discord.Interaction, text: str):
    # A slash opciót paraméterként kapjuk meg
    print(text)

# Help message constant
HELP_MESSAGE = """**Bot Parancsok**
*Alap parancsok:*
• `/help` - Ezt a súgót jeleníti meg
• `/level [felhasználó]` - Megmutatja a szinted és XP-d (vagy másét)
• `/test` - Random teszt funkció

*XP parancsok:*
• `/xp show [felhasználó]` - XP állapot lekérdezése
• `/xp add <felhasználó> <mennyiség>` - XP hozzáadása (admin)
• `/xp remove <felhasználó> <mennyiség>` - XP levonása (admin) 
• `/xp set <felhasználó> <mennyiség>` - XP beállítása (admin)
• `/top` - Toplista megjelenítése
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
                    f"Hiba történt a súgó megjelenítésekor.\n"
                    f"Hely: {guild_name} | {channel_name}\n"
                    f"Küldő: {interaction.user} (ID: {interaction.user.id})"
                )
        except Exception as dm_err:
            print(f"Nem sikerült DM-et küldeni az adminnak: {dm_err}")

        # Töröljük az eredeti (ephemeral) választ, hogy a felhasználó ténylegesen ne lásson semmit
        with contextlib.suppress(Exception):
            await interaction.delete_original_response()


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
