import time
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def get_current_millis():
	return int(round(time.time() * 1000))

def merge_dict(*args, deep=False):
	target = args[0]
	sources = args[1:]
	for source in sources:
		for key, value in source.items():
			if deep and isinstance(value, dict):
				if key not in target or not isinstance(target[key], dict):
					target[key] = {}
				target[key] = merge_dict(target[key], value, deep=True)
			else:
				target[key] = value
	return target

def module_from_string(name: str):
	module_name, member_name = name.rsplit(".", 1)
	module = __import__(module_name, globals(), locals(), [member_name], 0)
	member = getattr(module, member_name)
	return member

class Timer:
	def __init__(self):
		self.reset()

	def reset(self):
		self.startTime = time.time()

	def elapsed(self, mult=1.0):
		return (time.time() - self.startTime) * mult

	def after(self, seconds, mult=1.0):
		return seconds <= self.elapsed(mult)

	def before(self, seconds, mult=1.0):
		return seconds > self.elapsed(mult)
