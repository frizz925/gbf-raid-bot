import time

OFFSETS = {
	"game": [0, 36]
}

REGIONS = {
	"viramate_characters": {
		"x": 0,
		"y": 445,
		"width": 480,
		"height": 243
	}
}

class AppContext:
	def __init__(self, context={}):
		self.context = context

	def get(self, key, default=None, fail=False):
		original = key
		keys = key.split(".")
		value = self.context
		while len(keys) > 0 and value is not None:
			key = keys.pop(0)
			if key in value:
				value = value[key]
			else:
				value = None
		if fail and value is None:
			raise ValueError("Can't find %s in AppContext" % original)
		return value if value is not None else default

	def __getitem__(self, key):
		return self.context[key]

	def __setitem__(self, key, item):
		self.context[key] = item

class Logger:
	def __init__(self, config):
		self.config = config

	def debug(self, text):
		self.printOutput("[Debug] " + text)

	def info(self, text):
		self.printOutput("[Info]  " + text)

	def error(self, text):
		self.printOutput("[Error] " + text)

	def printOutput(self, text):
		if self.config.get("enabled", True):
                    print("[%s] %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), text))
