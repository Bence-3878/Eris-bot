import discord
from discord.ext import commands
import json
import asyncio
from init import client, tree




@tree.command(name="ping", description="Bot válaszideje")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong! Válaszidő: {} ms".format(round(client.latency * 1000)))
