# -*- coding: utf-8 -*-
# 2.0.0
# message.py

import discord
from config import config
import commands.info.help as help

client = config.client

@client.event                                       # Üzenetekre reagáló eseménykezelő
async def on_message(message):                      # Minden bejövő üzenetre lefut (DM és szerver)
    if message.author.bot:                          # Ha az üzenet küldője bot
        return                                      # Ne reagáljunk botokra, elkerülve a végtelen loopokat


