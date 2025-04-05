import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import reroll_shiny
import time

# Load the .env file to securely recieve the bot token
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
COOLDOWN_TIME = 30

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# dictionary keeping record of the last reroll time for each player
last_reroll_times = {}

def checkIsUserOnCooldown(last_reroll_times, player_name):
    player_name = player_name.lower()
    if player_name in last_reroll_times:
        time_since_last_reroll = time.time() - last_reroll_times[player_name]
        if time_since_last_reroll < COOLDOWN_TIME:
            return True
        
    return False
           

@bot.command()
async def reroll(ctx, *args):
    if len(args) != 2:
        await ctx.send(f"Usage: !reroll <username> <party slot number>")
        return
    
    player_name = args[0]

    if checkIsUserOnCooldown(last_reroll_times, player_name):
        time_since_last_reroll = time.time() - last_reroll_times[player_name]
        await ctx.send(f"{player_name} must wait {COOLDOWN_TIME - int(time_since_last_reroll)} more seconds until they reroll their pokemon again.")
        return
    
    # convert the party slot number to an int
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