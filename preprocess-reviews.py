#!/usr/bin/env python

import sqlite3
import json
import sys
import re

usage = """ 
USAGE:  ./preprocess-reviews.py database.sqlite rating
Assumes that database.sqlite is a SQLite file with a table called "reviews" that has fields called "score" and "text".
An example such database is available from the public domain Amazon fine foods review dataset:

https://www.kaggle.com/snap/amazon-fine-food-reviews/
"""

connection = sqlite3.connect(sys.argv[1])
cursor = connection.execute("SELECT score, text FROM reviews WHERE score = ?", sys.argv[2])
for row in cursor:
    print(re.sub('<[^<]+?>', '', row[1]))

