# update-analyzer

An Apache Spark application to monitor a stream of social media style updates
from an Apache Kafka source. Sentiment analysis is applied to the updates and
then they are sent to a REST based microservice.

For installation instructions, please see the base [README](../README.md)

## Command line launch

If you have already configured an Apache Spark cluster and would like to
launch the analyzer from the command line with the `oc` tool, please use
the following command:

```
oc new-app --template=oshinko-python-spark-build-dc \
  -p APPLICATION_NAME=analyzer \
  -p GIT_URI=https://github.com/radanalyticsio/streaming-lab \
  -p CONTEXT_DIR=update-analyzer \
  -p APP_ARGS='--brokers=kafka.kafka.svc:9092 --topic=firehose --visualizer-host=visualizer --visualizer-port=8080' \
  -p SPARK_OPTIONS='--packages org.apache.spark:spark-sql-kafka-0-10_2.11:2.2.1' \
  -p OSHINKO_CLUSTER_NAME=mycluster
```

Please note, you will need to change the brokers, visualizer, and cluster
names to match your deployments.
