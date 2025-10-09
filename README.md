# Eris Bot

Discord bot XP/level rendszerrel, slash parancsokkal és opcionális MySQL adatbázissal.

## Meghívás
[Bot meghívása](https://discord.com/oauth2/authorize?client_id=1412928677980930108&permissions=8&integration_type=0&scope=bot)

## Fő funkciók
- XP és szint rendszer üzenet-aktivitás alapján (képes üzenetek plusz XP-t adnak)
- Toplista a legtöbb XP-vel rendelkező tagokról
- Slash parancsok (/rank, /xp csoport, /top, /help, /test)
- Szintlépés értesítés (DM és/vagy csatorna)
- Opcionális üdvözlő üzenet új tagoknak
- NSFW parancs: /rule34 (csak NSFW csatornában)
- Admin parancsok: bot leállítás, újraindítás, frissítés

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
Hozz létre egy .env fájlt a projekt gyökerében, és add meg benne a Discord token-t, valamint (ha szükséges) az adatbázis elérési adatokat. A bot hibanaplója a error.log fájlba íródik.

## Parancsok
- /help – Súgó
- /rank [felhasználó] – Szint és XP lekérdezése
- /top – Top 10 felhasználó XP alapján

XP parancs csoport (/xp):
- /xp show [felhasználó] – XP lekérdezése
- /xp add <felhasználó> <mennyiség> – XP hozzáadása
- /xp remove <felhasználó> <mennyiség> – XP levonása
- /xp set <felhasználó> <mennyiség> – XP beállítása

Üzenet parancsok:
- /send dm <üzenet> <felhasználó> – Privát üzenet küldése

Csatorna beállítás parancsok:
- /set_welcome_channel <csatorna> – Üdvözlő csatorna beállítása (admin)
- /set_goodbye_channel <csatorna> – Távozó csatorna beállítása (admin)
- /set_level_up_channel <csatorna> – Szintlépő csatorna beállítása (admin)

NSFW parancsok:
- /rule34 [keresés] – NSFW kép keresése vagy véletlenszerű kép (csak NSFW csatornában)

Főadmin parancsok:
- /poweroff – Bot leállítás (bot admin)
- /reboot – Bot újraindítás (bot admin)
- /update – Bot frissítés (bot admin)

Jogosultság:
- Az /xp add/remove/set parancsok csak szerver adminoknak érhetők el (vagy a kódban megadott tulajdonos azonosítónak).

## Meghívási jogosultságok
A fenti meghívó link admin jogosultságokat kér. Ha szűkíteni szeretnéd:
- Legalább: Üzenetek olvasása/küldése, Embed küldése, Szerver tagok olvasása (intents), Alap csatorna-hozzáférés.

## Hibaelhárítás
- „DISCORD_TOKEN nincs beállítva” – Ellenőrizd a `.env` fájlt és a betöltési útvonalat.
- „Az adatbázis nem érhető el…” – Futtat a MySQL? Helyesek a hitelesítési adatok? Léteznek a táblák?
- Parancsok nem látszanak – Várj pár percet a slash parancsok szinkronjára, vagy indítsd újra a botot.
- Jogosultsági hibák – Ellenőrizd a bot jogosultságait a szerveren és a csatornákon.
- Egyéb hibák – Nézd meg a `discord.log` fájlt a részletes naplóért.

## Fejlesztői jegyzetek
- A parancsok globálisan szinkronizálódnak induláskor, majd per-szerver ellenőrzés történik.
- Szintlépéskor DM és/vagy csatorna-értesítés történhet (ha be van állítva `level_up_ch`).
- Üdvözlő és távozó üzenetek opcionálisak, ha a megfelelő csatornák be vannak állítva.
- A bot admin ID-ját a kódban kell megadni a főadmin parancsokhoz.
- A MySQL adatbázis használata opcionális, a bot működik nélküle is, de az XP/level funkciók nem lesznek elérhetők.
- A bot hibanaplózása a `error.log` fájlba történik, ami segít a hibakeresésben.
- Havi XP nullázás automatikusan történik minden hónap első napján.