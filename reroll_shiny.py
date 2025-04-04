import nbtlib
from nbtlib.tag import Int
from mcstatus import JavaServer
import sys
import numpy as np
import csv
import os
from tempfile import NamedTemporaryFile
import shutil
from mcrcon import MCRcon
import time

SERVER_IP = "localhost"
SERVER_PORT = 25566
RCON_PORT = 25576
RCON_PASSWORD = "boss"
SERVER_PATH = "/srv/minecraft/cobblemon-test-server"
WORLD_NAME = "test-world"
REROLL_HISTORY_FILE_PATH = "shiny-reroll-history.csv"
MINECRAFT_ITEM_COST_ID = "minecraft:diamond"
MINECRAFT_ITEM_COST_PER_REROLL = 64
REROLL_SHINY_BASH_SCRIPT = "./shiny_reroll.sh"
SCREEN_NAME = "cobblemon-test"

party_pokemon_file_path = os.path.join(SERVER_PATH, WORLD_NAME, "pokemon/playerpartystore")

# get the players id by name
def getPlayerUUID(server, player_name):
    status = server.status()
    players = status.players.sample

    if players == None:
        return None

    for player in players:
        if (player.name).lower() == player_name.lower():
            return player.id
        
    return None

def reroll_shiny(player_name, party_slot):

    if party_slot < 0 or party_slot > 5:
        return (1, f"Erm... there is no slot {party_slot+1} in Cobblemon... Party slot must be between 1 and 6.")

    # check if server is online
    server = JavaServer.lookup(f"{SERVER_IP}:{SERVER_PORT}")
    mcr = MCRcon(SERVER_IP, RCON_PASSWORD, RCON_PORT)
    try:
        mcr.connect()
    except:
        return(1, f"Sorry, I can't connect to the server through RCON right now. Tell @dawsani he's dumb and messed something up.")


    mcr.command("save-all flush")
        

    # TODO: Check if server is actually online

    # get uuid of player
    player_uuid = getPlayerUUID(server, player_name)
    if player_uuid is None:
        return(1, f"Player {player_name} is offline.")

    # make sure the pokemon is shiny
    # get the id of their pokemon
    # get the name of that pokemon for printing
    uuid_prefix = player_uuid[:2]
    party_full_path = os.path.join(party_pokemon_file_path, uuid_prefix, player_uuid + ".dat")
    nbt_file = nbtlib.load(party_full_path)

    # check if player has a pokemon in that slot
    slot_key = f"Slot{party_slot}"
    if slot_key not in nbt_file:
        return(1, f"{player_name} doesn't have a pokemon in slot {party_slot+1}")
    
    pokemon_id = nbt_file[slot_key]["UUID"]
    is_shiny = nbt_file[slot_key]["Shiny"]
    pokemon_name = nbt_file[slot_key]["Species"]
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
        return(1, f"{player_name}'s {pokemon_name} in slot {party_slot+1} is not shiny and cannot be rerolled.")

    # see how many times this pokemon has been rolled
    # file will have the following columns:
    # id, original trainer id, times rerolled, original form, form 2, form 3... etc.
    times_rerolled = 0
    with open(REROLL_HISTORY_FILE_PATH, newline='') as reroll_history_file:
        reader = csv.reader(reroll_history_file, delimiter=',', quotechar='\"')
        for row in reader:
            # see if it matches the id
            row_pokemon_id = row[0]
            if row_pokemon_id == pokemon_hex_id:
                # match found
                times_rerolled = int(row[2])
                break

    # check if the player has the required diamonds
    player_file = os.path.join(SERVER_PATH, WORLD_NAME, "playerdata", f"{player_uuid}.dat")
    player_data = nbtlib.load(player_file)

    if 'Inventory' not in player_data:
        print(f"No inventory found for {player_name}.")
        exit(1)

    total_available = 0
    diamond_slots = []
    for item in player_data['Inventory']:
        if 'id' not in item:
            continue
        if item['id'] == MINECRAFT_ITEM_COST_ID:
            total_available += item['count']
            diamond_slots.append(item)

    total_cost = ( times_rerolled + 1 ) * MINECRAFT_ITEM_COST_PER_REROLL
    if (total_available < total_cost):
        return(1, f"Broke! {player_name} does not have enough diamonds to reroll their {pokemon_name}. ({total_available} / {total_cost})")

    # reroll the pokemon with the bash script
    os.system(f"{REROLL_SHINY_BASH_SCRIPT} {player_name} {party_slot+1}")

    # remove the diamonds
    mcr.command(f"clear {player_name} {MINECRAFT_ITEM_COST_ID} {total_cost}")

    mcr.command("save-all flush")

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
                row[2] = int(row[2]) + 1
                # add this new pokemon to the pokemon it's been
                row.append(pokemon_name)
            writer.writerow(row)

        if (times_rerolled == 0):
            writer.writerow([pokemon_hex_id, player_uuid, 1, pokemon_name])

    shutil.move(tempfile.name, REROLL_HISTORY_FILE_PATH)

    mcr.disconnect()

    return(0, f"Rerolled {player_name}'s {pokemon_name} for {total_cost} diamonds!")

# for cmd usage
# args = sys.argv
# if len(args) != 3:
#     print(f"usage: {args[0]} <player name> <party slot>")
#     exit(1)

# player_name = args[1]
# party_slot = int(args[2]) - 1
# reroll_shiny(player_name, party_slot)