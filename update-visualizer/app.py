import argparse
import copy
import logging
import logging.config as lconfig
import math
import os
import threading

import flask
from flask import views
from flask import json
import kafka


class LastData():
    def __init__(self):
        self._access_lock = threading.Lock()
        self._data = {
            'last-seen': {},
            'most-positive': {},
            'most-negative': {},
        }

    @staticmethod
    def get_compound_average(sentiments):
        """return the average compound sentiment from a list of sentiments"""
        if len(sentiments) > 0:
            compounds = [s.get('compound', 0) for s in sentiments]
            avg = math.fsum(compounds) / len(sentiments)
        else:
            avg = 0
        return avg

    def update(self, newdata):
        self._access_lock.acquire()
        self._data['last-seen'] = copy.deepcopy(newdata)
        new_cavg = LastData.get_compound_average(
                self._data['last-seen'].get('sentiments', []))
        pos_cavg = LastData.get_compound_average(
                self._data['most-positive'].get('sentiments', []))
        neg_cavg = LastData.get_compound_average(
                self._data['most-negative'].get('sentiments', []))
        if new_cavg >= pos_cavg:
            self._data['most-positive'] = self._data['last-seen']
        if new_cavg <= neg_cavg:
            self._data['most-negative'] = self._data['last-seen']
        self._access_lock.release()

    def copy(self):
        self._access_lock.acquire()
        retval = copy.deepcopy(self._data)
        self._access_lock.release()
        return retval


exit_event = threading.Event()
_last_data = LastData()


def last_data(update=None):
    if update is not None:
        _last_data.update(update)
    return _last_data.copy()


class RootView(views.MethodView):
    def get(self):
        return json.jsonify(last_data())


def consumer(args):
    logging.info('starting kafka consumer')
    consumer = kafka.KafkaConsumer(args.topic, bootstrap_servers=args.brokers)
    for msg in consumer:
        if exit_event.is_set():
            break
        try:
            last_data(json.loads(str(msg.value, 'utf-8')))
        except Exception as e:
            logging.error(e.message)
    logging.info('exiting kafka consumer')


def get_arg(env, default):
    return os.getenv(env) if os.getenv(env, '') is not '' else default


def parse_args(parser):
    args = parser.parse_args()
    args.brokers = get_arg('KAFKA_BROKERS', args.brokers)
    args.topic = get_arg('KAFKA_TOPIC', args.topic)
    return args


def main(args):
    exit_event.clear()
    # setup consumer thread
    cons = threading.Thread(group=None, target=consumer, args=(args,))
    cons.start()

    # create the flask app object
    app = flask.Flask(__name__)
    # change this value for production environments
    app.config['SECRET_KEY'] = 'secret!'
    app.add_url_rule('/', view_func=RootView.as_view('index'))
    app.run(host='0.0.0.0', port=8080)

    exit_event.set()
    cons.join()
    logging.info('exiting flask-kafka-listener')


if __name__ == '__main__':
    lconfig.dictConfig({
        'version': 1,
        'formatters': {'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
            }},
        'handlers': {'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
            }},
        'root': {
            'level': 'INFO',
            'handlers': ['wsgi']
            }
        })
    logging.basicConfig(level=logging.INFO)
    logging.info('starting update-visualizer')
    parser = argparse.ArgumentParser(
            description='listen for some stuff on kafka')
    parser.add_argument(
            '--brokers',
            help='The bootstrap servers, env variable KAFKA_BROKERS',
            default='kafka.kafka.svc:9092')
    parser.add_argument(
            '--topic',
            help='Topic to publish to, env variable KAFKA_TOPIC',
            default='social-firehose')
    args = parse_args(parser)
    main(args)
    logging.info('exiting')
