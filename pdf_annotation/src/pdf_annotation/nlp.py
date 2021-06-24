import re

wordBreak = re.compile("-\n")
lineBreak = re.compile("\n")
notAlphaNum = re.compile("[^a-zA-Z0-9 -]")

subs = [
    [wordBreak, ""],
    [lineBreak, " "],
    [notAlphaNum, ""]
]

def clean(s):
    """
    Remove unwanted characters
    """
    for old, new in subs:
        s=re.sub(old,new,s)
    return s