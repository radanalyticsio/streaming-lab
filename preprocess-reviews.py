#!/usr/bin/env python

import sqlite3
import json
import sys
import re

usage = """ 
USAGE:  ./preprocess-reviews.py database.sqlite [rating] [limit]
Assumes that database.sqlite is a SQLite file with a table called "reviews" that has fields called "score" and "text".
An example such database is available from the public domain Amazon fine foods review dataset:

https://www.kaggle.com/snap/amazon-fine-food-reviews/

This script will extract all reviews with the specified rating, or 5 if no rating is supplied.
"""

connection = sqlite3.connect(sys.argv[1])
if len(sys.argv) < 2:
    rating = 5
    limit = None
elif len(sys.argv) < 3:
    rating = int(sys.argv[2])
    limit = None
else:
    rating = int(sys.argv[2])
    limit = int(sys.argv[3])

cursor = connection.execute("SELECT score, text FROM reviews WHERE score = ?", str(rating))
if limit is None:
    limit = cursor.rowcount

for row in cursor:
    print(re.sub('<[^<]+?>', '', row[1]))
    limit = limit - 1
    if limit == 0:
        break
