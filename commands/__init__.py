# -*- coding: utf-8 -*-
# commands/__init__.py
# Parancsok regisztrációja

"""
Parancsok regisztrációját és konfigurációját kezelő modul.
A bot indulásakor ez a modul regisztrálja az összes elérhető parancsot.
"""

if __name__ == '__main__':
    exit(1)

from commands.info import register_commands_info, register_dm_commands_info, get_available_commands_info, get_dm_commands_info
from commands.settings import get_available_commands_settings, get_dm_commands_settings
from commands.send import register_commands_send, get_available_commands_send
from commands.moderacio import register_commands_mod, get_available_commands_mod


def register_all_commands(tree, client, guild=None, enabled_commands=None):
    """
    Az összes elérhető parancs regisztrálása.

    Args:
        tree: A parancsfa objektum
        client: A Discord kliens
        guild: Az opcionális guild objektum szerverspecifikus parancsokhoz
    """
    # Ha guild van megadva, szerezd be a guild beállításait
    if guild:
        from guild_settings.guild_settings import guild_settings
        enabled_commands = guild_settings.get_guild_commands(guild.id)
        register_commands_info(tree, client, guild, enabled_commands)
        register_commands_send(tree, client, guild, enabled_commands)
        register_commands_mod(tree, client, guild, enabled_commands)
    else:
        # Ha nincs guild, használd az alapértelmezett parancsokat
        register_commands_info(tree, client, guild, get_available_commands_info())
        register_commands_send(tree, client, guild, get_available_commands_send())
        register_commands_mod(tree, client, guild, get_available_commands_send())


def register_all_dm_commands(tree, client):
    """
    DM parancsok regisztrálása.

    Args:
        tree: A parancsfa objektum 
        client: A Discord kliens
    """
    register_dm_commands_info(tree, client)


def get_all_available_commands():
    """
    Retrieves and returns a list of all available commands for the system.

    This function compiles a list of commands that can be executed in the
    current system or application. The purpose is to provide an overview
    of the functionalities accessible through these commands.

    Returns:
        list: A list containing all available commands as string values.
    """
    info_commands = get_available_commands_info()
    send_commands = get_available_commands_send()
    mod_commands = get_available_commands_mod()
    command = info_commands + send_commands + mod_commands
    return command

def  get_all_dm_commands():
    return get_dm_commands_info()