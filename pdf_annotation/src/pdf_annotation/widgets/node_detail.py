from ipywidgets import Tab, HTML, VBox, Button, HBox, Textarea, Output, FloatSlider, Checkbox
from IPython.display import display
from spacy.tokens import token
from traitlets import Unicode, Instance, observe, link, List
from collections import defaultdict

import matplotlib.colors as mcolors
from random import shuffle
import pandas as pd
import spacy
import layoutparser as lp
import pytesseract as tess

from ..widgets.new_ipytree import MyNode
from .new_ipytree import MyNode, NODE_REGISTER
from ..utils.nlp import tfidf_similarity
from ..utils.image_utils import ImageContainer, pil_2_rel
from ..utils.generate_training_data import get_text_blocks
from .dataframe_widget import DataFrame

nlp = spacy.load("en_core_web_lg")
lp_model = lp.models.PaddleDetectionLayoutModel('lp://PubLayNet/ppyolov2_r50vd_dcn_365e/config')


NODE_KWARGS = {
    "folder": [0,5],
    "pdf": [1,6,5,4],
    "section": [1,5],
    "text": [3,4],
    "image": [2],
}


class NodeDetail(Tab):
    def __init__(self, node):
        super().__init__()
        self.node = node
        self.tabs = [
            HTML("Select a section for inspection"),
            SubsectionTools(node),
            ImageTools(node),
            TextBlockTools(node),
            SpacyInsights(node),
            Cytoscape(node),
            AutoTools(node),
            # SectionInsights(node),
            # Summary(node),
        ]
        self.titles = [
            "Info",
            "Subsection Tools",
            "Image Tools",
            "Text Block Tools",
            "Spacy",
            "Cytoscape",
            "AutoTools",
            # "Insights",
            # "Summary",
        ]

        self.set_title(0, "Info")

    def set_node(self, node):
        self.node = node
        indexes = NODE_KWARGS[self.node._type]
        children = []
        for i in indexes:
            children.append(self.tabs[i])
            if getattr(self.tabs[i], "set_node", False):
                self.tabs[i].set_node(node)
        self.children = children
        for i, j in enumerate(indexes):
            self.set_title(i, self.titles[j])


class MyTab(HBox):
    def __init__(self):
        super().__init__()
        # TODO: when I made this init I thought this would only be run once, 
        # that is not the case. Refactor this to only run once.
        self.delete_btn = Button(
            icon="trash",
            tooltip="Delete this node and all of its children",
        )
        self.delete_btn.style.text_color = "red"
        self.delete_btn.add_class("eris-small-btn-red")
        self.delete_btn.on_click(self.delete_node)

    def add_node(self, btn):
        new_node = MyNode(
            data={"type": self._types[btn], "path": self.node._path, "children": {}},
            parent=self.node._id
        )
        self.node.add_node(new_node)
        new_node.selected = True
        self.node.selected = False

    def set_node(self, node):
        self.node = node

    def delete_node(self, _):
        self.node.delete()


class SubsectionTools(MyTab):
    def __init__(self, node):
        super().__init__()
        self.node = node

        text = Button(
            icon="align-left",
            tooltip="Add a new text node",
        )
        text.on_click(self.add_node)
        text.add_class("eris-small-btn")

        section = Button(
            icon="indent",
            tooltip="Add a subsection",
        )
        section.on_click(self.add_node)
        section.add_class("eris-small-btn")

        image = Button(
            icon="image",
            tooltip="Add an image",
        )
        image.on_click(self.add_node)
        image.add_class("eris-small-btn")

        self._types = {text: "text", section: "section", image: "image"}

        self.children = [section, text, image, self.delete_btn]


class ImageTools(MyTab):
    def __init__(self, node):
        super().__init__()
        self.node = node

        text = Button(
            icon="align-left",
            tooltip="Add a description for the image",
        )
        text.on_click(self.add_node)
        text.add_class("eris-small-btn")

        self._types = {
            text: "text",
        }

        self.children = [text, self.delete_btn]


class TextBlockTools(MyTab):
    content = List(default_value=[]).tag(sync=True)

    def __init__(self, node):
        super().__init__()
        self.node = node
        self.link = link((self.node, "content"), (self, "content"))

    @observe("content")
    def redraw_content(self, _=None):
        self.children = [
            VBox([Textarea(x["value"]) for x in self.node.content]),
            self.delete_btn,
        ]

    def set_node(self, node):
        self.link.unlink()
        self.node = node
        self.link = link((self.node, "content"), (self, "content"))
        self.redraw_content()

