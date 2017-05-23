from mss import mss
from PIL import Image
from gbf_raid_bot.capture.region import Region
from gbf_raid_bot.utilities import get_current_millis

import time
import numpy as np
import cv2

def capture_region(region):
	monitor = {
		"left": region.left,
		"top": region.top,
		"width": region.width,
		"height": region.height
	}
	with mss() as sct:
		sct.get_pixels(monitor)
		img = Image.frombytes("RGB", (sct.width, sct.height), sct.image)
	# img = ImageGrab.grab(bbox=(region.x, region.y, region.w, region.h))
	img = np.array(img, dtype="uint8")
	img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
	return img

def capture(callback, **kwargs):
	if "region" in kwargs:
		region = kwargs["region"]
	else:
		region = Region(**kwargs)

	if not isinstance(region, Region):
		region = Region(region=region)

	last_time = get_current_millis()
	while (True):
		img = capture_region(region)
		if not callback(img, region, last_time):
			break
		last_time = get_current_millis()
