import argparse
import httplib
import json
import logging
import os

import pyspark.sql as sql
import pyspark.sql.types as types
import pyspark.sql.functions as functions
import vaderSentiment.vaderSentiment as vader


# This code is borrowed from Sparkling Pandas; see here:
# https://github.com/sparklingpandas/sparklingml/blob/627c8f23688397a53e2e9e805e92a54c2be1cf3d/sparklingml/transformation_functions.py#L53
class SpacyMagic(object):
    """
    Simple Spacy Magic to minimize loading time.
    >>> SpacyMagic.get("en")
    <spacy.en.English ...
    """
    _spacys = {}

    @classmethod
    def get(cls, lang):
        if lang not in cls._spacys:
            import spacy
            cls._spacys[lang] = spacy.load(lang)
        return cls._spacys[lang]


def main(args):
    spark = sql.SparkSession.builder.appName('update-analyzer').getOrCreate()

    msg_struct = types.StructType([
        types.StructField('text', types.StringType(), True),
        types.StructField('user_id', types.StringType(), True),
        types.StructField('update_id', types.StringType(), True)
    ])

    analyzer = vader.SentimentIntensityAnalyzer()
    analyzer_bcast = spark.sparkContext.broadcast(analyzer)
    vhost_bcast = args.vhost
    vport_bcast = args.vport

    def sentiment_generator_impl(text, user_id, update_id):
        va = analyzer_bcast.value
        english = SpacyMagic.get('en_core_web_sm')
        result = english(text)
        sents = [str(sent) for sent in result.sents]
        sentiments = [va.polarity_scores(str(s)) for s in sents]
        obj = dict(user_id=user_id,
                   update_id=update_id,
                   text=text,
                   sentiments=sentiments)
        try:
            con = httplib.HTTPConnection(host=vhost_bcast,
                                         port=vport_bcast)
            con.request('POST', '/', body=json.dumps(obj))
            con.close()
        except Exception as e:
            logging.warn('unable to POST to visualizer, error:')
            logging.warn(e.message)

    sentiment_generator = functions.udf(
        sentiment_generator_impl, types.NullType())

    records = (
        spark
        .readStream
        .format('kafka')
        .option('kafka.bootstrap.servers', args.brokers)
        .option('subscribe', args.topic)
        .load()
        .select(
            functions.column('value').cast(types.StringType()).alias('value'))
        .select(
            functions.from_json(
                functions.column('value'), msg_struct).alias('json'))
        .select(
            functions.column('json.user_id'),
            functions.column('json.update_id'),
            functions.column('json.text'),
            sentiment_generator(
                functions.column('json.text'),
                functions.column('json.user_id'),
                functions.column('json.update_id')))
        .writeStream
        .format("console")
        .start()
    )

    records.awaitTermination()


def get_arg(env, default):
    return os.getenv(env) if os.getenv(env, '') is not '' else default


def parse_args(parser):
    args = parser.parse_args()
    args.brokers = get_arg('KAFKA_BROKERS', args.brokers)
    args.topic = get_arg('KAFKA_TOPIC', args.topic)
    args.vhost = get_arg('VISUALIZER_HOST', args.vhost)
    args.vport = get_arg('VISUALIZER_POST', args.vport)
    return args


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.info('starting update-listener')
    parser = argparse.ArgumentParser(
            description='listen for synthetic social media updates on kafka')
    parser.add_argument(
            '--brokers',
            help='The bootstrap servers, env variable KAFKA_BROKERS',
            default='localhost:9092')
    parser.add_argument(
            '--topic',
            help='Topic to publish to, env variable KAFKA_TOPIC',
            default='social-firehose')
    parser.add_argument(
            '--visualizer-host',
            dest='vhost',
            help='The hostname for the visualizer service, env variable '
                 'VISUALIZER_HOST',
            default='visualizer')
    parser.add_argument(
            '--visualizer-port',
            dest='vport',
            help='The port for the visualizer service, env variable '
                 'VISUALIZER_PORT',
            default=8080)
    args = parse_args(parser)
    main(args)
    logging.info('exiting')
