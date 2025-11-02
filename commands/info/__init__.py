# -*- coding: utf-8 -*-
# commands/__init__.py
# Parancsok regisztrációja


if __name__ == '__main__':
    exit(1)

from .ping import register_ping_command
from .help import register_help_command, register_help_command_dm

# Elérhető parancsok registry (guild-ekhez)
AVAILABLE_COMMANDS = {
    "ping": register_ping_command,
    # "stats": register_stats_command,  # Később hozzáadható
    "help": register_help_command,
}

# DM parancsok registry
DM_COMMANDS = {
    "ping": register_ping_command,
    # "stats": register_stats_command_dm,
    "help": register_help_command_dm,
}

def register_commands_info(tree, client, guild=None, enabled_commands=None):
    """
    Parancsok regisztrálása egy adott szerverre

    Args:
        tree: CommandTree példány
        client: Discord Client példány
        guild: Discord Guild objektum
        enabled_commands: Engedélyezett parancsok listája (pl. ["ping", "stats"])
    """
    registered_count = 0

    if guild not in [None, client.guilds[0]]:
        for cmd_name in enabled_commands:
            if cmd_name in AVAILABLE_COMMANDS:
                try:
                    AVAILABLE_COMMANDS[cmd_name](tree, client, guild=guild)
                    registered_count += 1
                except Exception as e:
                    print(f"  ✗ Hiba a '{cmd_name}' regisztrálásakor: {e}")
            else:
                print(f"  ⚠️ Ismeretlen parancs: {cmd_name}")
    else:
        # DM parancsok regisztrálása globálisan (de csak DM-ben működnek)
        for cmd_name, register_func in DM_COMMANDS.items():
            try:
                register_func(tree, client)
                registered_count += 1
            except Exception as e:
                print(f"  ✗ Hiba a '{cmd_name}' DM regisztrálásakor: {e}")

    return registered_count




def get_available_commands():
    """Összes elérhető parancs nevének listája"""
    return list(AVAILABLE_COMMANDS.keys())


def get_dm_commands():
    """DM-ben elérhető parancsok listája"""
    return list(DM_COMMANDS.keys())