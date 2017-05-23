# Granblue Fantasy Computer Vision Bot

## This software is highly experimental and is changing from times to times!
Since I'm too lazy to write documentation, I'll just leave some FAQs here.

## FAQs
### Is it undetectable?
So far this does not use any JavaScript injection or Chrome extension and relies heavily using OpenCV library so it should be virtually undetectable.

### Can I get banned?
If you keep the bot running 24/7 and failed to enter the captcha, sure.

### Where can I download it?
You can't. Only source code provided for free under MIT license.

### When will it be available?
This software is still very experimental and may break from times to times so it's not going to happen soon.

### Does it work on Windows?
Maybe. The bot's vision partially works across platforms but there's calibration tool to train the bot's vision when needed. So far it's only tested on Xubuntu 16.04.1 64-bit with 1920x1080 resolution with 1.0x scaling.

## Prerequisites
- Python 3.5
- PIP
- OpenCV

## Features
- Built as a framework as much as possible, making new features or modules be easily written and implemented by other developers.
- Uses OpenCV and PyAutoGUI to automatically detect a portion of image on the screen and move the mouse accordingly.