# Requires Spacy model
class SpacyInsights(MyTab):
    def __init__(self, node):
        super().__init__()

        self.refresh_btn = Button(icon="refresh")
        self.refresh_btn.add_class("eris-small-btn")
        self.refresh_btn.on_click(self.refresh)

        self.utils = HBox(
            [
                self.refresh_btn
            ]
        )
        if nlp is None:
            self.utils = HTML("Spacy model not found. Do 'pip install spacy && python -m spacy download en_core_web_lg'")
        self.children = [self.utils]

    def refresh(self, _=None):
        doc = nlp(self.node.stringify())
        ents = defaultdict(int)
        for ent in doc.ents:
            ents[(ent.text, ent.label_)] += 1
        ent_rows = []
        for k,v in ents.items():
            ent_rows.append({"Entity":k[0], "Label":k[1], "Count":v})
        ent_rows.sort(key=lambda x: x["Count"], reverse=True)
        ents = pd.DataFrame(ent_rows)
        token_df = pd.DataFrame([
            {
                "TEXT": token.text,
                "LEMMA": token.lemma_,
                "POS": token.pos_,
                "TAG": token.tag_,
                "DEP": token.dep_,
            } for token in doc
        ])
        
        self.children = [
            VBox([
                self.utils,
                DataFrame(ents),
                DataFrame(token_df)
            ])
        ]

# class SectionInsights(MyTab):
#     def __init__(self, node):
#         super().__init__()
#         self.node = node
#         self.refresh_btn = Button(icon="refresh")
#         self.refresh_btn.add_class("eris-small-btn")
#         self.refresh_btn.on_click(self.refresh)
#         self.ents = HTML()
#         self.children = [
#             VBox(
#                 [
#                     self.refresh_btn,
#                     HBox(
#                         [
#                             Label("Entities: "),
#                             self.ents,
#                         ]
#                     ),
#                 ]
#             )
#         ]
#     def refresh(self, _=None):
#         dd = defaultdict(int)
#         for node in self.node.dfs():
#             if node._type == "text":
#                 for ent in nlp(" ".join([x["value"].strip() for x in node.content])).ents:
#                     dd[str(ent).strip().lower()]+=1
#         results = sorted(list(dd.items()), key=lambda x: x[1], reverse=True)[:5]
#         view = "".join([f"<tr><td>{x[0]}</td><td>{x[1]}</td></tr>" for x in results])
#         self.ents.value = f"<table>{view}<tr><td>...</td></tr></table>"


from ipycytoscape import CytoscapeWidget

class Cytoscape(MyTab):
    def __init__(self, node):
        super().__init__()
        self.node = node
        self.refresh_btn = Button(
            icon="refresh",
            tooltip="Recompute network"
        )
        self.refresh_btn.add_class("eris-small-btn")
        self.refresh_btn.on_click(self.refresh)
        self.slider = FloatSlider(0.4, min=0,max=1)
        self.config_btn_recursive = Checkbox(True, description="Recursive")
        self.confib_btn_intradoc = Checkbox(True, description="Intra-document connections")
        self.children = [
            VBox(
                [
                    self.refresh_btn,
                    self.slider,
                    self.config_btn_recursive,
                    self.confib_btn_intradoc,
                    HTML("Hit refresh to generate cytoscape")
                ]
            )
        ]
    def on_node_click(self, event):
        NODE_REGISTER[event["data"]["id"]].selected=True

    def refresh(self, _=None):
        
        self.children = [
            VBox(
                [
                    self.refresh_btn,
                    self.slider,
                    self.config_btn_recursive,
                    self.confib_btn_intradoc,
                    HTML("loading...")
                ]
            )
        ]
        if self.config_btn_recursive.value:
            gen = self.node.dfs()
            next(gen)  # skip first
            docs = {
                node: node.stringify()
                for node in gen
            }
        else:
            docs = {
                node: node.stringify()
                for node in self.node.nodes
            }

        for doc, v in list(docs.items()):
            if v == '' or doc.label=="":
                docs.pop(doc)
        


        sim = tfidf_similarity(docs)
        if len(sim) == 0:
            self.children = [
                VBox(
                    [
                        self.refresh_btn,
                        self.slider,
                        self.config_btn_recursive,
                        self.confib_btn_intradoc,   
                        HTML("Not enough nodes")
                    ]
                )
            ]
            return

        colors = list(mcolors.cnames)  #[x.split(":")[1] for x in mcolors.TABLEAU_COLORS]
        shuffle(colors)

        files = set([x._path for x in sim])
        cmap = {k: colors[i] for i,k in enumerate(files)}

        g_edges = []
        pairs = set()
        nodes_with_edges = set()
        for source, edges in sim.items():
            for edge in edges:
                target, weight = edge
                if weight>self.slider.value and source._id!=target._id:
                    pair = tuple(sorted([source._id, target._id]))
                    if not pair in pairs:
                        if self.confib_btn_intradoc.value:
                            nodes_with_edges.add(source)
                            nodes_with_edges.add(target)
                            g_edges.append({"data":{"source":source._id, 'target':target._id}})
                            pairs.add(pair)
                        elif source._path != target._path:
                            nodes_with_edges.add(source)
                            nodes_with_edges.add(target)
                            g_edges.append({"data":{"source":source._id, 'target':target._id}})
                            pairs.add(pair)

        graph_dict = {
            "nodes":[
                {"data":{"id":node._id, "color":cmap[node._path], "name":node.label}} 
                for node in nodes_with_edges
            ],
            "edges":g_edges
        }
        

        cyto = CytoscapeWidget()
        cyto.graph.add_graph_from_json(graph_dict)
        cyto.on("node","click", self.on_node_click)
        

        self.children = [
            VBox(
                [
                    self.refresh_btn,
                    self.slider,
                    self.config_btn_recursive,
                    self.confib_btn_intradoc,
                    cyto
                ]
            )
        ]


        cyto.set_style([{
            'selector': 'node',
            'css': {
                'content': 'data(name)',
                'text-valign': 'center',
                'color': 'white',
                'text-outline-width': 2,
                'text-outline-color': 'black',
                'background-color': 'data(color)'
            }
            },
            {
            'selector': ':selected',
            'css': {
                'background-color': 'data(color)',
                'line-color': 'black',
                'target-arrow-color': 'black',
                'source-arrow-color': 'black',
                'text-outline-color': 'black'
            }}
            ])


