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

