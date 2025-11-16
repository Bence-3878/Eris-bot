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
from commands.nsfw import register_commands_nsfw, register_dm_commands_nsfw, get_available_commands_nsfw, get_dm_commands_nsfw


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
        register_commands_nsfw(tree, client, guild, enabled_commands)
    else:
        # Ha nincs guild, használd az alapértelmezett parancsokat
        register_commands_info(tree, client, guild, get_available_commands_info())
        register_commands_nsfw(tree, client, guild, get_available_commands_info())


def register_all_dm_commands(tree, client):
    """
    DM parancsok regisztrálása.

    Args:
        tree: A parancsfa objektum 
        client: A Discord kliens
    """
    register_dm_commands_info(tree, client)
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
    commands = get_available_commands_info() + get_available_commands_nsfw()
    return commands

def  get_all_dm_commands():
    commands = get_dm_commands_info() + get_dm_commands_nsfw()
    return commands