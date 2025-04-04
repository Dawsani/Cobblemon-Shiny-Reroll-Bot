#!/bin/bash

SHINY_LIST_FILENAME="shiny_list.txt"

# make sure proper arguments were passed
if [ $# -ne 2 ] && [ $# -ne 3 ]; then
	echo "Usage: $0 (screen name) <player name> <slot number>"
	exit 1
fi

SCREEN_NAME="cobblemon-test"
if [ $# -eq 3 ]; then
	SCREEN_NAME=$1
	PLAYER_NAME=$2
	SLOT_NUMBER=$3
else
	PLAYER_NAME=$1
	SLOT_NUMBER=$2
fi

# get the number of lines in the file
NUM_SHINIES=$(wc -l < $SHINY_LIST_FILENAME)

# pick a random number from those
CHOICE=$((RANDOM % NUM_SHINIES + 1))
echo CHOICE=$CHOICE

# get the name of the pokemon
POKEMON_NAME=$(sed -n ${CHOICE}p $SHINY_LIST_FILENAME)
echo $POKEMON_NAME was chosen.

# set the players slot to that pokemon
screen -S $SCREEN_NAME -X stuff "pokeeditother ${PLAYER_NAME} ${SLOT_NUMBER} ${POKEMON_NAME}\n"
screen -S $SCREEN_NAME -X stuff "say ${PLAYER_NAME} got a ${POKEMON_NAME}!\n"
echo done
