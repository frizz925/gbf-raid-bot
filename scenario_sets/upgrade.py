from gbf_raid_bot.scenario.scenario_action import ScenarioAction, actionMouseClick
from gbf_raid_bot.scenario import Scenario

class BaseUpgradeScenario(Scenario):
	def nextOrRetry(self, context, names, successAction=None, retryAction=None):
		if not isinstance(names, list):
			names = [names]

		for name in names:
			regions = context.features[name]
			if len(regions) > 0:
				action = None
				if successAction is not None:
					action = ScenarioAction(context, regions[0], successAction)
				return self.nextScenario(action)

		region = self.getDefaultRegion(context)
		action = None
		if retryAction is not None:
			action = ScenarioAction(context, region, retryAction)
		return self.retryScenario(action)

class AutoSelectScenario(BaseUpgradeScenario):
	def handle(self, context):
		# upgrade by pressing Auto Select
		return self.nextOrRetry(
			context, "btn_auto-select", 
			actionMouseClick
		)

class UpgradeScenario(BaseUpgradeScenario):
	def handle(self, context):
		# running out of materials
		regions = context.features["btn_ok"]
		if len(regions) > 0:
			return self.endScenario(ScenarioAction(context, regions[0]))

		# upgrade by pressing Auto Select
		return self.nextOrRetry(
			context, "btn_upgrade", 
			actionMouseClick
		)

class UpgradeAgainScenario(BaseUpgradeScenario):
	def handle(self, context):
		# loop again by pressing Upgrade Again
		return self.nextOrRetry(
			context, "btn_upgrade-again",
			actionMouseClick, actionMouseClick
		)
