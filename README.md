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
