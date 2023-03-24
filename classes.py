import storage
from drone_enum import Mood, Censor
from random import choice
import re
import values

class Drone:
	def __init__(self,designation,display_picture_url,key,guild_id):
		self.my_guild = guild_id
		self.names = []
		self.name_regexes = []
		self.designation = designation
		self.model = "Drone"
		self.mood = Mood.Normal
		self.display_picture_url = display_picture_url
		self.muted = False
		self.visor = ""
		self.censor_method = Censor.Blank
		self.mantra = ""
		self.mantra_repetitions = -1
		self.key = key
		self.strict_mode = False
		self.forbidden_words = []		
		self.forbiddencensor = Censor.Blank
		self.word_regexes = []

	async def updated(self,kind,webhook):
		if kind == "identitytab":
			await self.speak(f"{self.designation} :: Update :: Identity.", webhook)
		elif kind == "namestab":
			await self.speak(f"{self.designation} :: Update :: Verbal restrictions.", webhook)
		elif kind == "speechtab":
			await self.speak(f"{self.designation} :: Update :: Speech.", webhook)
		elif kind == "mantrastab":
			pass # Drones already announce new mantras.
		else:
			raise Exception("Unknown kind of update pased to drone!")
	def get_configure_url(self,base_url):
		return f"{base_url}/{self.key}"

	def set_visor(self,s):
		if len(s)<=5:
			self.visor = s		

	def get_web_data(self):
		return {
			'avatar_url':self.display_picture_url,
			'names':self.names,
			'designation':self.designation,
			'model':self.model,
			'mood':self.mood,
			'visor':self.visor,
			'censor_method':self.censor_method,
			'strict_mode':self.strict_mode,			
			'forbidden_words':self.forbidden_words,
			'forbiddencensor':self.forbiddencensor
		}

	async def order(self,s,webhook):
		desig = s[:4]
		order = s.split(',')[1]
		if desig == self.designation:
			if 'mute' in order.lower():
				await self.mute(webhook)

	async def receive_mantra(self,mantra,count, webhook):
		self.mantra_repetions = -1
		await self.speak(f"{self.designation} :: New Mantra Received :: Reciting.",webhook)
		self.mantra = mantra
		self.mantra_repetitions = count

	def set_names(self,names):
		self.names = []
		self.name_regexes = []
		for name in names:
			name = re.compile(r'[^\w\s]').sub('',name)			
			self.names.append(name) #Remove non-word characters.
			name_reg = '+[\\s]*'.join(name)			
			self.name_regexes.append(re.compile(name_reg, re.IGNORECASE))

		print(self.names)
		print(self.name_regexes)

	def set_forbidden_words(self,words):
		self.forbidden_words = []
		self.words_regex = []		
		for word in words:
			word = re.compile(r'[^\w\s]').sub('',word)			
			self.forbidden_words.append(word)
			word_reg = '+[\\s]*'.join(word)
			self.word_regexes.append(re.compile(word_reg, re.IGNORECASE))

	async def speak(self,s,webhook):
		if self.muted:
			non_whitespace = re.compile(r'\w')
			s = non_whitespace.sub('\\_', s)
		else:
			#Enforce mantras.
			if self.mantra_repetitions > 0:
				if s == self.mantra or s == f"{self.designation} :: {self.mantra}":					
					pass
				else:
					s = f"{self.designation} :: Enforcing Mantra :: {self.mantra}"
				self.mantra_repetitions -=1

		if self.mood == Mood.Cheerful:
			#Tilde punctuation at the end of the sentence.
			end_punc = re.compile(r'[.!]$')
			end_question = re.compile(r'[?]$')
			s = end_punc.sub('~',s)
			s = end_question.sub('~?',s)
			if s[len(s)-1] != '~' and s[len(s)-1] != '?':
				s = s +"~"

			if ' :: ' in s:
				ind = s.index(' :: ')
				s = f"{s[:ind]} :: 𝅘𝅥𝅮 {s[ind+4:]} 𝅘𝅥𝅮"
			else:
				s = f"𝅘𝅥𝅮 {s} 𝅘𝅥𝅮"

		#Censor name.
		for name_regex in self.name_regexes:
			if not name_regex == "":				
				name = self.names[self.name_regexes.index(name_regex)]
				if self.censor_method == Censor.Blank:
					replace_with = '\\_'*len(name)
				elif self.censor_method == Censor.Scramble:
					random_scramble = ''.join([choice(values.alphabet) for letter in range(0,len(name))])
					replace_with = f'{random_scramble}'
				elif self.censor_method == Censor.Error:
					replace_with = choice(values.flavor_errors)				
				elif self.censor_method == Censor.Censor:
					replace_with = '█'*len(name)
				elif self.censor_method == Censor.Replace:
					full_sentence_name_regex = re.compile('(I am|I\'m)\\s+' + ('+[\\s]*'.join(name)),re.IGNORECASE)
					full_sentence_name_regex2 = re.compile('My name is\\s+' + ('+[\\s]*'.join(name)),re.IGNORECASE)
					s = full_sentence_name_regex.sub(f"`This drone's designation is #{self.designation}`", s)
					s = full_sentence_name_regex2.sub(f"`Drones do not have names. This drone's designation is #{self.designation}`", s)
					
					replace_with = f"`#{self.designation}`"

			s = name_regex.sub(replace_with, s)		

		# Censor other words.
		for word_regex in self.word_regexes:
			if not word_regex == "":
				word = self.forbidden_words[self.word_regexes.index(word_regex)]
				if self.forbiddencensor == Censor.Blank:
					replace_with = '\\_'*len(word)
				elif self.forbiddencensor == Censor.Scramble:
					random_scramble = ''.join([choice(values.alphabet) for letter in range(0,len(word))])
					replace_with = f'{random_scramble}'
				elif self.forbiddencensor == Censor.Error:
					replace_with = choice(values.flavor_errors)
				elif self.forbiddencensor == Censor.Censor:
					replace_with = '█'*len(word)
			s = word_regex.sub(replace_with, s)	
			
		if len(self.visor) > 0:
			s = f"{s} ` {self.visor} `"
			
		await webhook.send(s, username=f"{self.model} #{self.designation}", avatar_url=self.display_picture_url)

	async def mute(self,webhook):
  		confirm = f"{self.designation} :: Order confirmed. Muting vocal subsystems."
  		await self.speak(confirm,webhook)
  		self.muted = True