from gbf_raid_bot.utilities import merge_dict

import json
import os

_config_dir = os.path.join(
	os.path.realpath(os.path.dirname(__file__)), 
	"../config"
)

class Config:
	def __init__(self, config):
		self.config = config

	def get(self, key: str, default=None):
		keys = key.split(".")
		value = self.config
		while len(keys) > 0 and value is not None:
			key = keys.pop(0)
			if key in value:
				value = value[key]
			else:
				value = None
		if isinstance(value, dict):
			value = Config(value)
		return value if value is not None else default

	def baseSet(self, parent, key, value):
		keys = key.split(".")
		while len(keys) > 1:
			key = keys.pop(0)
			child = None
			if key in parent:
				child = parent[key]
			if not isinstance(child, dict) :
				parent[key] = child = {}
			parent = child
		lastKey = keys.pop(0)
		parent[lastKey] = value
		return self

	def set(self, key, value):
		return self.baseSet(self.config, key, value)

	def toDict(self):
		return self.config

	def __getitem__(self, key):
		return self.get(key)

	def __setitem__(self, key, item):
		self.set(key, item)

	def __missing__(self, key):
		return key in self.config

	def __delitem__(self, key):
		del self.config[key]

	def __iter__(self):
		return self.config.__iter__()

class ConfigFile(Config):
	def __init__(self, name):
		self.name = name
		Config.__init__(self, self.load())

	def baseLoad(self, filename):
		if not self.baseFileExists(filename):
			return {}
		with open(filename) as f:
			config = json.load(f)
		return config

	def baseSave(self, filename, config, indent=4):
		with open(filename, mode="w") as f:
			json.dump(config, f, indent=indent, sort_keys=True)
		return self

	def baseFileExists(self, filename):
		return os.path.isfile(filename)

	def getFilename(self):
		return os.path.join(_config_dir, self.name + ".json")

	def load(self):
		self.config = self.baseLoad(self.getFilename())
		return self.config

	def save(self, indent=4):
		return self.baseSave(self.getFilename(), self.config, indent)

	def fileExists(self):
		return self.baseFileExists(self.getFilename())

class ConfigReader(ConfigFile):
	def __init__(self, name):
		self.base = {}
		self.derived = {}
		ConfigFile.__init__(self, name)

	def load(self):
		self.base = self.baseLoad(self.getFilename("base"))
		self.derived = self.baseLoad(self.getFilename())
		self.config = merge_dict({}, self.base, self.derived, deep=True)
		return self.config

	def save(self, indent=4):
		return self.baseSave(self.getFilename(), self.derived, indent)

	def getFilename(self, folder=None):
		if folder is None:
			return ConfigFile.getFilename(self)
		return os.path.join(_config_dir, folder, self.name + ".json")

	def set(self, key, value):
		self.baseSet(self.config, key, value)
		self.baseSet(self.derived, key, value)
		return self

class ConfigGenerator(ConfigFile):
	def __init__(self, name, config={}, folder="generated"):
		self.folder = folder
		ConfigFile.__init__(self, name)
		self.config = config

	def getFilename(self):
		return os.path.join(_config_dir, self.folder, self.name + ".json")
