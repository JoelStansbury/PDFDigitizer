import re

wordBreak = re.compile("-\\n")

procs = [
    [wordBreak, ""]
]

def clean(s):
    for old, new in procs:
        re.sub(old,new)
    return s
