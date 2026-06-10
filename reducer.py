#!/usr/bin/env python3
import sys

current, count = None, 0

for line in sys.stdin:
    line = line.strip()
    if "\t" not in line:
        continue
    word, c = line.split("\t", 1)
    c = int(c)
    if word == current:
        count += c
    else:
        if current is not None:
            print(f"{current}\t{count}")
        current, count = word, c

if current is not None:
    print(f"{current}\t{count}")
