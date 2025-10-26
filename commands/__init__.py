# -*- coding: utf-8 -*-
# commands/__init__.py
# Parancsok regisztrációja

from commands.ping import register_ping_command


# Elérhető parancsok registry
AVAILABLE_COMMANDS = {
    "ping": register_ping_command,
    # "stats": register_stats_command,  # Később hozzáadható
    # "help": register_help_command,
}


def register_commands_for_guild(tree, client, guild, enabled_commands):
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


def get_available_commands():
    """Összes elérhető parancs nevének listája"""
    return list(AVAILABLE_COMMANDS.keys())


def register_commands(tree, client):
    """
    Összes parancs regisztrálása

    Args:
        tree: Discord CommandTree példány
        client: Discord Client példány
    """
    # Parancsok regisztrálása és a visszatérési érték használata
    ping_cmd = register_ping_command(tree, client)
    print(f"✓ Parancs regisztrálva: {ping_cmd.name if ping_cmd else 'ismeretlen'}")

    # Debug: Ellenőrizzük, hogy tényleg benne van-e a tree-ben
    all_commands = tree.get_commands()
    print(f"🔍 Tree-ben lévő parancsok: {[cmd.name for cmd in all_commands]}")

    # További parancsok regisztrálása itt...