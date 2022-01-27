# This script (Work in Progress) contains a pipeline for generating
# trainable data from user input. So far (12/13/2021) the pipeline only
# adds an identifier to words extracted from Tesseract indicating wether or
# not the word is part of a section heading. There is not yet any mechanism
# for indicating the position of the section relative to the document tree.
# The current plan is to pass this data into an LSTM to predict the hierarchy.

import json
from pathlib import Path

import numpy as np
import pytesseract as tess
import pandas as pd

from ..widgets.new_ipytree import MyNode
from .image_utils import rel_2_pil, pil_2_rel, ImageContainer
from .nlp import levenshtein_distance

def get_ocr_data(path):
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
        df["width"] = df["width"].astype(int)
        df["height"] = df["height"].astype(int)
        
        df["block_num"] = df["block_num"].astype(int)
        # Remember page num
        df["page"] = i
        df["page_width"] = img.width
        df["page_height"] = img.height
        rows += df.to_dict("records")
    return pd.DataFrame(rows)


def get_text_blocks(path):
    df = get_ocr_data(path)
    groups = df.groupby(by=["page","block_num"]).groups
    keys = sorted(list(groups.keys()))
    text_blocks = []
    for k in keys:
        word_idxs = groups[k]
        tmp = df.iloc[word_idxs]
        w = tmp.to_dict("records")[0]
        x1 = min(tmp["left"])
        y1 = min(tmp["top"])
        x2 = max(tmp["left"] + tmp["width"])
        y2 = max(tmp["top"] + tmp["height"])
        coords = pil_2_rel([x1,y1,x2,y2], w["page_width"], w["page_height"])
        text = " ".join(tmp["text"])
        text_blocks.append({"value":text,"page":w["page"],"coords":coords})
    return text_blocks


def do_other_stuff():
    
    path = Path("../pdfs/ARMY/2020avcad.pdf")

    with path.with_suffix(".json").open("r") as f:
        children = json.load(f)
    node = MyNode(path=path, data={"type":"pdf", "children":children})
    sections = [x for x in node.dfs() if x._type == "section"]

    df = get_ocr_data(path)

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