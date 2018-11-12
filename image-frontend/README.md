# image-frontend

This is a very basic Flask application that accepts image uploads and serializes the image data on to a Kafka topic.

## usage

```
oc new-app centos/python-36-centos7~https://github.com/radanalyticsio/streaming-lab/ \
  --context-dir=image-frontend \
  -e KAFKA_BROKERS=my-kafka-host:9092 \
  -e KAFKA_TOPIC=raw-images \
  --name=image-frontend
```