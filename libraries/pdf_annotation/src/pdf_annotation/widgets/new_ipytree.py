from ipytree import Node, Tree
from collections import defaultdict
from pathlib import Path
from traitlets import Unicode, Instance, observe, link, List

from ..utils.update_json_data import clean
from ..utils.image_utils import rel_2_canvas

NODE_TYPES = {}
MAX_LEN = 20


def truncate(s: str):
    ellipsis = "..." if len(s) > MAX_LEN else ""
    return s[:MAX_LEN] + ellipsis


NODE_KWARGS = {
    "folder": {
        "icon": "folder",
    },
    "pdf": {
        "icon": "file-pdf",
    },
    "section": {
        "icon": "indent",
    },
    "text": {
        "icon": "align-left",
    },
    "image": {
        "icon": "image",
    },
}


def node_factory(directory):
    tree = lambda: defaultdict(tree)
    path = Path(directory)
    root_parts = path.parts
    data = tree()
    for x in path.rglob("*.pdf"):
        cursor = data["children"]
        c_path = path
        for part in x.parts[len(root_parts) :]:
            c_path = c_path / part
            cursor = cursor[part]

            # Node Attributes
            cursor["path"] = c_path
            set_node_type(cursor, c_path)
            cursor = cursor["children"]

    data["type"] = "folder"
    data["path"] = path
    return MyNode(directory, data)


def set_node_type(cursor, c_path):
    if c_path.is_file():
        if c_path.suffix.lower() == ".pdf":
            cursor["type"] = "pdf"
            if c_path.with_suffix(".json").exists():
                with c_path.with_suffix(".json").open("r") as f:
                    cursor["children"] = json.load(f)
    else:
        cursor["type"] = "folder"


class TreeWidget(Tree):
    def __init__(self, directory: str):
        super().__init__(multiple_selection=False)
        self.add_class("eris-doc-tree")
        self.root = node_factory(directory)
        self.add_node(self.root)
        self.root.collapse_to(2)


class MyNode(Node):
    content = List(default_value=[]).tag(sync=True)

    def __init__(
        self,
        label: str,
        data=None,
    ):
        super().__init__()
        self._type = data["type"]
        self._path = data["path"]
        self.label = label

        # Visual aspects of the node
        self.name = truncate(self.label)
        self.icon = NODE_KWARGS[self._type]["icon"]

        if not data is None:
            for label, d in data["children"].items():
                self.add_node(MyNode(label, d))

    def add_content(self, item):
        self.content = self.content + [item]

    def collapse_to(self, level):
        if level == 0:
            self.opened = False
            for n in self.nodes:
                n.opened = False
        else:
            self.opened = True
            for n in self.nodes:
                n.collapse_to(level - 1)

    def get_boxes(self, page_num, w, h, include_children=False):
        bboxes = [
            (rel_2_canvas(c["coords"], w, h), self._type)
            for c in self.content
            if c["page"] == page_num
        ]

        if include_children:
            for child in self.nodes:
                bboxes += child.get_boxes(page_num, w, h, include_children)
        return bboxes
