# -*- coding: utf-8 -*-
# 2.0.0
# main.py

import init
from init import tree, client
import discord
from discord.ext import commands
import logging
import info.ping  # ping modul importálása, hogy a parancs regisztrálódjon
                                           
@client.event  # Eseménykezelő regisztrálása a klienshez
async def on_ready():  # Akkor fut, amikor a bot sikeresen csatlakozott és készen áll
    print(client.user.name)  # Bot felhasználó nevének kiírása
    print(client.user.id)  # Bot felhasználó azonosítójának kiírása
    #print(leveldb)  # DB kapcsolat objektum kiírása (debug)
    print(discord.__version__)  # discord.py verzió kiírása
    for g in client.guilds: # Végigmegy a bot által elérhető szervereken
            try:
                cmds = await tree.sync(guild=g) # Parancsok szinkronizálása az adott szerverrel
                print(f"Per-guild sync kész: {g.name} ({g.id}).\nParancsok: {[c.name for c in cmds]}")
            except Exception as ge:
                print(f"Per-guild sync hiba {g.name} ({g.id}): {ge}")
    global_cmds = await tree.fetch_commands()
    print(f"Globális parancsok: {[c.name for c in global_cmds]}")

    print(f'Bejelentkezve mint {client.user} (ID: {client.user.id})')
    print('------')


if __name__ == '__main__':
    client.run(init.token, log_handler=init.handler, log_level=logging.DEBUG)