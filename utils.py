from random import randint, choices
import string
import storage
import re

def starts_with_designation(s):
  order_regex = re.compile(r'^\d\d\d\d,')
  return re.match(order_regex, s)

def is_drone(mention):
  return mention in storage.drones

def not_drone_and_target_drone(target_mention,user_mention):
  if is_drone(user_mention):
    return "Drones cannot use this command!"
  elif not is_drone(target_mention):
    return "That person is not a drone!"
  else:
    return True

def random_designation():  
  return f"#{randint(0,9999):0>4}"

def combine_texts(first_text,second_text):
  arr1 = first_text.split('\n')
  arr2 = second_text.split('\n')
  num_lines = max( len(arr1), len(arr2))
  return_arr = []
  for i in range(0,num_lines+1):
    arr3=[]
    for index, value in enumerate(arr1):
      if index < i:
        arr3.append(arr1[index] if index < len(arr1) else "")
      else:
        arr3.append(arr2[index] if index < len(arr2) else "")
    return_arr.append('\n'.join(arr3))

  return return_arr

async def get_hook(channel):
  hooks = await channel.webhooks()
  if len(hooks) == 0:
    webhook = await channel.create_webhook(name="BeepyBot Webhook")
  else:
    webhook = hooks[0]
  return webhook

key_len=36
def random_key():
  return ''.join(choices(string.ascii_letters, k=key_len))
