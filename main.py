import init
from init import client
from init import tree
import discord
from discord.ext import commands
import logging



if __name__ == '__main__':
    client.run(init.token, log_handler=init.handler, log_level=logging.DEBUG)