from gbf_raid_bot.capture.region import Region
from gbf_raid_bot.utilities import ROOT_DIR

import numpy as np
import os
import cv2

class TemplateImage:
	def __init__(self, filename, process_img=None, scale=1.0):
		path = os.path.join(ROOT_DIR, filename)
		if not os.path.isfile(path):
			raise FileNotFoundError(path)

		img = cv2.imread(path, cv2.IMREAD_COLOR)
		if process_img is not None:
			img = process_img(img)
		self.filename = filename
		self.image = img
		self.scale = scale
		self.width, self.height = img.shape[:2][::-1]

	def match(self, img, threshold=0.8):
		res = cv2.matchTemplate(img, self.image, cv2.TM_CCOEFF_NORMED)
		loc = np.where(res >= threshold)
		zipped = zip(*loc[::-1])

		result = []
		for pt in zipped:
			region = Region(
				x=int(pt[0] / self.scale), 
				y=int(pt[1] / self.scale),
				w=int(self.width / self.scale),
				h=int(self.height / self.scale)
			)
			result.append(region)

		return result

class Template:
	def __init__(self, filenames, name, process_img=None, scale=1.0):
		self.images = []
		self.name = name
		self.process_img = process_img
		self.scale = scale

		if isinstance(filenames, list):
			self.loadMultipleFiles(filenames)
		else:
			self.loadSingleFile(filenames)

	def loadMultipleFiles(self, filenames):
		for filename in filenames:
			self.loadSingleFile(filename)

	def loadSingleFile(self, filename):
		self.images.append(TemplateImage(filename, self.process_img, self.scale))

	def match(self, img, threshold=0.8):
		result = []
		for image in self.images:
			result.extend(image.match(img, threshold))
		return result

class TemplateList:
	def __init__(self, templates={}, process_img=None, scale=1.0):
		self.scale = scale
		self.process_img = process_img
		self.templates = {}
		for item in templates.items():
			self.put(*item)

	def get(self, name):
		return self.templates[name];

	def put(self, name, filenames):
		self.templates[name] = Template(filenames, name, self.process_img, self.scale)

	def match(self, img, threshold=0.8, features=None):
		result = {}
		if features is None:
			features = self.templates.keys()

		for name in features:
			template = self.templates[name]
			result[name] = template.match(img, threshold)

		return result

	def __getitem__(self, key):
		return self.templates[key]

	def __setitem__(self, key, item):
		self.templates[key] = item

	def __iter__(self):
		return self.templates.__iter__()

class TemplateMatcher:
	def __init__(self, templateList, image, threshold=0.8):
		self.templateList = templateList
		self.image = image
		self.threshold = threshold
		self.cache = {}

	def get(self, name):
		if name in self.cache:
			return self.cache[name]
		matches = self.templateList[name].match(self.image, self.threshold)
		self.cache[name] = matches
		return matches

	def some(self, names):
		result = {}
		for name in names:
			result[name] = self.get(name)
		return result

	def items(self):
		return self.cache.items()

	def __getitem__(self, key):
		return self.get(key)
