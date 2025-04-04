import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import reroll_shiny
import time

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
COOLDOWN_TIME = 30

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

last_reroll_times = {}

@bot.command()
async def reroll(ctx, *args):
    if len(args) != 2:
        await ctx.send(f"Usage: !reroll <username> <party slot number>")
        return
    
    player_name = args[0]

    if player_name.lower() in last_reroll_times:
        time_since_last_reroll = time.time() - last_reroll_times[player_name.lower()]
        if time_since_last_reroll < COOLDOWN_TIME:
            await ctx.send(f"{player_name} must wait {COOLDOWN_TIME - int(time_since_last_reroll)} more seconds until they reroll their pokemon again.")
            return
    
    try:
        party_slot = int(args[1]) - 1
    except ValueError:
        await ctx.send("Party slot must be a number!")
        return

    exit_code, message = reroll_shiny.reroll_shiny(player_name, party_slot)
    if exit_code == 0:
        last_reroll_times[player_name.lower()] = time.time()
    await ctx.send(message)
    # make that player wait 30 seconds before rolling again

bot.run(TOKEN)