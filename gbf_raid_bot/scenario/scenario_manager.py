import pyautogui
import random
import time

from gbf_raid_bot.scenario import Scenario, ScenarioContext, \
	NEXT_SCENARIO, PREVIOUS_SCENARIO, RESET_SCENARIO, \
	RETRY_SCENARIO, END_SCENARIO

from gbf_raid_bot.scenario.scenario_action import ScenarioActionList, ScenarioAction
from gbf_raid_bot.utilities import get_current_millis
from typing import List

class ScenarioManager:
	def __init__(self, appContext, scenarios):
		self.appContext = appContext
		self.logger = appContext.get("logger")
		self.scenarios = scenarios
		self.index = 0
		self.lastScenario = None
		self.running = True
		self.resetContext()

	def resetContext(self):
		self.context = {
			"retryCount": 0,
			"startTime": get_current_millis()
		}

	def handle(self, region, image, features) -> List[ScenarioAction]:
		if not self.running:
			return None

		context = ScenarioContext(self, region, image, features)
		scenario = self.getCurrentScenario()

		if scenario != self.lastScenario:
			if self.lastScenario is not None:
				self.lastScenario.tearDown(context)
			self.lastScenario = scenario
			scenario.setUp(context)

		result = scenario.handle(context)
		result.actionList.execute()
		self.handleScenarioResult(result.result)

		return result.actionList.actions

	def handleScenarioResult(self, result):
		if result is NEXT_SCENARIO:
			self.cycleScenario(1)
		elif result is PREVIOUS_SCENARIO:
			self.cycleScenario(-1)
		elif result is RESET_SCENARIO:
			self.cycleScenario(-self.index)
		elif result is RETRY_SCENARIO:
			self.context["retryCount"] += 1
		elif result is END_SCENARIO:
			self.running = False

	def getCurrentScenario(self) -> Scenario:
		return self.scenarios[self.index]

	def cycleScenario(self, increment=1):
		index = self.index + increment
		count = len(self.scenarios)
		if index >= count:
			self.index = 0
		elif index < 0:
			self.index = count - 1
		else:
			self.index = index
		self.resetContext()

		scenario = self.getCurrentScenario()
		self.logger.debug("Cycling to scenario %d: %s" % (self.index+1, type(scenario).__name__))
