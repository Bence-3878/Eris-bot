# -*- coding: utf-8 -*-
# commands/info/__init__.py
# Parancsok regisztrációja

from .server import register_server_commands

# Elérhető parancsok registry (guild-ekhez)
AVAILABLE_COMMANDS = {
    "server": register_server_commands,
}

# DM parancsok registry
DM_COMMANDS = {

}

def register_commands_send(tree, client, guild, enabled_commands):
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


def register_dm_commands_send(tree, client):
    """
    Globális parancsok regisztrálása (CSAK DM támogatáshoz)

    Args:
        tree: CommandTree példány
        client: Discord Client példány

    Returns:
        int: Regisztrált parancsok száma
    """
    registered_count = 0

    # DM parancsok regisztrálása globálisan (de csak DM-ben működnek)
    for cmd_name, register_func in DM_COMMANDS.items():
        try:
            register_func(tree, client)
            registered_count += 1
        except Exception as e:
            print(f"  ✗ Hiba a '{cmd_name}' DM regisztrálásakor: {e}")

    return registered_count


def get_available_commands_send():
    """Összes elérhető parancs nevének listája"""
    return list(AVAILABLE_COMMANDS.keys())


def get_dm_commands_send():
    """DM-ben elérhető parancsok listája"""
    return list(DM_COMMANDS.keys())