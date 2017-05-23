import re

class TweetParser:
	def parse(self, status):
		pattern = r'(参戦ID：|Battle ID: )(.+)\n(.+)'
		match = re.search(pattern, status.text)
		return match.group(2), match.group(3)
