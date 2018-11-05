import copy
import logging
import math
import threading

import flask
from flask import views
from flask import json


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


_last_data = LastData()


def last_data(update=None):
    if update is not None:
        _last_data.update(update)
    return _last_data.copy()


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
