# PDF Digitizer (_It has a back button!!_)
Somewhat user-friendly tool to help parse out structured text from a pdf document



## Installation
```bash
conda env create -f environment.yml
conda activate pdf
pip install -e pdf_annotation
```

## Usage
1. First, you'll need some pdf documents to play with.
2. Once you have a folder with all of the pdfs you want to work with, launch the tool with ...
    ```bash
    jupyter lab notebooks
    ```
3. Open the notebook `DocTreeBuilder.ipynb`
4. Edit the path used as a parameter in the App initializer to point to your document directory. By default, this points to a folder in the root of this repo named `pdfs`
5. Run the first cell with `Shift`+`Enter`

## Features
### Cytoscape
`Folders`, `PDF Documents`, and `Sections` have a tab labeled `Cytoscape`. This runs a tfidf similarity calculation over all nodes beneath the selected item. I.e. if you select the root node, then all defined nodes will be included in the calculation. However, only those with a link to another node will be drawn (this is for speed, may change this in the future).
![image](https://user-images.githubusercontent.com/48299585/140627461-2685fe18-d918-461c-b678-86ca5f1f6a8e.png)

Selecting a node in the graph will highlight the node in the `DocTree`. Clicking the node in the `DocTree` will render the first page of the node.
![image](https://user-images.githubusercontent.com/48299585/140627583-0afea862-0b85-438c-b8b0-b6361f18d8e3.png)
