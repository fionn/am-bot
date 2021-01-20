#!/usr/bin/env python3
"""May Avram tweet forever"""

import os
import re
import sys
import json
import pathlib
from typing import List

import tweepy
import markovify
import nltk

class NLPText(markovify.NewlineText):
    """Extend markovify.NewlineText with NLP"""

    def word_split(self, sentence: str) -> List[str]:
        """Splits a sentence into a list of words"""
        words = re.split(self.word_split_pattern, sentence)
        return ["::".join(tag) for tag in nltk.pos_tag(words)]

    # Not a static method because it's an override
    def word_join(self, words: List[str]) -> str:
        """Re-joins a list of words into a sentence"""
        return " ".join(word.split("::")[0] for word in words)

# pylint: disable=too-few-public-methods
class Twitter:
    """Wrapper for the Twitter API"""

    def __init__(self) -> None:
        auth = tweepy.OAuthHandler(os.environ["API_KEY"],
                                   os.environ["API_SECRET"])
        auth.set_access_token(os.environ["ACCESS_TOKEN"],
                              os.environ["ACCESS_TOKEN_SECRET"])
        self.api = tweepy.API(auth, wait_on_rate_limit=True,
                              wait_on_rate_limit_notify=True)

    @staticmethod
    def _compose(model: NLPText) -> dict:
        """Compose a status dictionary compatible with api.status_update"""
        text = model.make_short_sentence(280, state_size=2)

        # Don't @ people
        while text[0] == "@" or text[0] == ".":
            text = " ".join(text.split()[1:])
        text = text.replace("@", "")

        # Remove URLs
        # pylint: disable=W1401
        text = re.sub("https://t.co/[^\s]+", "", text)

        return {"status": text}

    def update(self, model: NLPText,
               dry_run: bool = False) -> tweepy.Status:
        """Post tweet for constituency"""
        composition = self._compose(model)
        print(composition["status"], file=sys.stderr)

        if dry_run:
            return tweepy.Status

        return self.api.update_status(**composition)

def generate_corpus(tweets: List[str]) -> str:
    """Very simple corpus text"""
    return "\n".join(tweet.strip() for tweet in tweets)

def main() -> None:
    """Entry point"""
    tweets_file = pathlib.Path("data/corpus.json")
    with tweets_file.open() as tweets_fd:
        tweets = json.load(tweets_fd)

    corpus = generate_corpus(tweets)
    model = NLPText(corpus)
    twitter = Twitter()
    twitter.update(model)

if __name__ == "__main__":
    main()
