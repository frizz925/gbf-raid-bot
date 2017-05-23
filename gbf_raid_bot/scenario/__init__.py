from gbf_raid_bot.scenario.scenario_action import ScenarioActionList, actionMouseMove
from gbf_raid_bot.capture.region import Region
from gbf_raid_bot.utilities import get_current_millis, merge_dict

import platform
import pyautogui

RETRY_SCENARIO = 0
NEXT_SCENARIO = 1
PREVIOUS_SCENARIO = 2
RESET_SCENARIO = 3
END_SCENARIO = 4

if platform.system() is "Windows":
	_scroll_modifier = 100
else:
	_scroll_modifier = 5

_scroll_amount = 1 * _scroll_modifier
_scroll_limit = 5 * _scroll_modifier

class ScenarioResult:
	def __init__(self, result: int, actions=None):
		self.result = result
		self.actionList = ScenarioActionList(actions)

class ScenarioContext:
	def __init__(self, manager, region, image, features):
		self.manager = manager
		self.region = region
		self.image = image
		self.features = features

		self.appContext = manager.appContext
		self.managerContext = manager.context
		self.elapsedTime = get_current_millis() - self.managerContext["startTime"]

class Scenario:
	def __init__(self, appContext):
		self.appContext = appContext
		self.logger = appContext.get("logger", fail=True)
		self.config = self.defaultConfig()

	def mergeConfig(self, config):
		self.config = merge_dict(self.config, config, deep=True)

	def defaultConfig(self):
		return {}

	def setUp(self, context):
		self.scroll = 0
		self.direction = -1 # -1: down, 1: up

	def tearDown(self, context):
		pass

	def cleanUp(self):
		pass

	def getScrollAmount(self):
		min_scroll = _scroll_limit * -1
		max_scroll = _scroll_limit * 1
		if self.scroll < min_scroll and self.direction < 0:
			self.direction = 1
		elif self.scroll > max_scroll and self.direction > 0:
			self.direction = -1
		return _scroll_amount * self.direction
        
	def getMousePosition(self, context):
		mouse = pyautogui.position()
		window = (context.region.x, context.region.y)
		return (mouse[0] - window[0], mouse[1] - window[1])

	def doScroll(self, context, region, amount):
		self.scroll += amount
		if not region.within(*self.getMousePosition(context)):
			actionMouseMove(context, region)
		pyautogui.scroll(amount, pause=0.75)
		#self.logger.debug("Scroll %d" % amount)

	def actionMouseScroll(self, context, region, args={}):
		self.doScroll(context, region, self.getScrollAmount())

	def actionMouseScrollReset(self, context, region, args={}):
		self.doScroll(context, region, -self.scroll)

	def getDefaultRegion(self, context):
		return Region(
			x=0,
			y=0,
			width=context.region.width,
			height=context.region.height
		)

	def retryScenario(self, actions=None):
		return ScenarioResult(RETRY_SCENARIO, actions)

	def nextScenario(self, actions=None):
		return ScenarioResult(NEXT_SCENARIO, actions)

	def prevScenario(self, actions=None):
		return ScenarioResult(PREVIOUS_SCENARIO, actions)

	def endScenario(self, actions=None):
		return ScenarioResult(END_SCENARIO, actions)

	def resetScenario(self, actions=None):
		return ScenarioResult(RESET_SCENARIO, actions)

	def handle(self, context: ScenarioContext) -> ScenarioResult:
		return self.nextScenario(self)

from gbf_raid_bot.scenario.scenario_manager import ScenarioManager
