# update-transformer

A Python based microservice using Apache Spark to process social media
updates by consuming them from an Apache Kafka topic, applying sentiment
analysis to the text, and then broadcasting the updated message with metadata
on a second topic.

## Quickstart

```
oc new-app --template=oshinko-python-spark-build-dc \
  -p APPLICATION_NAME=transformer \
  -p GIT_URI=https://github.com/radanalyticsio/streaming-lab \
  -p CONTEXT_DIR=update-transformer \
  -p APP_ARGS='--brokers=summit-kafka.kafka.svc:9092 --in-topic=social-firehose --out-topic=sentiments' \
  -p SPARK_OPTIONS='--packages=org.apache.spark:spark-sql-kafka-0-10_2.11:2.2.1' \
  -p OSHINKO_CLUSTER_NAME=<INSERT CLUSTER NAME HERE>
```
