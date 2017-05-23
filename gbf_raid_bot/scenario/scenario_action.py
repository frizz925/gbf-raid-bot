from gbf_raid_bot.utilities import Timer

import math
import pyautogui
import random
import time
import numpy as np
import pyperclip

from threading import Thread

TWEEN = pyautogui.easeInOutCirc
SCREEN_SIZE = np.array(pyautogui.size())

_mouse_last_pos = (0, 0)
_mouse_last_region = None
_mouse_timer = Timer()
_mouse_same_distance = 10

def getTarget(context, region):
	half_width = int(math.floor(region.width / 2))
	half_height = int(math.floor(region.height / 2))

	if half_width > 0:
		quarter_width = int(math.floor(half_width / 2))
	else:
		quarter_width = 0
	if half_height > 0:
		quarter_height = int(math.floor(half_height / 2))
	else:
		quarter_height = 0

	if quarter_width > 0:
		random_width = random.randrange(-quarter_width, quarter_width)
	else:
		random_width = 0
	if quarter_height > 0:
		random_height = random.randrange(-quarter_height, quarter_height)
	else:
		random_height = 0

	return np.array([
		context.region.x + region.x + half_width + random_width,
		context.region.y + region.y + half_height + random_height
	])

def getSource():
	return np.array(pyautogui.position())

def getDuration(source, target, min_duration=0.3):
	distance = int(np.linalg.norm(target - source))
	if distance <= 0:
		return 0.0
	duration = float(random.randrange(distance) / SCREEN_SIZE[0] / SCREEN_SIZE[1] * 20)
	duration = max(min_duration, duration)
	return duration

def sameRegion(regionA, regionB):
	if regionA is None:
		return False
	if regionB is None:
		return False
	a = np.array([regionA.x, regionA.y])
	b = np.array([regionB.x, regionB.y])
	return np.linalg.norm(a - b) < _mouse_same_distance

def actionMouseMove(context, region, args={}):
	source = getSource()
	target = getTarget(context, region)
	duration = getDuration(source, target)

	pyautogui.moveTo(
		target[0],
		target[1],
		duration=duration,
		tween=TWEEN
	)

def actionMouseClick(context, region, args={}):
	global _mouse_last_region, _mouse_last_pos

	source = getSource()
	target = getTarget(context, region)
	duration = getDuration(source, target)

	# deny action if the mouse clicks in the same region under 3 seconds
	if sameRegion(_mouse_last_region, region) and _mouse_timer.before(3):
		return

	clicks = args["clicks"] if "clicks" in args else 1
	interval = args["interval"] if "interval" in args else 0.1
	button = args["button"] if "button" in args else "left"
	pause = float(random.randint(25, 75) / 100)

	pyautogui.click(
		target[0], target[1],
		clicks, interval, button,
		duration=duration,
		tween=TWEEN,
		pause=pause
	)
	_mouse_last_pos = target
	_mouse_last_region = region
	_mouse_timer.reset()

def actionClipboardPaste(context, region, args={}):
	pyperclip.paste()

def actionKeyboardHotkey(context, region, args={}):
	assert("hotkey" in args)
	pyautogui.hotkey(*args["hotkey"])

def actionKeyboardPress(context, region, args={}):
	assert("key" in args)
	pyautogui.press(args["key"])

def actionDelay(context, region, args={}):
	assert("seconds" in args)
	time.sleep(args["seconds"])

class ScenarioAction:
	def __init__(self, context, region, callback=actionMouseClick, args={}):
		self.context = context
		self.region = region
		self.callback = callback
		self.args = args

	def execute(self):
		self.callback(self.context, self.region, self.args)

class ScenarioActionList:
	def __init__(self, actions=None):
		if actions is None:
			actions = []
		elif not isinstance(actions, list):
			actions = [actions]
		self.actions = actions

	def push(self, context, region, callback):
		self.actions.append(ScenarioAction(context, region, callback))

	def execute(self):
		for action in self.actions:
			action.execute()
