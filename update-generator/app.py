import argparse
import logging
import os
import time
import urllib

from kafka import KafkaProducer

import markovify
import spacy
import numpy
import math
import collections

import gzip
import codecs

import json

def train_markov_gutenberg_txt(fn):
    """ trains a Markov model on text data from Project Gutenberg """
    with codecs.open(fn, "r", "cp1252") as f:
        text = f.read()

    return markovify.Text(text, retain_original=False, state_size=3)

def train_markov_gz(fn):
    """ trains a Markov model on gzipped text data """
    with gzip.open(fn, "rt", encoding="utf-8") as f:
        text = f.read()
    return markovify.Text(text, retain_original=False, state_size=3)


class UserTable(object):
    """ 
    Table of random user IDs; models two kinds of user:  talkative and moderate.
    The assumption is that talkative users represent a proportion p of all users 
    but 1 - p of all utterances. 
    """
    def __init__(self, size, weights=[8, 2]):
        self._talkative = collections.deque()
        self._moderate = collections.deque()
        self._size = size
        self._cutoff = float(weights[0]) / sum(weights)
        
        for i in range(size):
            new_uid = math.floor(numpy.random.uniform(10 ** 10))
            if numpy.random.uniform() >= self._cutoff:
                self._moderate.append(new_uid)
            else:
                self._talkative.append(new_uid)
    
    def random_uid(self):
        def choose_from(c):
            return c[math.floor(numpy.random.uniform() * len(c))]
        
        if numpy.random.uniform() >= self._cutoff:
            return choose_from(self._talkative)
        else:
            return choose_from(self._moderate)

import spacy
nlp = spacy.load('en_core_web_sm')

def make_sentence(model, length=200):
    return model.make_short_sentence(length)
    
def hashtagify_full(sentence):
    doc = nlp(sentence)
    for ent in doc.ents:
        sentence = sentence.replace(str(ent), "#%s" % str(ent).replace(" ", ""))
    return (sentence, ["#%s" % str(ent).replace(" ", "") for ent in doc.ents])

def hashtagify(sentence):
    result,_ = hashtagify_full(sentence)
    return result

def update_generator(models, weights=None, hashtag_weights=[8, 2], ut=None, seed_hashtags=[]):
    if weights is None:
        weights = [1] * len(models)
    
    if ut is None:
        ut = UserTable(10000)
    
    choices = []
    
    total_weight = float(sum(weights))
    
    for i in range(len(weights)):
        choices.append((float(sum(weights[0:i+1])) / total_weight, models[i]))
    
    def choose_model():
        r = numpy.random.uniform()
        for (p, m) in choices:
            if r <= p:
                return m
        return choices[-1][1]
    
    seen_hashtags = set()
    hashtags = []
    total_hashtag_weight = float(sum(hashtag_weights))
    for i in range(len(hashtag_weights)): 
        hashtags.append((float(sum(hashtag_weights[0:i+1])) / total_hashtag_weight, collections.deque()))
    
    iws = [1.0 - w for (w, _) in hashtags]
    inverse_weights = [(sum(iws[0:i+1]), i) for _, i in zip(iws, range(len(iws)))]    

    def choose_from(c):
        idx = math.floor(numpy.random.uniform() * len(c))
        return c[idx]
    
    def store_hashtag(tag):
        if tag not in seen_hashtags:
            seen_hashtags.add(str(tag))
            r = numpy.random.uniform()
            for(p, deq) in hashtags:
                if r <= p:
                    deq.append(tag)
    
    def choose_hashtag():
        r = numpy.random.uniform()
        for(p, i) in hashtags:
            if r <= - p and len(hashtags[i][1]) > 0:
                return choose_from(hashtags[i][1])
        return len(hashtags[0][1]) > 0 and choose_from(hashtags[0][1]) or choose_from(hashtags[1][1])
    
    for tag in seed_hashtags:
        seen_hashtags.add(str(tag))
        hashtags[-1][1].append(str(tag))
    
    while True:
        tweet, tags = hashtagify_full(make_sentence(choose_model()))
        for tag in tags:
            store_hashtag(str(tag))
        
        this_tweet_tags = set([str(t) for t in tags])
        
        if len(seen_hashtags) > 0:
            for i in range(min(numpy.random.poisson(3), len(seen_hashtags))):
                tag = choose_hashtag()
                if str(tag) not in this_tweet_tags:
                    this_tweet_tags.add(str(tag))
                    tweet += " %s" % str(tag)
            
        yield (ut.random_uid(), tweet)


def main(args):
    logging.info('brokers={}'.format(args.brokers))
    logging.info('topic={}'.format(args.topic))
    logging.info('rate={}'.format(args.rate))
    logging.info('source={}'.format(args.source))

    logging.info('creating Markov chains')
    
    austen_model = train_markov_gutenberg_txt("austen.txt")
    negative_model = train_markov_gz("reviews-1.txt.gz")
    positive_model = train_markov_gz("reviews-5-100k.txt.gz")
    
    logging.info('creating update generator')
    
    seed_hashtags=["#ff", "#marketing", "#fail", "#followfriday", "#yolo", "#retweet", "#tbt", "#socialmedia", "#startup", "#blogpost", "#news", "#health"]
    ug = update_generator([austen_model, positive_model, negative_model], [22, 4, 4], seed_hashtags=seed_hashtags)
    
    update_id = 0
    
    logging.info('creating kafka producer')
    producer = KafkaProducer(bootstrap_servers=args.brokers)
    
    logging.info('sending lines')
    while True:
        update = {"update_id" : "%020d" % update_id}
        update_id += 1
        userid, text = next(ug)
        update["userid"] = "%010d" % userid
        update["text"] = text
        
        producer.send(args.topic, bytes(json.dumps(update), "utf-8"))
        time.sleep(1.0 / args.rate)
    logging.info('finished sending source')


def get_arg(env, default):
    return os.getenv(env) if os.getenv(env, '') is not '' else default


def parse_args(parser):
    args = parser.parse_args()
    args.brokers = get_arg('KAFKA_BROKERS', args.brokers)
    args.topic = get_arg('KAFKA_TOPIC', args.topic)
    args.rate = get_arg('RATE', args.rate)
    args.source = get_arg('SOURCE_URI', args.source)
    return args


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.info('starting update-generator')
    parser = argparse.ArgumentParser(description='emit synthetic social media updates on kafka')
    parser.add_argument(
            '--brokers',
            help='The bootstrap servers, env variable KAFKA_BROKERS',
            default='localhost:9092')
    parser.add_argument(
            '--topic',
            help='Topic to publish to, env variable KAFKA_TOPIC',
            default='social-firehose')
    parser.add_argument(
            '--rate',
            type=int,
            help='Lines per second, env variable RATE',
            default=10)
    parser.add_argument(
            '--source',
            help='The source URI for data to emit, env variable SOURCE_URI')
    args = parse_args(parser)
    main(args)
    logging.info('exiting')
