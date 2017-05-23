import numpy as np

def _region_from_args(args):
	if isinstance(args[0], tuple):
		return args[0]
	elif isinstance(args[0], dict):
		return _region_from_kwargs(args[0])
	else:
		return args

def _region_from_kwargs(kwargs):
	if "region" in kwargs:
		return kwargs["region"]

	x = -1 
	y = -1
	w = -1
	h = -1

	if "x" in kwargs:
		x = kwargs["x"]
	elif "left" in kwargs:
		x = kwargs["left"]

	if "y" in kwargs:
		y = kwargs["y"]
	elif "top" in kwargs:
		y = kwargs["top"]

	if "w" in kwargs:
		w = kwargs["w"]
	elif "width" in kwargs:
		w = kwargs["width"]
	elif "right" in kwargs:
		w = kwargs["right"] - x

	if "h" in kwargs:
		h = kwargs["h"]
	elif "height" in kwargs:
		h = kwargs["height"]
	elif "bottom" in kwargs:
		h = kwargs["bottom"] - y

	assert(x >= 0)
	assert(y >= 0)
	assert(w >= 0)
	assert(h >= 0)

	return (x, y, w, h)

class Region:
	def __init__(self, *args, **kwargs):
		if len(args) > 0:
			self.region = _region_from_args(args)
		else:
			self.region = _region_from_kwargs(kwargs)
		
		self.x = self.left = self.region[0]
		self.y = self.top = self.region[1]
		self.w = self.width = self.region[2]
		self.h = self.height = self.region[3]

		self.right = self.left + self.width
		self.bottom = self.top + self.height

	def within(self, x, y):
		return (
			x >= self.x and
			y >= self.y and
			x < self.x + self.width and
			y < self.y + self.height
		)

	def distance(self, other):
		return np.linalg.norm(other.position() - self.position())

	def position(self):
		return np.array([self.x, self.y])

	def __iter__(self):
		return iter(self.region)

	def __truediv__(self, other):
		return Region(
			int(self.x / other), 
			int(self.y / other),
			int(self.w / other),
			int(self.h / other)
		)
