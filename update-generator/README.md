# update-generator

A Python application that emits synthetic social media updates to an Apache Kafka topic.

## Launching on OpenShift

```
oc new-app centos/python-34-centos7~https://github.com/bones-brigade/kafka-openshift-python-emitter \
  -e KAFKA_BROKERS=kafka:9092 \
  -e KAFKA_TOPIC=social-firehose \
  -e UPDATE_SOURCE_1=austen.txt \
  -e UPDATE_SOURCE_2=reviews-1.txt.gz \
  -e UPDATE_SOURCE_3=reviews-5-100k.txt.gz \
  -e UPDATE_WEIGHT_1=20 \
  -e UPDATE_WEIGHT_2=3 \
  -e UPDATE_WEIGHT_3=3 \
  --name=emitter
```

You will need to adjust the `KAFKA_BROKERS` and `KAFKA_TOPICS` variables to match your configured
Kafka deployment and desired topic. 

For now, text corpora and weights are hardcoded to data files bundled in the image. In the
future, the `UPDATE_SOURCE_X` environment variables will allow you to specify several URIs of
text corpora to train independent Markov chains from; you can specify weighting factors for these
with `UPDATE_WEIGHT_X` variables.
