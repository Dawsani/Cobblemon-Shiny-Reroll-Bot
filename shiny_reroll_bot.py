import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import reroll_shiny

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.command()
async def reroll(ctx, *args):
    if len(args) != 2:
        await ctx.send(f"Usage: !reroll <username> <party slot number>")
        return
    
    player_name = args[0]
    try:
        party_slot = int(args[1]) - 1
    except ValueError:
        await ctx.send("Party slot must be a number!")
        return

    await ctx.send(reroll_shiny.reroll_shiny(player_name, party_slot))

bot.run(TOKEN)