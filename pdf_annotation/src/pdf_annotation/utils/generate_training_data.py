import json
from pathlib import Path

import numpy as np
import pytesseract as tess
import pandas as pd

from ..widgets.new_ipytree import MyNode
from .image_utils import rel_2_pil, ImageContainer
from .nlp import levenshtein_distance

path = Path("../pdfs/ARMY/2020avcad.pdf")

with path.with_suffix(".json").open("r") as f:
    children = json.load(f)
node = MyNode(path=path, data={"type":"pdf", "children":children})
sections = [x for x in node.dfs() if x._type == "section"]

imgs = ImageContainer(path)
rows = []
for i,img in enumerate(imgs):
    # Pass full page into Tesseract
    data = tess.image_to_data(img, config="--psm 1")
    # Parse output into dataframe
    p_rows = [line.split("\t") for line in data.split("\n")]
    df = pd.DataFrame(data = p_rows[1:-1], columns = p_rows[0])
    # Remove whitespaces TODO: keep this whitespace in the dataset
    df = df[df["conf"]!="-1"]
    df["left"] = df["left"].astype(int)
    df["top"] = df["top"].astype(int)
    # Remember page num
    df["page"] = i
    rows += df.to_dict("records")

df = pd.DataFrame(rows)

i = 1
coords = sections[i].content[0]["coords"]
label = sections[i].content[0]["value"]
page = sections[i].content[0]["page"]
w = imgs[page].width
h = imgs[page].height
left, top, right, bottom = rel_2_pil(coords, w, h)
b_height = bottom - top
first_word = label.split()[0]
score = (
    (
        100 * (abs(df["top"]-top)) / b_height
        + (abs(df["left"]-left))
    ) 
    + (100 * np.array([levenshtein_distance(x, first_word) for x in df["text"]]))
    + (10000 * np.array([x != page for x in df["page"]]))
)

print(label)

start = score.argmin()
# NOTE: Possible improvement could involve adding tokens until levenshtein_distance jumps up
df.iloc[start:start+len(label.split())]

# TODO: Add visual features for font
# TODO: Add indicator for going up/down the tree