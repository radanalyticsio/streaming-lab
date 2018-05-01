import argparse
import httplib
import json
import logging
import os

import pyspark
from pyspark import streaming
from pyspark.streaming import kafka as kstreaming


def main(args):
    spark_context = pyspark.SparkContext(appName='update-analyzer')
    streaming_context = streaming.StreamingContext(spark_context, 1)
    kafka_stream = kstreaming.KafkaUtils.createDirectStream(
            streaming_context,
            [args.topic],
            {'bootstrap.servers': args.brokers})

    def analyze_update(rdd):
        def post_update(u):
            try:
                con = httplib.HTTPConnection(host=args.vhost,
                                             port=args.vport)
                con.request('POST', '/', body=json.dumps(u))
                con.close()
            except Exception as e:
                logging.warn('unable to POST to visualizer, error:')
                logging.warn(e.message)

        rdd.foreach(post_update)

    messages = kafka_stream.map(lambda m: m[1])
    messages.foreachRDD(analyze_update)
    streaming_context.start()
    streaming_context.awaitTermination()


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
