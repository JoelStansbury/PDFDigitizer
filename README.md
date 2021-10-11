# PDF Digitizer (_It has a back button!!_)
Somewhat user-friendly tool to help parse out structured text from a pdf document

https://www.dote.osd.mil/Publications/Annual-Reports/2020-Annual-Report/

```
Changelog:
1/8/2021: Added procedures for saving and reloading pages and documents
```
## Usage
[Youtube Video](https://www.youtube.com/watch?v=_My2JVHbknM&ab_channel=JoelS "Video Title")

## Notes
* You'll need `ipyevents` and `ipywidgets`
* Conda should be able to handle everything else. `pytesseract` should be ok, but it has been problematic in the past, maybe only if `Tesseract` is installed separately??? Should be fine.

## Installation
```bash
conda env create -f environment.yml
conda activate pdf
pip install -e pdf_annotation
```


## TODO:
### Relationship Modeling
- [ ] Draw arrows between bboxes
- [ ] Attach a predicate to arrows. Implementation should allow the reverse predicate to be defined
- [ ] Should probably add infrastructure for tool selection (textblock, relationship, ...)
### Searching Functionality
- [x] Store OCR results in database for later use.
- [ ] Store the bboxes as percentages of the full page, as opposed to pixel locations, so we can easily scale dpi.
- [x] Database meta-model
  ```
  fname: {
      "sizes":      [(page1width, page1height), ...],
      "texts":      [["text found from ocr from 1st bbox on page1","..."],[...],...],
      "categories": [[category of texts[0] from page 1, ...], ...],
      "textblocks": [[  coords of texts[0] from page 1, ...], ... ],
  }
  ```
- [ ] I don't think image_to_bboxes will give spaces, if this is the case then we'll need to make an alg to do this, which will probably suck. Or we can run image_to_string to get the splitable text used for doc retreival, then image_to_bboxes to get the backend charboxes used for searching.
- [ ] Image_to_boxes could also be run via subprocess to minimize the impact on user experience.
