from gbf_raid_bot.scenario.scenario_action import ScenarioAction, actionKeyboardPress, actionDelay
from gbf_raid_bot.scenario import Scenario
from gbf_raid_bot.twitter import TwitterClient
from gbf_raid_bot.config import ConfigReader
from gbf_raid_bot.utilities import Timer
from scenario_sets.result import WaitForResultScenario as BaseResultScenario
from threading import Thread, Lock

import pyperclip
import random
import time

class TweetScenario(Scenario):
	def __init__(self, appContext):
		Scenario.__init__(self, appContext)
		self.credentials = ConfigReader("twitter_settings")
		self.client = TwitterClient(self.credentials.toDict())
		self.raid = None
		self.lock = Lock()
		self.running = False

	def defaultConfig(self):
		return {
			"delay": {
				"amount": 1500,
				"variance": 1500
			},
			"twitter": {
				"retry": {
					"delay": 5000
				}
			}
		}

	def addToQueue(self, code, boss):
		self.raid = (code, boss, time.time())
		if self.lock.locked():
			self.lock.release()

	def setUp(self, context):
		Scenario.setUp(self, context)
		if self.running:
			return
		def task(query):
			while self.running:
				try:
					self.client.stream(self.addToQueue, query)
				except Exception as e:
					if isinstance(e, KeyboardInterrupt):
						self.running = False
						break
					else:
						self.logger.error("Stream crashed: %s" % str(e))
						time.sleep(self.config["twitter"]["retry"]["delay"] / 1000)
						continue

		self.running = True
		query = self.appContext.get("settings.basic.leech.query")
		Thread(target=task, args=(query,)).start()

	def handle(self, context):
		delay_amount = self.config["delay"]["amount"]
		delay_variance = self.config["delay"]["variance"]
		delay_time = delay_amount + random.randint(0, delay_variance)
		time.sleep(delay_time / 1000)

		regions = context.features["thumbnail_viramate"]
		if len(regions) == 0:
			return self.retryScenario()
		viramate_region = regions[0]
		actions = [
			ScenarioAction(context, viramate_region),
			ScenarioAction(context, viramate_region, actionDelay, {"seconds": 0.5})
		]

		if self.raid is None:
			if not self.lock.locked():
				self.lock.acquire()
			self.lock.acquire()
		code, boss, time_from = self.raid
		self.raid = None
		elapsed = int(round(time.time() - time_from))
		self.logger.info("Raidfinder: %s (%s) (%s second(s) ago)" % (code, boss, elapsed))
		pyperclip.copy(code)

		action = ScenarioAction(context, viramate_region, actionKeyboardPress, {"key": "enter"})
		actions.append(action)

		return self.nextScenario(actions)

class CheckRaidScenario(Scenario):
	def __init__(self, appContext):
		Scenario.__init__(self, appContext)
		self.timer = Timer()
		self.callbackMap = {
			"next": self.nextScenario,
			"previous": self.prevScenario,
			"reset": self.resetScenario,
			"end": self.endScenario
		}
		self.delay = 0
		self.delayFinished = False

	def defaultConfig(self):
		return {
			"delay": 3000,
			"timeout": {
				"amount": 15000,
				"action": "reset"
			},
			# what features to check during this secnario
			"check": {
				"next": ["btn_select-arrow", "btn_attack", "thumbnail_loading", "thumbnail_ready"],
				"previous": [],
				"reset": ["btn_ok"],
				"end": []
			},
			"scroll": False
		}

	def setUp(self, context):
		Scenario.setUp(self, context)
		self.delay = self.config["delay"]
		self.timeout = self.config["timeout"]
		self.delayFinished = False
		self.timer.reset()

	def doCheck(self, context, key, callback):
		for value in self.config["check"][key]:
			if isinstance(value, list):
				name, min_length = value
			else:
				name = value
				min_length = 1
			regions = context.features[name]
			if len(regions) >= min_length:
				action = ScenarioAction(context, regions[0], self.actionMouseScrollReset)
				return callback(action)
		return None

	def handle(self, context):
		# delay before start checking
		if not self.delayFinished:
			if self.delay > 0:
				if self.timer.after(self.delay, 1000):
					self.delayFinished = True
					self.timer.reset()
				else:
					return self.retryScenario()
			else:
				self.delayFinished = True

		# check for features
		for key in self.config["check"]:
			callback = self.callbackMap[key]
			result = self.doCheck(context, key, callback)
			if result is not None:
				return result

		# timeout after preset amount of time
		if self.timer.after(self.timeout["amount"], 1000):
			self.timer.reset()
			callback = self.callbackMap[self.timeout["action"]]
			return callback()

		region = self.getDefaultRegion(context)
		action = None
		if self.config["scroll"]:
			action = ScenarioAction(context, region, self.actionMouseScroll)
		return self.retryScenario(action)

class WaitForResultScenario(BaseResultScenario):
	def __init__(self, appContext):
		BaseResultScenario.__init__(self, appContext)
		self.timer = Timer()

	def setUp(self, context):
		BaseResultScenario.setUp(self, context)
		self.timeoutSeconds = self.appContext.get("settings.basic.leech.timeout_seconds", -1)
		self.timer.reset()

	def handle(self, context):
		# timeout in seconds
		if self.timeoutSeconds > 0 and self.timer.after(self.timeoutSeconds):
			return self.nextScenario()
		else:
			return BaseResultScenario.handle(self, context)
