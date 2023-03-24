from enum import IntEnum

class Mood(IntEnum):
	Normal   = 1
	Cheerful = 2

class Censor(IntEnum):
	Blank    = 1
	Scramble = 2
	Error    = 3
	Censor   = 4
	Replace  = 5