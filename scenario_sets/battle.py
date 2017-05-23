from gbf_raid_bot.scenario.scenario_action import ScenarioAction, actionDelay
from gbf_raid_bot.scenario import Scenario
from gbf_raid_bot.utilities import module_from_string
from gbf_raid_bot.config import ConfigGenerator
from gbf_raid_bot.capture import Region
from gbf_raid_bot import OFFSETS, REGIONS
from scenario_sets import PartyScenario

address_bar_offset = OFFSETS["game"][1]
characters_regions = REGIONS["viramate_characters"]
characters_offset = address_bar_offset + characters_regions["y"] + characters_regions["height"]

class AttackScenario(PartyScenario):
	def featureNames(self):
		return ["btn_attack"]

	def featureNamesCheck(self):
		return []

class AutoScenario(PartyScenario):
	def featureNamesPrevious(self):
		return ["btn_attack"]

	def featureNames(self):
		return ["btn_auto"]

	def featureNamesCheck(self):
		return []

class PlayScenario(Scenario):
	def defaultConfig(self):
		return {
			"battle_count": 1
		}

	def setUp(self, context):
		Scenario.setUp(self, context)
		self.turn = 0
		self.commandIndex = 0
		self.commandHandlers = self.loadCommands()
		self.pendingCommand = 0
		self.lastCommand = None
		self.hasStarted = False
		self.battleCount = self.config["battle_count"]
		self.battlePassed = 0

		pattern_name = self.appContext.get("settings.basic.battle.pattern", "default")
		self.patterns = self.appContext.get("settings.pattern." + pattern_name, [])

	def loadCommands(self):
		result = {}
		commands = self.appContext.get("settings.advanced.battle.commands", {})
		for command, module in commands.items():
			result[command] = module_from_string("battle_commands." + module)
		return result

	def commandToAction(self, context, command):
		name, args = command.split(":", 2)
		args = args.split(",")
		handler = self.commandHandlers[name]
		return handler(self, context, *args)

	def nextButtons(self):
		return ["btn_next", "btn_ok"]

	def handle(self, context):
		# only check when the battle has started
		if self.hasStarted:
			# battle finished, click Next or OK button
			for name in self.nextButtons():
				regions = context.features[name]
				if len(regions) > 0:
					self.battlePassed += 1
					if self.battlePassed >= self.battleCount:
						return self.nextScenario()
					else:
						return self.retryScenario(ScenarioAction(context, regions[0]))

		# sometimes Vyrn says stuff
		regions = context.features["icon_dialog"]
		if len(regions) > 0:
			return self.retryScenario(ScenarioAction(context, regions[0]))

		# check if we have the attack button
		regions = context.features["btn_attack"]
		if len(regions) == 0:
			return self.retryScenario()

		# saw the attack button, flag the battle has started
		if not self.hasStarted:
			self.hasStarted = True

		# there's a pending command, don't continue
		if self.pendingCommand > 0 and self.lastCommand is not None:
			action = self.commandToAction(context, self.lastCommand)
			return self.retryScenario(action)

		attack_region = regions[0]
		attack = False

		action = None
		if self.turn < len(self.patterns):
			pattern = self.patterns[self.turn]
			if self.commandIndex < len(pattern):
				self.lastCommand = command = pattern[self.commandIndex]
				action = self.commandToAction(context, command)
			else:
				# end of patterns, attack
				attack = True
			self.commandIndex += 1
		else:
			# run out of patterns, attack
			attack = True

		if attack:
			action = ScenarioAction(context, attack_region)
			self.turn += 1
			self.commandIndex = 0

		return self.retryScenario(action)

