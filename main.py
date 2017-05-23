#!/usr/bin/env python

from gbf_raid_bot.capture.template import TemplateList, TemplateMatcher
from gbf_raid_bot.capture import capture
from gbf_raid_bot.scenario import ScenarioManager
from gbf_raid_bot.utilities import get_current_millis, module_from_string
from gbf_raid_bot.config import ConfigReader
from gbf_raid_bot import AppContext, Logger
from threading import Thread
from queue import Queue

import numpy as np
import cv2
import time
import pyautogui
import sys
import os
import random

# time in seconds
start_time = time.time()

def get_timeout_in_seconds(timeout):
	return (
		timeout["seconds"] +
		(timeout["minutes"] * 60) +
		(timeout["hours"] * 3600)
	)

basic_config = ConfigReader("basic_settings")
advanced_config = ConfigReader("advanced_settings")
scenario_config = ConfigReader("scenario_settings")
pattern_config = ConfigReader("pattern_settings")
training_data = ConfigReader("training_data").config

debug_log = advanced_config.get("debug.log")
logger = Logger(debug_log)

app_context = AppContext({
	"settings": {
		"basic": basic_config,
		"advanced": advanced_config,
		"scenario": scenario_config,
		"pattern": pattern_config
	},
	"logger": logger
})

debug_vision = advanced_config.get("debug.vision")
debug_scenarios = advanced_config.get("debug.scenarios")

frame_per_second = advanced_config.get("image_processing.fps")
threshold = advanced_config.get("image_processing.threshold")
window_region = advanced_config.get("image_processing.window.region")
downsample_scale = advanced_config.get("image_processing.downsample")
blur_amount = advanced_config.get("image_processing.blur")

timeout_seconds = get_timeout_in_seconds(basic_config.get("timeout"))
start_delay = basic_config.get("start_delay")

scenario_selected = basic_config.get("scenario")
scenario_sets = scenario_config.get(scenario_selected)
scenarios = []

for scenario in scenario_sets:
	if isinstance(scenario, list):
		scenario_name, config = scenario
	else:
		scenario_name = scenario
		config = None

	class_ = module_from_string("scenario_sets." + scenario_name)
	instance = class_(app_context)
	if config is not None:
		instance.mergeConfig(config)
	scenarios.append(instance)

scenario_manager = ScenarioManager(app_context, scenarios)
frame_time = 1000 / frame_per_second
img_queue = Queue(maxsize=1)

logger.debug("Using scenario '%s'" % scenario_selected)

def process_img(img):
	img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
	if blur_amount > 0:
		img = cv2.GaussianBlur(img, (blur_amount, blur_amount), 0)
	if downsample_scale != 1.0:
		img = cv2.resize(img, (0, 0), fx=downsample_scale, fy=downsample_scale, interpolation=cv2.INTER_LANCZOS4)
	img = cv2.Canny(img, 190, 250)
	return img

templates = TemplateList(training_data, process_img, downsample_scale)

if len(sys.argv) >= 2:
	scenario_manager.index = int(sys.argv[1])

def check_timeout():
	diff_time = time.time() - start_time
	return diff_time < timeout_seconds and scenario_manager.running

def mark_region(img, name, region):
	color = tuple(debug_vision.get("regions.color", [255, 0, 255])[::-1])

	cv2.putText(
		img, name,
		(region.x, region.y - 5),
		cv2.FONT_HERSHEY_DUPLEX,
		0.4,
		color,
		thickness=1
	)

	cv2.rectangle(
		img,
		(region.left, region.top),
		(region.right, region.bottom),
		color,
		thickness=2
	)

	return img

def handle_window(item):
	global low, high

	processed_img = item["processed_img"]
	features = item["features"]
	region = item["region"]
	img = item["img"]

	if debug_vision.get("processed", False):
		img = processed_img

	if debug_vision.get("regions.enabled", False):
		vision_features = debug_vision.get("regions.features", [])
		for name, match_regions in features.some(vision_features).items():
			for match_region in match_regions:
				img = mark_region(img, name, match_region)

	position = debug_vision.get("position")
	cv2.imshow("Bot Vision", img)
	cv2.moveWindow("Bot Vision", position["x"], position["y"])

	if cv2.waitKey(1) & 0xFF == ord("q"):
		cv2.destroyAllWindows()
		return False

	return True

def handle_capture(img, region, last_time):
	processed = process_img(img)
	features = TemplateMatcher(templates, processed, threshold)

	if debug_vision.get("enabled", False):
		img_queue.put({
			"last_time": last_time,
			"processed_img": processed,
			"features": features,
			"region": region,
			"img": img
		})

	if debug_scenarios.get("enabled", False):
		scenario_manager.handle(region, img, features)

	diff_time = get_current_millis() - last_time
	if debug_log.get("frame_time", False):
		logger.debug("Took %.2fs to process" % float(diff_time / 1000))

	wait_time = float((frame_time - diff_time) / 1000)
	if wait_time > 0:
		time.sleep(wait_time)

	return check_timeout()

def thread_task(queue, handler):
	running = True
	while running and check_timeout():
		item = queue.get()
		running = handler(item)
		queue.task_done()

if debug_vision.get("enabled", False):
	t = Thread(target=thread_task, args=(img_queue, handle_window,))
	t.daemon = True
	t.start()

if start_delay > 0:
	for i in range(start_delay)[::-1]:
		print("%d..." % (i+1))
		time.sleep(1)

capture_args = window_region.toDict()
capture_args["callback"] = handle_capture
capture(**capture_args)

# clean up the mess
for scenario in scenarios:
	scenario.cleanUp()

logger.debug("Finished successfully")
