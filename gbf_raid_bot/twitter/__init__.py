from gbf_raid_bot.twitter.tweet_filter import TweetFilter
from gbf_raid_bot.twitter.tweet_parser import TweetParser

import tweepy

class TwitterClient:
	def __init__(self, consumerKeys, accessTokens=None):
		if "access_token" in consumerKeys:
			accessTokens = {
				"access_token": consumerKeys["access_token"],
				"access_token_secret": consumerKeys["access_token_secret"],
			}

		self.consumerKeys = consumerKeys
		self.auth = tweepy.OAuthHandler(
			consumerKeys["consumer_key"], 
			consumerKeys["consumer_secret"]
		)

		self.accessTokens = None
		self.client = None
		if accessTokens is not None:
			self.setAccessTokens(accessTokens)

	def setAccessTokens(self, accessTokens):
		self.accessTokens = accessTokens
		self.client = self.auth.set_access_token(
			accessTokens["access_token"],
			accessTokens["access_token_secret"]
		)

	def stream(self, callback, query=None, async=False):
		processor = TweetProcessor(callback, query)
		listener = TweetListener().setUp(processor)
		stream = tweepy.Stream(auth=self.auth, listener=listener)

		track = ["I need backup!Battle ID: "]
		for lvl in range(15, 150, 5):
			track.append("Lv%d" % lvl)
		stream.filter(track=track, async=async)

class TweetProcessor:
	def __init__(self, callback, query=None):
		self.callback = callback
		self.query = query
		self.filter = TweetFilter(query)
		self.parser = TweetParser()

	def process(self, status):
		if not self.filter.check(status):
			return
		code, boss = self.parser.parse(status)
		self.callback(code, boss)

class TweetListener(tweepy.StreamListener):
	def setUp(self, processor):
		self.processor = processor
		return self

	def on_status(self, status):
		assert(self.processor)
		self.processor.process(status)

if __name__ == "__main__":
	def printTweet(code, boss):
		print("%s %s" % (code, boss))

	from gbf_raid_bot.config import ConfigReader
	twitter_settings = ConfigReader("twitter_settings")
	twitter_client = TwitterClient(twitter_settings.toDict())
	twitter_client.stream(printTweet, "Lvl 75 Celeste Omega")
