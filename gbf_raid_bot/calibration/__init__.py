from gbf_raid_bot.config import ConfigReader, ConfigGenerator
from gbf_raid_bot.utilities import Timer
from gbf_raid_bot import OFFSETS
from abc import ABC, abstractmethod
from mss import mss as MSS
from PIL import Image
from threading import Thread, Lock
from pymouse import PyMouseEvent

import time
import numpy as np
import pyautogui
import cv2

address_bar_offset = OFFSETS["game"][1]

class ImageCrop:
	def __init__(self):
		self.original = None
		self.image = None
		self.crop = False
		self.point = []
		self.threads = [
			# Thread(target=self.previewLoop),
			Thread(target=self.imageLoop)
		]
		self.lock = Lock()

		cv2.namedWindow("Image")
		cv2.setMouseCallback("Image", self.mouseListener)

	def setImage(self, image):
		self.original = image
		self.image = image

	def mouseListener(self, event, x, y, flags, param):
		if event == cv2.EVENT_LBUTTONDOWN and not self.crop:
			self.point = [(x, y)]

			self.image = self.original.copy()
			self.crop = True
		elif event == cv2.EVENT_MOUSEMOVE and self.crop:
			self.image = self.original.copy()
			cv2.rectangle(
				self.image, self.point[0], (x, y),
				(0, 255, 0),
				thickness=1
			)
		elif event == cv2.EVENT_LBUTTONUP and self.crop:
			self.point.append((x, y))
			self.image = self.original.copy()
			self.crop = False
			cv2.rectangle(
				self.image, self.point[0], self.point[1], 
				(255, 0, 255),
				thickness=1
			)

	def previewLoop(self):
		while self.running:
			if len(self.point) < 2: continue

			left, top = self.point[0]
			right, bottom = self.point[1]
			width = right - left
			height = bottom - top

			if width <= 0: continue
			if height <= 0: continue

			cv2.imshow("Preview", self.original[top:bottom, left:right])
			cv2.waitKey(1)

	def imageLoop(self):
		cv2.moveWindow("Image", 0, 0)
		while self.running:
			cv2.imshow("Image", self.image)
			key = cv2.waitKey(int(round(1000 / 30))) & 0xFF
			if key == 10: # ENTER key
				self.accepted = True
				break
			elif key == 27: # ESCAPE key
				break
		self.running = False

	def start(self):
		self.running = True
		self.accepted = False
		for thread in self.threads:
			thread.start()

	def stop(self):
		for thread in self.threads:
			thread.join()
		cv2.destroyAllWindows()

class Calibration(ABC):
	@abstractmethod
	def name(self):
		pass

	def calibrate(self):
		pass

	def regionFromMouse(self, region=None):
		print("Press ENTER to accept")
		print("Press ESCAPE to cancel")
		time.sleep(0.5)

		img = self.screenshot(region)
		ic = ImageCrop()
		ic.setImage(img)
		ic.start()
		ic.stop()

		if not ic.accepted:
			return (None, None)

		left, top = ic.point[0]
		right, bottom = ic.point[1]
		width = right - left
		height = bottom - top

		return ({
			"left": left, "top": top,
			"width": width, "height": height
		}, img[top:bottom, left:right])

	def screenshot(self, region=None):
		with MSS() as sct:
			if region is None:
				region = sct.enum_display_monitors()[0]
			sct.get_pixels(region)
			img = Image.frombytes("RGB", (sct.width, sct.height), sct.image)
			img = np.array(img)
			img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
		return img

	def showScreenshot(self, img):
		def task():
			cv2.imshow("Result", img)
			cv2.waitKey(0)

		Thread(target=task).start()
		respond = input("Result (Y/N): ").lower() == "y"
		cv2.destroyAllWindows()
		return respond

	def saveTrainingImage(self, name, img):
		filename = "training_sets/images/" + name + ".png"
		cv2.imwrite(filename, img)
		return filename

class ImageTraining(Calibration):
	def name(self):
		return "Image Training"

	def takeImage(self):
		window_region = ConfigReader("advanced_settings").get("image_processing.window.region")
		region, img = self.regionFromMouse(window_region)
		return img

	def calibrate(self):
		name = input("Name: ")
		filename = input("Filename (leave empty if same as name): ")
		if filename == "":
			filename = name

		img = self.takeImage()
		if img is None:
			input("Cancelled.")
			return

		filename = self.saveTrainingImage(filename, img)
		config = ConfigReader("training_data")
		data = config.get(name)

		if isinstance(data, list):
			data.append(filename)
			data = list(set(data))
		elif data is None:
			data = filename
		else:
			if data == filename:
				data = filename
			else:
				data = list(set([data, filename]))

		config.set(name, data).save()

class WindowRegion(Calibration):
	def name(self):
		return "Window Region"

	def takeRegion(self):
		region, img = self.regionFromMouse()
		return region

	def calibrate(self):
		region = self.takeRegion()
		if region is None:
			input("Cancelled.")
			return

		region["top"] -= address_bar_offset
		region["height"] += address_bar_offset
		(ConfigReader("advanced_settings")
			.set("image_processing.window.region", region)
			.save())

class ListenInterrupt(Exception):
	pass

class BattlePattern(Calibration, PyMouseEvent):
	def __init__(self):
		Calibration.__init__(self)
		self.settings = ConfigReader("advanced_settings")
		self.timer = Timer()
		self.region = None

	def name(self):
		return "Battle Pattern"

	def record(self, x, y):
		x -= self.region["left"]
		y -= self.region["top"]

		if x > self.region["width"] or y > self.region["height"]:
			return

		print("Move %d: %d, %d" % (len(self.positions), x, y))
		elapsed = int(round(self.timer.elapsed(1000)))
		self.positions.append((x, y, elapsed))

	def calibrate(self):
		pattern_name = input("Name: ")

		self.positions = []
		self.settings.load()
		self.timer.reset()

		self.region = self.settings.get("image_processing.window.region")
		listener = MouseListener(self.click)
		try:
			input("Press ENTER to start recording")
			listener.run()
		except ListenInterrupt:
			pass

		print("Recorded %d move(s)" % len(self.positions))
		print("Saving....")
		ConfigGenerator(pattern_name, self.positions, "patterns").save(indent=None)
		input("Saved.")

	def click(self, x, y, button, press):
		if button == 1 and press:
			self.record(x, y)
		elif button == 3 and press:
			raise ListenInterrupt
		
class MouseListener(PyMouseEvent):
	def __init__(self, callback):
		PyMouseEvent.__init__(self)
		self.callback = callback

	def click(self, x, y, button, press):
		self.callback(x, y, button, press)
