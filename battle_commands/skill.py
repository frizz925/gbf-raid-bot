from gbf_raid_bot.scenario.scenario_action import ScenarioAction
from gbf_raid_bot.scenario.scenario_manager import ScenarioContext
from gbf_raid_bot.scenario import Scenario
from gbf_raid_bot.capture import Region
from scenario_sets.battle import PlayScenario

def indexed_region(scenario: Scenario, name, index):
	settings = scenario.appContext.get(name)
	margin = settings["margin"]
	region = settings["region"]
	return Region({
		"left": region["left"] + ((region["width"] + margin) * index),
		"top": region["top"],
		"width": region["width"],
		"height": region["height"]
	})

def character_region(scenario: Scenario, index):
	return indexed_region(scenario, "settings.advanced.image_processing.character", index)

def skill_region(scenario: Scenario, index):
	return indexed_region(scenario, "settings.advanced.image_processing.skill", index)

def skill(scenario: PlayScenario, context: ScenarioContext, *args):
	action = None
	chara_index = int(args[0])
	skill_indexes = map(int, args[1:])
	pending_command = scenario.pendingCommand
	click_args = {"clicks": 2}

	# click the character
	if pending_command == 0:
		region = character_region(scenario, chara_index)
		action = ScenarioAction(context, region, args=click_args)
		scenario.pendingCommand = 1
	# click the skills
	elif pending_command == 1:
		action = []
		for index in skill_indexes:
			region = skill_region(scenario, index)
			action.append(ScenarioAction(context, region, args=click_args))
		scenario.pendingCommand = 2
	# click the back button
	elif pending_command == 2:
		regions = context.features["btn_back"]
		if len(regions) == 0:
			return action
		action = ScenarioAction(context, regions[0])
		scenario.pendingCommand = 0

	return action
