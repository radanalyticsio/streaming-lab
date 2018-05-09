import argparse
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
    spark = sql.SparkSession.builder.appName('update-mutator').getOrCreate()

    msg_struct = types.StructType([
        types.StructField('text', types.StringType(), True),
        types.StructField('user_id', types.StringType(), True),
        types.StructField('update_id', types.StringType(), True)
    ])

    sentiments_struct = types.ArrayType(
            types.MapType(types.StringType(), types.FloatType(), False))

    analyzer = vader.SentimentIntensityAnalyzer()
    analyzer_bcast = spark.sparkContext.broadcast(analyzer)

    def sentiment_generator_impl(text):
        va = analyzer_bcast.value
        english = SpacyMagic.get('en_core_web_sm')
        result = english(text)
        sents = [str(sent) for sent in result.sents]
        sentiment = [va.polarity_scores(str(s)) for s in sents]
        return sentiment

    sentiment_generator = functions.udf(
        sentiment_generator_impl,  sentiments_struct)

    def json_converter_impl(user_id, update_id, text, sentiments):
        obj = dict(user_id=user_id,
                   update_id=update_id,
                   text=text,
                   sentiments=sentiments)
        return json.dumps(obj)

    json_converter = functions.udf( json_converter_impl, types.StringType())

    records = (
        spark
        .readStream
        .format('kafka')
        .option('kafka.bootstrap.servers', args.brokers)
        .option('subscribe', args.intopic)
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
                functions.column('json.text')).alias('sentiments'))
        .select(
            json_converter(
                functions.column('user_id'),
                functions.column('update_id'),
                functions.column('text'),
                functions.column('sentiments')).alias('value'))
        .writeStream
        .format('kafka')
        .option('kafka.bootstrap.servers', args.brokers)
        .option('topic', args.outtopic)
        .option('checkpointLocation', '/tmp')
        .start()
    )

    records.awaitTermination()


def get_arg(env, default):
    return os.getenv(env) if os.getenv(env, '') is not '' else default


def parse_args(parser):
    args = parser.parse_args()
    args.brokers = get_arg('KAFKA_BROKERS', args.brokers)
    args.intopic = get_arg('KAFKA_IN_TOPIC', args.intopic)
    args.outtopic = get_arg('KAFKA_OUT_TOPIC', args.outtopic)
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
            '--in-topic',
            dest='intopic',
            help='Topic to publish to, env variable KAFKA_TOPIC',
            default='social-firehose')
    parser.add_argument(
            '--out-topic',
            dest='outtopic',
            help='Topic to publish to, env variable KAFKA_TOPIC',
            default='social-firehose')
    args = parse_args(parser)
    main(args)
    logging.info('exiting')