# class Summary(MyTab):
#     def __init__(self, node):
#         super().__init__()

#         self.refresh_btn = Button(icon="refresh")
#         self.refresh_btn.add_class("eris-small-btn")
#         self.refresh_btn.on_click(self.refresh)

#         self.utils = HBox(
#             [
#                 self.refresh_btn
#             ]
#         )
#         self.children = [self.utils]

#     def refresh(self, _=None):
#         summary = summarize(self.node.stringify())
        
#         self.children = [
#             VBox([
#                 self.utils,
#                 HTML(summary),
#             ])
#         ]


class AutoTools(MyTab):
    def __init__(self, node):
        super().__init__()

        tesseract_btn = Button(
            description="Text Only",
            tooltip="Detect and parse text-blocks",
        )
        layoutparser_btn = Button(
            description="Parse Document",
            tooltip="Detect and parse (sections, textblocks, and images)",
        )
        tesseract_btn.on_click(self.extract_text)
        layoutparser_btn.on_click(self.extract_layout)
        self.progress = HTML()
        self.children = [VBox([layoutparser_btn,tesseract_btn,self.progress])]

    def extract_text(self, _):
        self.progress.value = "Detecting Textblocks: ..."
        for tb in get_text_blocks(self.node._path):
            self.node.add_node(
                MyNode(
                    data={"type": "text", "path": self.node._path, "children": {}, "content": [tb]},
                    parent=self.node._id
                )
            )
        self.progress.value = ""
    def extract_layout(self, _):
        path = self.node._path
        imgs = ImageContainer(path, bulk_render=False)
        for page_num, img in enumerate(imgs):
            self.progress.value = f"LayoutParser: {page_num+1}/{imgs.info['Pages']}"
            layout = lp_model.detect(img)
            for block in layout:
                x1,y1,x2,y2 = [int(x) for x in block.coordinates]
                coords = (x1,y1,x2+20,y2+5)
                text = tess.image_to_string(img.crop(coords)).strip()
                rel_coords = pil_2_rel(coords, img.width, img.height)
                content = [{"value":text,"page":page_num,"coords":rel_coords}]
                if block.type == "Title":
                    self.node.add_node(
                        MyNode(
                            label=text,
                            data={
                                "type": "section",
                                "path": self.node._path,
                                "children": {},
                                "content": content,
                                "label":text
                            },
                            parent=self.node._id
                        )
                    )
                elif block.type in ["List", "Text"]:
                    self.node.add_node(
                        MyNode(
                            data={
                                "type": "text",
                                "path": self.node._path,
                                "children": {},
                                "content": content
                            },
                            parent=self.node._id
                        )
                    )
                elif block.type in ["Figure", "Table"]:
                    self.node.add_node(
                        MyNode(
                            data={
                                "type": "image",
                                "path": self.node._path,
                                "children": {},
                                "content": [
                                    {
                                        "value":None,
                                        "page":page_num,
                                        "coords":pil_2_rel(block.coordinates, img.width, img.height)
                                    }
                                ]
                            },
                            parent=self.node._id
                        )
                    )
            self.progress.value = ""

