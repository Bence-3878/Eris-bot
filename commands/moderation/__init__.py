# -*- coding: utf-8 -*-
# commands/mod/__init__.py
# Parancsok regisztrációja

from .kick import register_kick_command
from .ban import register_ban_command

# Elérhető parancsok registry (guild-ekhez)
AVAILABLE_COMMANDS = {
    "ping": register_kick_command,
    "help": register_ban_command,
}


def register_commands_mod(tree, client, guild, enabled_commands):
    """
    Parancsok regisztrálása egy adott szerverre

    Args:
        tree: CommandTree példány
        client: Discord Client példány
        guild: Discord Guild objektum
        enabled_commands: Engedélyezett parancsok listája (pl. ["ping", "stats"])
    """
    registered_count = 0

    for cmd_name in enabled_commands:
        if cmd_name in AVAILABLE_COMMANDS:
            try:
                AVAILABLE_COMMANDS[cmd_name](tree, client, guild=guild)
                registered_count += 1
            except Exception as e:
                print(f"  ✗ Hiba a '{cmd_name}' regisztrálásakor: {e}")
        else:
            print(f"  ⚠️ Ismeretlen parancs: {cmd_name}")

    return registered_count



def get_available_commands_mod():
    """Összes elérhető parancs nevének listája"""
    return list(AVAILABLE_COMMANDS.keys())
