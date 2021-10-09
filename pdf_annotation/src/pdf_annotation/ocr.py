import pytesseract
from pytesseract import Output

from .nlp import clean


class Base:


class WordBoxes(Base):
    """
    Returns cleaned words with bboxes.
    Does not preserve newline characters or punctuation.
    """
    def __init__(self, img, bbox=None):
        if bbox:
            x1,y1,x2,y2 = bbox
            x1, x2 = sorted([x1,x2])
            y1, y2 = sorted([y1,y2])
            coords = x1,y1,x2,y2
            img = img.crop(coords)
        d = pytesseract.image_to_data(img, output_type=Output.DICT)
        words = []
        wordboxes = []
        n_boxes = len(d['level'])
        for i in range(n_boxes):
            word = strip(clean(d["text"][i]))
            if word != '':
                words.append(word)
                (x1, y1, w, h) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
                x2 = x1+w
                y2 = y1+h
                wordboxes.append((x1,y1,x2,y2))
        return words, wordboxes

            