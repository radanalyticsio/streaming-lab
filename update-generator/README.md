# update-generator

A Python application that emits synthetic social media updates to an Apache Kafka topic.

## Launching on OpenShift

```
oc new-app centos/python-34-centos7~https://github.com/radanalyticsio/streaming-lab/ \
  --context-dir=update-generator \
  -e KAFKA_BROKERS=my-cluster-kafka:9092 \
  -e KAFKA_TOPIC=social-firehose \
  --name=emitter
```

You will need to adjust the `KAFKA_BROKERS` and `KAFKA_TOPICS` variables to match your configured
Kafka deployment and desired topic. 

For now, text corpora and weights are hardcoded to data files bundled in the image.