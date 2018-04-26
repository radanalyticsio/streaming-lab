import argparse
import copy
import logging
import os
import threading

import flask
from flask import views
from flask import json


access_lock = threading.Lock()
_last_data = {}

def last_data(update=None):
    access_lock.acquire()
    if update is not None:
        global _last_data
        _last_data = copy.deepcopy(update)
    retval = copy.deepcopy(_last_data)
    access_lock.release()
    return retval


class RootView(views.MethodView):
    def get(self):
        return json.jsonify(last_data())

    def post(self):
        data = flask.request.data
        last_data(json.loads(data))
        return ('', 202)


def main():
    # create the flask app object
    app = flask.Flask(__name__)
    # change this value for production environments
    app.config['SECRET_KEY'] = 'secret!'

    app.add_url_rule('/', view_func=RootView.as_view('index'))

    app.run(host='0.0.0.0', port=8080)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.info('starting update-visualizer')
    main()
    logging.info('exiting')

