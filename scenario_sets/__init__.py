from gbf_raid_bot.scenario import Scenario
from gbf_raid_bot.capture import Region
from gbf_raid_bot.scenario.scenario_action import ScenarioAction, actionMouseMove, actionMouseClick, actionDelay
from gbf_raid_bot.utilities import module_from_string, Timer
from numpy import Infinity

import random
import pyautogui
import time

_quest_feature_names = set(["thumbnail_angel-halo", "btn_select"])

class QuestScenario(Scenario):
	def defaultConfig(self):
		return {
			"thumbnail": "thumbnail_angel-halo",
			"quest_button": {
				"name": "btn_select",
				"location": "bottom right"
			}
		}

	def skipButtons(self):
		# sometimes showdowns guide pops up so we need to close it
		# in case of daily hard raids, the "quest can be played x times"
		return ["btn_close", "btn_ok"]

	def handleButton(self, context, name):
		regions = context.features[name]
		if len(regions) > 0:
			return self.retryScenario(ScenarioAction(context, regions[0]))
		return None

	def handle(self, context):
		for name in self.skipButtons():
			result = self.handleButton(context, name)
			if result is not None:
				return result
		return self.handleReal(context)

	def handleReal(self, context):
		regions = context.features[self.config["thumbnail"]]
		if len(regions) == 0:
			region = self.getDefaultRegion(context)
			return self.retryScenario(ScenarioAction(context, region, self.actionMouseScroll))
		thumbnail_region = regions[0]
		
		button_region = None
		button_distance = Infinity

		locations = self.config["quest_button"]["location"].split(" ")
		regions = context.features[self.config["quest_button"]["name"]]
		for region in regions:
			valid = False
			for location in locations:
				if location == "left" and thumbnail_region.x < region.x:
					valid = False
				elif location == "right" and thumbnail_region.x >= region.x:
					valid = False
				elif location == "top" and thumbnail_region.y < region.y:
					valid = False
				elif location == "bottom" and thumbnail_region.y >= region.y: 
					valid = False
				else:
					valid = True

				if not valid:
					break

			if not valid:
				continue

			distance = thumbnail_region.distance(region)
			if distance < button_distance:
				button_region = region
				button_distance = distance

		if button_region is None:
			region = self.getDefaultRegion(context)
			return self.retryScenario(ScenarioAction(context, region, self.actionMouseScroll))

		return self.nextScenario(ScenarioAction(context, button_region))

class DifficultyScenario(Scenario):
	def defaultConfig(self):
		return {
			"index": 2,
			"button": "btn_play"
		}

	def handle(self, context):
		index = self.config["index"]
		regions = context.features[self.config["button"]]
		if len(regions) < index + 1: 
			region = self.getDefaultRegion(context)
			return self.retryScenario(ScenarioAction(context, region, self.actionMouseScroll))
		
		return self.nextScenario(ScenarioAction(context, regions[index]))

class SupportScenario(QuestScenario):
	def defaultConfig(self):
		return {
			"timeout": 30000,
			"summon": {
				"preferred": None
			},
			"offset": {
				"left": -300,
				"top": -25,
				"right": -100,
				"bottom": 25
			}
		}

	def setUp(self, context):
		QuestScenario.setUp(self, context)
		self.hasSelectedElement = False
		self.timer = Timer()
		self.timeout = self.config["timeout"]
		self.element = self.appContext.get("settings.basic.battle.element", "dark")
		self.summons = self.appContext.get("settings.basic.battle.summons")
		if not isinstance(self.summons, list):
			self.summons = self.summons[self.element]
		if self.summons is None:
			self.summons = self.config["summon"]["preferred"]
		self.inPage = False

	def skipButtons(self):
		return ["btn_ok"]

	def handleReal(self, context):
		# refill AP button
		regions = context.features["btn_use"]
		if len(regions) > 0:
			self.logger.debug("Refill AP")
			actions = [
				ScenarioAction(context, regions[-1]),
				ScenarioAction(context, regions[-1], actionDelay, {"seconds": 1.5})
			]
			return self.retryScenario(actions)

		if not self.hasSelectedElement:
			# assume we're already in the selected element
			regions = context.features["icon_element-" + self.element]
			if len(regions) > 0:
				self.hasSelectedElement = True
				return self.retryScenario(ScenarioAction(context, regions[0]))
			else:
				return self.retryScenario()

		# check if we're actually in support page
		if not self.inPage:
			regions = context.features["btn_select-arrow"]
			if len(regions) > 0:
				self.inPage = True
			else:
				region = self.getDefaultRegion(context)
				return self.retryScenario(ScenarioAction(context, region, actionDelay, {"seconds": 1.5}))

		window_region = self.getDefaultRegion(context)

		# find the preferred summon if set. after some time and no summon found, choose randomly
		if self.summons is not None and self.timer.before(self.timeout, 1000):
			for summon in self.summons:
				regions = context.features[summon]
				if len(regions) > 0:
					return self.nextScenario(ScenarioAction(context, regions[0]))
			return self.retryScenario(ScenarioAction(context, window_region, self.actionMouseScroll))

		offset = self.config["offset"]
		regions = context.features["btn_select-arrow"]
		region = regions[random.randrange(0, len(regions))]
		region = Region(
			left=region.left + offset["left"],
			top=region.top + offset["top"],
			right=region.left + offset["right"],
			bottom=region.top + offset["bottom"]
		)
		
		return self.nextScenario(ScenarioAction(context, region))

class PartyScenario(Scenario):
	def defaultConfig(self):
		return {
			"timeout": 30000
		}

	def setUp(self, context):
		Scenario.setUp(self, context)
		self.timeout = self.config["timeout"]
		self.timer = Timer()

	def featureNamesPrevious(self):
		return []

	def featureNames(self):
		return ["btn_ok"]

	def featureNamesCheck(self):
		return ["btn_attack"]

	def handle(self, context):
		if self.timer.after(self.timeout, 1000):
			return self.prevScenario()
		for name in self.featureNamesPrevious():
			regions = context.features[name]
			if len(regions) > 0:
				return self.prevScenario()
		for name in self.featureNames():
			regions = context.features[name]
			if len(regions) > 0:
				return self.nextScenario(ScenarioAction(context, regions[0]))
		for name in self.featureNamesCheck():
			regions = context.features[name]
			if len(regions) > 0:
				return self.nextScenario()
		return self.retryScenario()
