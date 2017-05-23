#!/usr/bin/env python
from gbf_raid_bot.calibration import WindowRegion, ImageTraining, BattlePattern

import subprocess as sp
import sys

calibrations = [WindowRegion(), ImageTraining(), BattlePattern()]
shouldExit = False

def clear():
	platform = sys.platform
	if sys.platform.startswith("win32"):
		tmp = sp.call("cls", shell=True)
	else:
		tmp = sp.call("clear", shell=True)

def headerTitle(text):
	print(text)
	print("====================\n")

def showMenu():
	global shouldExit

	clear()
	lastIdx = 0
	for idx, calibration in enumerate(calibrations):
		print("%d. %s" % (idx+1, calibration.name()))
		lastIdx = idx
	exitIdx = lastIdx + 1
	print("%d. Exit" % (exitIdx+1))
	select = input("Choose menu: ")
	try:
		select = int(select) - 1
		if select == exitIdx:
			shouldExit = True
			return None
		return calibrations[select]
	except:
		return None

def main():
	running = True
	while running:
		calibration = None
		while calibration is None:
			calibration = showMenu()
			if shouldExit:
				running = False
				break
		if not running:
			break
		calibration.calibrate()

if __name__ == "__main__":
	main()
