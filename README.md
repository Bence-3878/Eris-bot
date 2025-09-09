# Eris Bot

Discord bot XP/level rendszerrel, slash parancsokkal és opcionális MySQL adatbázissal.

## Meghívás
[Bot meghívása](https://discord.com/oauth2/authorize?client_id=1412928677980930108&permissions=8&integration_type=0&scope=bot)

## Fő funkciók
- XP és szint rendszer üzenet-aktivitás alapján (képes üzenetek plusz XP-t adnak)
- Toplista a legtöbb XP-vel rendelkező tagokról
- Slash parancsok (/level, /xp csoport, /top, /help, /test)
- Szintlépés értesítés (DM és/vagy csatorna)
- Opcionális üdvözlő üzenet új tagoknak

## Követelmények
- Python 3.10+ (ajánlott 3.13)
- Discord bot alkalmazás és token
- Opcionális: MySQL 8.x (vagy kompatibilis) az XP/level funkciókhoz

## Telepítés
```bash
python3 -m venv venv; 
source venv/bin/activate; 
pip install --upgrade pip; 
pip install -r requirements.txt; 
```
Megjegyzés:
- A `math` a Python szabványkönyvtár része, nem kell telepíteni.
- A MySQL kliens csomag neve: `mysql-connector-python`.

## Konfiguráció
Hozz létre egy `.env` fájlt a projekt gyökerében:
A bot naplója a `discord.log` fájlba íródik.

## Parancsok
- /help – Súgó
- /level [felhasználó] – Szint és XP lekérdezése
- /top – Toplista (szerver szinten)
- /test <szöveg> – Teszt parancs

XP parancs csoport (/xp):
- /xp show [felhasználó] – XP lekérdezése
- /xp add <felhasználó> <mennyiség> – XP hozzáadása
- /xp remove <felhasználó> <mennyiség> – XP levonása
- /xp set <felhasználó> <mennyiség> – XP beállítása

Jogosultság:
- Az /xp add/remove/set parancsok csak szerver adminoknak érhetők el (vagy a kódban megadott tulajdonos azonosítónak).

## Meghívási jogosultságok
A fenti meghívó link admin jogosultságokat kér. Ha szűkíteni szeretnéd:
- Legalább: Üzenetek olvasása/küldése, Embed küldése, Szerver tagok olvasása (intents), Alap csatorna-hozzáférés.

## Hibaelhárítás
- „DISCORD_TOKEN nincs beállítva” – Ellenőrizd a `.env` fájlt és a betöltési útvonalat.
- „Az adatbázis nem érhető el…” – Futtat a MySQL? Helyesek a hitelesítési adatok? Léteznek a táblák?
- Parancsok nem látszanak – Várj pár percet a slash parancsok szinkronjára, vagy indítsd újra a botot.
- Nincs XP növekedés – Kapcsolt be a `level_sys` az adott szerveren, és a botnak legyen Message Content Intentje.

## Fejlesztői jegyzetek
- A parancsok globálisan szinkronizálódnak induláskor, majd per-szerver ellenőrzés történik.
- Szintlépéskor DM és/vagy csatorna-értesítés történhet (ha be van állítva `level_up_ch`).