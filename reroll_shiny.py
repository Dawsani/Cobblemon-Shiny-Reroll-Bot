import nbtlib
from mcstatus import JavaServer
import sys
import numpy as np
import csv
import os
from tempfile import NamedTemporaryFile
import shutil

SERVER_IP = "localhost"
PARTY_POKEMON_FILE_PATH = "/srv/minecraft/cobblemon/world/pokemon/playerpartystore"
# inside the pokemon file path there is a directory for each 2 letters of uuids
REROLL_HISTORY_FILE_PATH = "shiny-reroll-history.csv"
WORLD_FILE_PATH = "/srv/minecraft/cobblemon/world"
MINECRAFT_ITEM_COST_ID = "minecraft:diamond"
MINECRAFT_ITEM_COST_PER_REROLL = 64
REROLL_SHINY_BASH_SCRIPT = "./srv/minecraft/cobblemon/scripts/shiny_reroll.sh"

args = sys.argv
if len(args) != 3:
    print(f"usage: {args[0]} <player name> <party slot>")
    exit(1)

player_name = args[1]
party_slot = int(args[2]) - 1
if party_slot < 0 or party_slot > 5:
    print(f"Party slot must be between 1 and 6. (Not {party_slot+1})")
    exit(1)

def listOnlinePlayers(server_ip):
    server = JavaServer.lookup(server_ip)
    status = server.status()
    players = status.players.sample

    for player in players:
        print(f"Username: {player.name}, UUID: {player.id}")

# get the players id by name
def getPlayerUUID(server, player_name):
    status = server.status()
    players = status.players.sample

    for player in players:
        if (player.name).lower() == player_name.lower():
            return player.id
        
    return None




# check if server is online
server = JavaServer.lookup(SERVER_IP)

# get uuid of player
player_uuid = getPlayerUUID(server, player_name)
if player_uuid is None:
    print(f"Player {player_name} is offline.")
    exit(1)

# make sure the pokemon is shiny
# get the id of their pokemon
# get the name of that pokemon for printing
uuid_prefix = player_uuid[:2]
party_full_path = PARTY_POKEMON_FILE_PATH + '/' + uuid_prefix + "/" + player_uuid + ".dat"
nbt_file = nbtlib.load(party_full_path)

pokemon_id = nbt_file[f"Slot{party_slot}"]["UUID"]
is_shiny = nbt_file[f"Slot{party_slot}"]["Shiny"]
pokemon_name = nbt_file[f"Slot{party_slot}"]["Species"]
pokemon_name = pokemon_name.split(':')[1]

pokemon_id = pokemon_id.astype(np.uint16)
pokemon_hex_id = ""
for i in range(len(pokemon_id)):
    id_segment = pokemon_id[i]
    pokemon_hex_id += hex(id_segment)[2:]
    if ( i + 1) < len(pokemon_id):
        pokemon_hex_id += '-'

if is_shiny == 1:
    is_shiny = True
else:
    is_shiny = False

if is_shiny is False:
    print(f"{player_name}'s {pokemon_name} in slot {party_slot+1} is not shiny and cannot be rerolled.")
    exit(1)


# see how many times this pokemon has been rolled
# file will have the following columns:
# id, original trainer, times rerolled, original form, form 2, form 3... etc.
times_rerolled = 0
with open(REROLL_HISTORY_FILE_PATH, newline='') as reroll_history_file:
    reader = csv.reader(reroll_history_file, delimiter=',', quotechar='\"')
    for row in reader:
        # see if it matches the id
        row_pokemon_id = row[0]
        if row_pokemon_id == pokemon_hex_id:
            # match found
            times_rerolled = row[2]
            break

# calculate how many diamonds the reroll would cost
diamond_cost = times_rerolled * 64

# check if the player has the required diamonds
player_file = os.path.join(WORLD_FILE_PATH, "playerdata", f"{player_uuid}.dat")
player_data = nbtlib.load(player_file)

if 'Inventory' not in player_data:
    print(f"No inventory found for {player_name}.")
    exit(1)

total_available = 0
diamond_slots = []
for item in player_data['Inventory']:
    if item['id'] == MINECRAFT_ITEM_COST_ID:
        total_available += item['Count']
        diamond_slots.append(item)

total_cost = ( times_rerolled + 1 ) * MINECRAFT_ITEM_COST_PER_REROLL
if (total_available < total_cost):
    print(f"{player_name} does not have enough diamonds to reroll their {pokemon_name}. ({total_available} / {total_cost})")
    exit(1)

# reroll the pokemon with the bash script
os.system(f"{REROLL_SHINY_BASH_SCRIPT} {player_name} {party_slot+1}")

# remove the diamonds
remaining_cost = total_cost
for item in diamond_slots:
    if total_cost <= 0:
        break

    diamonds_in_slot = item['count']
    remove = min(diamonds_in_slot, remaining_cost)
    remaining_cost -= remove
    item['count'] -= remove

player_data.save()

# add the reroll to the records
tempfile = NamedTemporaryFile("w+t", newline='', delete=False)
with open(REROLL_HISTORY_FILE_PATH, newline='') as reroll_history_file:
    reader = csv.reader(reroll_history_file, delimiter=',', quotechar='"')
    writer = csv.writer(tempfile, delimiter=',', quotechar='"')
    for row in reader:
        # see if it matches the id
        row_pokemon_id = row[0]
        if row_pokemon_id == pokemon_hex_id:
            # increment the number of times it's been rerolled
            row[2] += 1
            # add this new pokemon to the pokemon it's been
            row.append(pokemon_name)
        writer.writerow(row)
shutil.move(tempfile.name, REROLL_HISTORY_FILE_PATH)


print(f"Rerolled {player_name}'s {pokemon_name}.")
