import argparse
import logging
import os
import json
import cv2

from kafka import KafkaConsumer

def get_arg(env, default):
    return os.getenv(env) if os.getenv(env, '') is not '' else default


def parse_args(parser):
    args = parser.parse_args()
    args.brokers = get_arg('KAFKA_BROKERS', args.brokers)
    args.topic_in = get_arg('KAFKA_TOPIC_IN', args.topic_in)
    args.topic_out = get_arg('KAFKA_TOPIC_OUT', args.topic_out)
    return args


def main(args):
    from darkflow.net.build import TFNet
    
    consumer = KafkaConsumer(args.topic_in, bootstrap_servers=args.brokers)
    producer = KafkaProducer(bootstrap_servers=args.brokers)
    options = {"model": "yolo.cfg", "load": "yolo.weights", "threshold" : 0.1}
    yolo = TFNet(options)
    
    for msg in consumer:
        value = json.loads(str(msg.value, "utf-8"))
        try:
          image = base64.b64decode(value["contents"])
          imgcv = cv2.imdecode(numpy.asarray(bytearray(image), dtype=numpy.uint8), cv2.IMREAD_COLOR)
          predictions = yolo.return_predict(imgcv)

          # annotate image with bounding boxes
          rows, cols, _ = imgcv.shape
          thickness = int(max(rows, cols) / 100)
          for prediction in predictions:
            tl = prediction["topleft"]
            topleft = (tl["x"], tl["y"])
            br = prediction["bottomright"]
            bottomright = (br["x"], br["y"])
            # draw a white rectangle around the identified object
            white = (255,255,255)
            cv2.rectangle(imgcv, topleft, bottomright, color=white, thickness=thickness)
          
          # resize long edge to 256 pixels
          factor = 256.0 / max(rows, cols)
          _, outimg = cv2.imencode(".jpg", cv2.resize(imgcv, fx=factor, fy=factor))
          outimg_enc = base64.b64encode(outimg.tobytes()).decode("ascii")
          
          producer.send(args.topic_out, bytes(json.dumps({"predictions" : predictions, "image": outimg_enc})))
        except Exception as e:
          logging.warn('error processing image data:')
          logging.warn(e.message)
              
    logging.info('exiting')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.info('starting kafka-openshift-python-listener')
    parser = argparse.ArgumentParser(
            description='listen for some stuff on kafka')
    parser.add_argument(
            '--brokers',
            help='The bootstrap servers, env variable KAFKA_BROKERS',
            default='localhost:9092')
    parser.add_argument(
            '--topic-in',
            help='Topic to listen to, env variable KAFKA_TOPIC_IN',
            default='raw-images')
    parser.add_argument(
            '--topic-out',
            help='Topic to publish to, env variable KAFKA_TOPIC_OUT',
            default='processed-images')
    args = parse_args(parser)
    main(args)