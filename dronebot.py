import disnake
from disnake.ext import commands
import os
from asyncio import sleep
import asyncio
from values import DRONE_INTRO_DELAY
from utils import random_key, random_designation, combine_texts, get_hook, not_drone_and_target_drone, starts_with_designation
from dronify import start_dronification
import classes
import storage
from drone_enum import Mood, Censor
import re
from quart import Quart, render_template, send_from_directory, request
import threading

TOKEN = os.environ['TOKEN']

server_url = "http://localhost:5000"

debug = True

intents = disnake.Intents.all()

async def find_drone_channel(guild_id):
  if guild_id in storage.drone_channels:
    return storage.drone_channels[guild_id]
  else:
    print("Couldn't find stored drone channel. Fetching..")
    guild = bot.get_guild(guild_id)
    channel = disnake.utils.get(guild.text_channels, name='drone-play-chat')
    if channel is None:
      print("Couldn't find drone play channel!")
    return channel

async def drone_intro(message_id,new_intro): 
  intro_channel = storage.intro_channels[storage.my_guild.id]
  msg = await intro_channel.fetch_message(message_id)
  old_intro = msg.content
  step_by_step = combine_texts(new_intro,old_intro)
  first = step_by_step.pop(0)  
  #Delete the original and repost it with the bot.
  await msg.delete()
  new_message = await intro_channel.send(f"{msg.author.mention}\n{first}")
  for para in step_by_step:
    await new_message.edit(para)
    await sleep(DRONE_INTRO_DELAY)

  #Finished! Now proxy it as the user.
  await new_message.delete()
  webhook = await get_hook(intro_channel)
  await webhook.send(para, username=msg.author.display_name, avatar_url=msg.author.display_avatar.url)

bot = commands.InteractionBot(
  command_prefix='',
  intents=intents
)

class ConfirmView(disnake.ui.View):
  def __init__(self):
    super().__init__(timeout=None)

  @disnake.ui.button(label="Finished!", style=disnake.ButtonStyle.success)
  async def a_button(
        self, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ):    
    await drone_intro(storage.claimed_by[inter.author.mention], storage.intro_saved[inter.author.mention])

@bot.event
async def on_ready():
  print("Started!")

@bot.event
async def on_message(message):
  if message.author.bot:
      return
  if isinstance(message.channel, disnake.DMChannel): #Is this a DM?
    if message.author.mention in storage.claimed_by: # Do they have a claimed message?
      embed = disnake.Embed()
      embed.description=message.content
      storage.intro_saved[message.author.mention] = message.content
      await message.author.send("This is what your edited introduction will look like. All good? If you'd like to change anything, just send another message.",embed=embed,view=ConfirmView())
    else:
      print(message.author)
      await message.author.send("You don't seem to be working on a message right now!")
  else: # Not a DM    
    webhook = await get_hook(message.channel)
    if message.author.mention in storage.drones: #A drone! Proxy time!
      drone = storage.drones[message.author.mention]
      content = message.content
      await message.delete()
      await drone.speak(content, webhook)
    else: #Non-drone, check if the drones need to respond to any orders.      
      if starts_with_designation(message.content):
        for d in storage.drones:
          drone = storage.drones[d]
          await drone.order(message.content,webhook)

@bot.slash_command(description="Configure a drone.")
async def configure(inter, target:disnake.Member):
  drone = storage.drones[target.mention]
  response = not_drone_and_target_drone(target.mention,inter.author.mention)
  if response == True:
    await inter.response.send_message(f"Go to the following URL to configure this drone: {drone.get_configure_url(server_url)}",ephemeral=True)
  else:
    await inter.response.send_message(response, ephemeral=True)

@bot.slash_command(description="Set a drone's censor method.")
async def set_censor(inter, target:disnake.Member, censor: Censor = commands.Param()):
  response = not_drone_and_target_drone(target.mention,inter.author.mention)
  if response == True:
    storage.drones[target.mention].censor_method = censor
    await inter.response.send_message("Done!", ephemeral=True)
  else:
    await inter.response.send_message(response, ephemeral=True)

@bot.slash_command(description="Set a drone's mood.")
async def set_mood(inter, target:disnake.Member, mood: Mood = commands.Param()):
  response = not_drone_and_target_drone(target.mention,inter.author.mention)  
  if response == True:
    storage.drones[target.mention].mood = mood
    await inter.response.send_message("Done!", ephemeral=True)
  else:
    await inter.response.send_message(response, ephemeral=True)    

@bot.slash_command(description="Assign a drone a mantra.")
async def assign_mantra(inter, target:disnake.Member, mantra: str, count: int):  
  response = not_drone_and_target_drone(target.mention,inter.author.mention)
  if response == True:
    webhook = await get_hook(inter.channel)
    await storage.drones[target.mention].receive_mantra(mantra, count,webhook)
  else:
    await inter.response.send_message(response, ephemeral=True) 

@bot.slash_command(description="Set a drone's visor display.")
async def set_visor(inter, target:disnake.Member, visor: str):
  response = not_drone_and_target_drone(target.mention,inter.author.mention)
  if response == True:
    storage.drones[target.mention].visor = visor
  else:
    await inter.response.send_message(response, ephemeral=True)     

