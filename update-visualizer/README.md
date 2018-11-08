# update-visualizer

an application to read updates from a kafka topic and provide a rest interface
to get information about what it has seen.

## Quickstart

Simple command line startup

```
oc new-app centos/python-36-centos7~https://github.com/radanalyticsio/streaming-lab \
  --context-dir=update-visualizer \
  -e KAFKA_BROKERS=kafka.kafka.svc:9092 \
  -e KAFKA_TOPIC=social-firehose \
  --name=visualizer

oc expose svc/visualizer
```

Please note that you will need to change the `KAFKA_BROKERS` and `KAFKA_TOPIC`
environment variables to match your deployment.
