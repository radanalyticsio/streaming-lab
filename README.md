# radanalytics.io streaming and event processing lab

This repository contains artifacts and resources to support the streaming and
event processing labs for radanalytics.io.

## Source data

The source data for this lab is imagined as a series of synthetic social media
updates. The text from these updates will be used in conjunction with sentiment
analysis to help demonstrate the use of machine learning to investigate data.
The data used for this lab is randomly generated using
[Markov chains](https://en.wikipedia.org/wiki/Markov_chain). None of this data
is from live accounts and it contains no personally identifiable information.

The format used for transmitting the update data on the wire is defined by
this [JSON Schema](http://json-schema.org) notation:

```
{
    "title": "Social Media Update",
    "type": "object",
    "properties": {
        "user_id": {
            "type": "string"
        },
        "update_id": {
            "type": "string"
        },
        "text": {
            "type": "string"
        }
    },
    "required": ["user_id", "update_id", "text"]
}
```

## Stream analyzer service

The stream analyzer service, `update-analyzer`, is a Python application
which uses Apaceh Spark to process the stream data as it arrives. After each
update is processed by the analyzer, it is sent to a visualizer,
`update-visualizer` application by a HTTP based request. In this manner, the
data processing that is occurring in the analyzer can be viewed by a user.

The following diagram represents the architecture of this application
pipeline:

![architecture](architecture.svg)

### Deployment

WIP
