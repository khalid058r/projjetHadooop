#!/usr/bin/env python3
import sys
import re

for line in sys.stdin:
    for word in re.findall(r"[a-zà-ÿ]{3,}", line.lower()):
        print(f"{word}\t1")
