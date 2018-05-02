# update-visualizer

An application to display social media updates that have been processed by
the update-analyzer.

## Quickstart

Simple command line startup

```
oc new-app centos/python-36-centos7~https://github.com/radanalyticsio/streaming-lab \
  --context-dir=update-visualizer \
  --name=visualizer

oc expose svc/visualizer
```