class PlayRecordedScenario(Scenario):
	def defaultConfig(self):
		return {
			"pattern_recorded": None,
			"buttons": {
				"click": ["btn_next", "btn_ok", "btn_dialog"],
				"check": ["btn_attack"],
				"next": ["btn_quests", "btn_event", "btn_event-home", "misc_emp-arrow"]
			}
		}

	def setUp(self, context):
		Scenario.setUp(self, context)
		self.caHold = self.appContext.get("settings.basic.battle.ca_hold", True)
		self.viramate = self.appContext.get("settings.basic.battle.viramate", True)
		self.autoAttack = self.appContext.get("settings.basic.battle.auto_attack", True)

		self.sync = self.appContext.get("settings.basic.battle.pattern_recorded.sync", False)
		self.repeat = self.appContext.get("settings.basic.battle.pattern_recorded.repeat", False)
		self.recordName = self.appContext.get("settings.basic.battle.pattern_recorded.name", None)
		if self.recordName is None:
			self.recordName = self.config["pattern_recorded"]
		if self.recordName is None:
			raise Exception("battle.pattern_recorded.name is not specified!")
		self.pattern = ConfigGenerator(self.recordName, folder="patterns").load()
		self.patternIndex = 0
		self.turn = 0
		self.logger.debug("Loaded pattern '%s' with %d move(s)" % (self.recordName, len(self.pattern)))

	def switchChargeAttack(self, context, caFrom, caTo):
		regions = context.features[caFrom]
		if len(regions) > 0:
			return self.retryScenario(ScenarioAction(context, regions[0]))
		regions = context.features[caTo]
		if len(regions) == 0:
			return self.retryScenario()
		return None

	def checkChargeAttack(self, context):
		if self.caHold:
			return self.switchChargeAttack(context, "btn_ca-auto", "btn_ca-hold")
		else:
			return self.switchChargeAttack(context, "btn_ca-hold", "btn_ca-auto")

	def handle(self, context):
		for name in self.config["buttons"]["next"]:
			regions = context.features[name]
			if len(regions) > 0:
				return self.nextScenario()

		for name in self.config["buttons"]["click"]:
			regions = context.features[name]
			if len(regions) > 0:
				actions = [
					ScenarioAction(context, regions[0]),
					ScenarioAction(context, regions[0], actionDelay, {"seconds": 1.5})
				]
				return self.retryScenario(actions)

		regions = []
		for name in self.config["buttons"]["check"]:
			regions = context.features["btn_attack"]
			if len(regions) > 0:
				break

		if len(regions) == 0:
			return self.retryScenario()
		attack_region = regions[0]

		if self.viramate and self.turn < 1:
			# if there's attack button, there should be auto/hold button
			ca_region = None
			for name in ["btn_ca-auto", "btn_ca-hold"]:
				regions = context.features[name]
				if len(regions) > 0:
					ca_region = regions[0]
					break

			# check if the CA button is below the characters offset
			if ca_region is None or ca_region.y < characters_offset:
				return self.retryScenario()

		if self.patternIndex == 0:
			result = self.checkChargeAttack(context)
			if result is not None:
				return result

		if self.patternIndex >= len(self.pattern):
			# run out of recorded pattern. just spam attack button
			if self.repeat:
				self.patternIndex = 0
			elif self.autoAttack:
				return self.retryScenario(ScenarioAction(context, attack_region))
			else:
				return self.nextScenario()

		attack = False
		actions = []
		lastPattern = []
		for pattern in self.pattern[self.patternIndex:]:
			x, y, timestamp = pattern
			region = Region(x, y, 1, 1)
			if self.sync and len(lastPattern) >= 3:
				delay = float((timestamp - lastPattern[2]) / 1000)
				actions.append(ScenarioAction(context, region, actionDelay, {"seconds": delay}))

			lastPattern = pattern
			actions.append(ScenarioAction(context, region))
			if attack_region.within(x, y):
				attack = True
				break


		self.patternIndex += len(actions)
		self.turn += 1
		self.logger.debug("Executing %d move(s) at turn %d" % (len(actions), self.turn))

		if not attack:
			actions.append(ScenarioAction(context, attack_region))
			attack = True

		actions.append(ScenarioAction(context, attack_region, actionDelay, {"seconds": 3}))
		return self.retryScenario(actions)