@bot.slash_command(description="Set a list of names to be filtered out when said by this drone. Seperate with a comma.")
async def set_drone_name(inter, target:disnake.Member, names: str):
  response = not_drone_and_target_drone(target.mention,inter.author.mention)
  if response == True:
    names = names.replace(" ",'').split(",")
    storage.drones[target.mention].set_names(names)
  else:
    await inter.response.send_message(response, ephemeral=True) 
  
@bot.slash_command(description="Dronify a person!")
async def dronify(inter,target:disnake.Member, designation:str):  
  if inter.author.mention in storage.drones:
    await inter.response.send_message(f"You can't dronify people, silly drone.", ephemeral=True)
  elif target.mention in storage.drones:
    inter.response.send_message(f"{target.mention} is already a drone!", ephemeral=True)
  else:
    await start_dronification(inter, target,designation)

@bot.message_command(description="Dronify an intro!")
async def DronifyIntro(inter, message):
  if storage.my_guild == -1:
    storage.my_guild = inter.guild    

  if inter.channel.name != 'drone-introduction':
    await inter.response.send_message("Please use this command in the #introduction channel!", ephemeral=True)
  elif message.author.bot:
    await inter.response.send_message("You can only use this command on messages sent by non-bots.", ephemeral=True)
  elif inter.author.name == message.author.name and not debug:
    await inter.response.send_message("You can't dronify yourself!", ephemeral=True)
  elif message.id in storage.claimed:
    if not storage.claimed[message.id] == inter.author.mention:
      await inter.response.send_message("This message has already been claimed by someone else!", ephemeral=True)
    else:
      await inter.response.send_message("You have already claimed this message! See your DMs to proceed.", ephemeral=True)
  elif message.author in storage.claimed.values():
    await inter.response.send_message("You may only claim one introduction at a time! Release your prior introduction first.", ephemeral=True)
  else:
    #Set this server's introduction channel if we don't have it cached already.
    if not inter.guild.id in storage.intro_channels:
      storage.intro_channels[inter.guild.id] = inter.channel

    storage.claimed[message.id] = inter.author.mention
    storage.claimed_by[inter.author.mention] = message.id
    await message.add_reaction('⏳')
    await inter.response.send_message("This introduction has been claimed by you! Please see your DMs.", ephemeral=True)

    embed = disnake.Embed()
    embed.description=message.content

    await inter.author.send("Here is the introduction you are editing!", embed=embed)
    desig = random_designation()
    msg = values.DRONE_INTRO_MESSAGE.replace('%',random_designation())
    await inter.author.send(msg)

app = Quart(__name__)

@app.route("/<path:key>")
async def control_panel(key):
  if key in storage.drone_keys:
    drone = storage.drones[storage.drone_keys[key]]
    print(drone.get_web_data())
    return await render_template('control.html',key=key,data=drone.get_web_data())
  else:
    return await render_template('404.html')

@app.route('/style.css')
async def return_style():
    return await send_from_directory('static', 'style.css')     

@app.route('/reset.css')
async def return_reset_style():
    return await send_from_directory('static', 'reset.css')    

@app.route('/script.js')
async def return_script():
    return await send_from_directory('static', 'script.js')

async def handle_set_values(key, typ,data):
  drone_id = storage.drone_keys[key]
  drone = storage.drones[drone_id]
  guild_id = drone.my_guild
  channel = asyncio.run_coroutine_threadsafe(find_drone_channel(guild_id), bot.loop)  
  channel = channel.result()
  webhook = asyncio.run_coroutine_threadsafe(get_hook(channel), bot.loop)  
  webhook = webhook.result()

  if (typ == "identitytab"):
    drone.model = data['model']
    drone.designation = data['designation']
    drone.set_visor(data['visor'])
    drone.mood = Mood[data['mood']]
  elif (typ == "namestab"):
    drone.set_names(data['names'].split('\n'))    
    print("Setting censor to",data['names_censor'])
    drone.censor_method = Censor[data['names_censor']]
    drone.strict_mode = data['strictmode']
  elif (typ == "speechtab"):
    drone.set_forbidden_words(data['forbidden_words'].split('\n'))    
    drone.forbiddencensor = Censor[data['forbiddencensor']]
  elif (typ == "mantrastab"):
    asyncio.run_coroutine_threadsafe(drone.receive_mantra(data['mantra'],int(data['mantra_count']),webhook), bot.loop)
  else:
    print("Unknown type: " + typ)

  asyncio.run_coroutine_threadsafe(drone.updated(typ,webhook), bot.loop)  

@app.route('/set_values', methods=['POST'])
async def set_values():
  data = await request.get_json()
  await handle_set_values(data['key'], data['type'], data)
  return 'okay'

async def run_server():
  await quart.serving.run(app, port=5000)

async def run_bot():
  bot.run(TOKEN)

async def run():
    server_task = asyncio.create_task(app.run_task(port=5000))
    bot_task = asyncio.create_task(asyncio.to_thread(bot.run, TOKEN))
    await asyncio.gather(server_task, bot_task)

asyncio.run(run())