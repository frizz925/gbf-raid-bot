import re

def checkSource(tweetFilter, status):
	return status.source_url == "http://granbluefantasy.jp/"

def checkText(tweetFilter, status):
	query = tweetFilter.query
	if query is None:
		return True
	elif not isinstance(query, list):
		query = [query]
	return re.search("(%s)" % "|".join(query), status.text)

class TweetFilter:
	def __init__(self, query=None):
		self.query = query
		self.checkers = [
			checkSource,
			checkText
		]

	def check(self, status):
		for checker in self.checkers:
			if not checker(self, status):
				return False
		return True
