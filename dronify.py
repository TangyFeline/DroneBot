import disnake
import classes
import storage
import values
import utils
from random import choice

async def start_dronification(inter:disnake.MessageInteraction,person:disnake.Member, desig:str):
	flavor = choice(values.flavor_drone_start)
	flavor = flavor.replace('#',f'#{desig}')
	await inter.response.send_message(flavor)

	create_drone(desig, person.display_avatar.url, person,inter.guild.id)

def create_drone(designation:str,avatar:str,person:disnake.Member,guild_id:int):
	key = utils.random_key()
	new_drone = classes.Drone(designation, avatar, key, guild_id)	
	storage.drones[person.mention] = new_drone
	storage.drone_keys[key] = person.mention