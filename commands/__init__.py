# -*- coding: utf-8 -*-
# commands/__init__.py
# Parancsok regisztrációja

"""
Parancsok regisztrációját és konfigurációját kezelő modul.
A bot indulásakor ez a modul regisztrálja az összes elérhető parancsot.
"""

from commands.info import register_commands_for_guild_info, register_dm_commands_info, get_available_commands, get_dm_commands


def register_all_commands(tree, client, guild=None):
    """
    Az összes elérhető parancs regisztrálása.

    Args:
        tree: A parancsfa objektum
        client: A Discord kliens
        guild: Az opcionális guild objektum szerverspecifikus parancsokhoz
    """
    register_commands_for_guild_info(tree, client, guild)


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
    return get_available_commands()

def  get_all_dm_commands():

    return get_dm_commands()