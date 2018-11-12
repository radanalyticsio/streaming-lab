#!/usr/bin/env python

# some file uploading code adapted from Flask documentation
# some kafka/flask integration code adapted from https://github.com/bones-brigade/flask-kafka-openshift-python-listener/

from flask import Flask, redirect, request, url_for
import base64
import argparse
import os
import json

from kafka import KafkaProducer

from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
topic = None
producer = None

def allowed_file(filename):
  return '.' in filename and \
    filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
  if request.method == 'POST':
    # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    f = request.files['file']
    # if user does not select file, browser also
    # submit a empty part without filename
    if f.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if f and allowed_file(f.filename):
        filename = secure_filename(f.filename)
        if producer is not None:
          producer.send(topic, bytes(json.dumps({"filename" : filename, "contents" : base64.b64encode(f.stream.read()).decode('ascii')}), "ascii"))
        f.close()
        return "<!doctype html><title>got your file</title><p>received file %s</p>" %  filename
  return '''
    <!doctype html>
    <title>Upload an image</title>
    <h1>Upload an image</h1>
    <form method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''

def get_arg(env, default):
    return os.getenv(env) if os.getenv(env, '') is not '' else default

def parse_args(parser):
    args = parser.parse_args()
    args.brokers = get_arg('KAFKA_BROKERS', args.brokers)
    args.topic = get_arg('KAFKA_TOPIC', args.topic)
    return args

if __name__ == '__main__':
  app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
  app.logger.setLevel(0)
  parser = argparse.ArgumentParser(
          description='listen for some stuff on kafka')
  parser.add_argument(
          '--brokers',
          help='The bootstrap servers, env variable KAFKA_BROKERS',
          default='localhost:9092')
  parser.add_argument(
          '--topic',
          help='Topic to publish to, env variable KAFKA_TOPIC',
          default='raw-images')
  
  args = parse_args(parser)
  
  topic = args.topic
  producer = KafkaProducer(bootstrap_servers=args.brokers)
  
  app.run(host='0.0.0.0', port=8080)