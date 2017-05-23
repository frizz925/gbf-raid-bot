from gbf_raid_bot.scenario.scenario_action import ScenarioAction, actionDelay
from gbf_raid_bot.utilities import merge_dict
from gbf_raid_bot.scenario import Scenario
from scenario_sets import PartyScenario

_wait_feature_names = set(["btn_next", "btn_ok", "btn_cancel", "misc_emp-arrow"])
_friend_feature_names = set(["btn_cancel", "btn_close"])

class WaitForResultScenario(PartyScenario):
	def defaultConfig(self):
		return merge_dict(PartyScenario.defaultConfig(self), {
			"buttons": ["btn_event", "btn_quests", "btn_event-home"]
		})

	def featureNames(self):
		return self.config["buttons"]

	def excludeFeatureNames(self):
		return _wait_feature_names

	def handle(self, context):
		for name in self.featureNames():
			regions = context.features[name]
			if len(regions) > 0:
				return self.nextScenario()

		regions = None
		for name in self.excludeFeatureNames():
			regions = context.features[name]
			if len(regions) > 0:
				break
			else:
				regions = None

		if regions is None:
			return self.retryScenario()

		actions = [
			ScenarioAction(context, regions[0]),
			ScenarioAction(context, regions[0], actionDelay, {"seconds": 1.5})
		]

		return self.retryScenario(actions)

class BackToQuestScenario(PartyScenario):
	def defaultConfig(self):
		return merge_dict(PartyScenario.defaultConfig(self), {
			"buttons": ["btn_quests", "btn_event", "btn_event-home"]
		})

	def featureNames(self):
		return self.config["buttons"]

class FriendRequestScenario(WaitForResultScenario):
	def defaultConfig(self):
		return merge_dict(WaitForResultScenario.defaultConfig(self), {
			"buttons": ["btn_select", "btn_select-arrow"],
			"notifications": {
				"thumbnail_dimensional-halo": "Dimensional Halo"
			}
		})

	def featureNames(self):
		return self.config["buttons"]

	def excludeFeatureNames(self):
		return _friend_feature_names

	def handleNotification(self, name, message):
		pass

	def handle(self, context):
		for name, message in self.config["notifications"].items():
			regions = context.features[name]
			if len(regions) > 0:
				self.handleNotification(name, message)
		return WaitForResultScenario.handle(self, context)
