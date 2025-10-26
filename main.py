# -*- coding: utf-8 -*-
# 2.0.0
# main.py

import logging
from bot import bot_instance

if __name__ == '__main__':
    """
    A projekt belépési pontja.
    Csak elindítja a botot, minden funkció külön modulokban van.
    """
    bot_instance.run()