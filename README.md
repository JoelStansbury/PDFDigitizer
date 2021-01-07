# PDF Digitizer
Somewhat user-friendly tool to help parse out structured text from a pdf document

## Usage
[Youtube Video](https://www.youtube.com/watch?v=_My2JVHbknM&ab_channel=JoelS "Video Title")

## Notes
* You'll need `ipyevents` and `ipywidgets`
* Conda should be able to handle everything else. `pytesseract` should be ok, but it has been problematic in the past, maybe only if `Tesseract` is installed separately??? Should be fine.

## Installation
```bash
conda env create -f environment.yml
jupyter labextension install @jupyter-widgets/jupyterlab-manager
jupyter labextension install @jupyter-widgets/jupyterlab-manager ipyevents
jupyter labextension install @jupyter-widgets/jupyterlab-manager ipycanvas
pip install -e pdf_annotation
```


## TODO:
### Searching Functionality
* Keep a set of all words in the doc for quick doc retreival
* I don't think image_to_bboxes will give spaces, if this is the case then we'll need to make an alg to do this, which will probably suck. Or we can run image_to_string to get the splitable text used for doc retreival, then image_to_bboxes to get the backend charboxes used for searching.
* Image_to_boxes could also be run via subprocess to minimize the impact on user experience.
* Store the bboxes as percentages of the full page, as opposed to pixel locations, so we can easily scale dpi.

Database meta-model
```
Database of docs
  filename                  (path())
  words                     sum([tb.words for tb in data], set())
  data:
    text_blocks
        page_num
        category            (label assigned in the parsing tool)
        bbox                [x1, y1, x2, y2]
        words               (set() of words within)
        content:
          character_string  (concated chars found by image_to_bboxes)
          bboxes            (2Darray (Nx4) [[x1, y2, x2, y2],...], where N=len(character_string))
```

