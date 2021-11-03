from ipytree import Node, Tree

from ..utils.update_json_data import clean

NODE_TYPES = {}
MAX_LEN = 20


class TreeWidget(Tree):
    def __init__(self, data=None):
        super().__init__()
        self.add_class("doc-tree")

        root = SectionNode(data)
        self.add_node(root)
        root.collapse_to(2)


class MyNode(Node):
    def __init__(self, data=None):
        super().__init__()

        if data:
            try:  # TODO: remove this when no longer needed
                self.load(data)
            except KeyError:
                clean(data)
                self.load(data)

    def load(self, data):
        for child in data["children"]:
            if not child["type"] in "labeltable":
                self.add_node(NODE_TYPES[child["type"]](child))

    def collapse_to(self, level):
        if level == 0:
            self.opened = False
            for n in self.nodes:
                n.opened = False
        else:
            self.opened = True
            for n in self.nodes:
                n.collapse_to(level-1)


class SectionNode(MyNode):
    __type__ = "section"

    def __init__(self, data=None):
        super().__init__(data)
        self.value = data.get("value","")
        ellipsis = "..." if len(self.value)>MAX_LEN else ""
        self.name = self.value[:MAX_LEN] + ellipsis

class TextNode(MyNode):
    __type__ = "text"

    def __init__(self, data=None):
        super().__init__(data)
        self.value = data.get("value","")
        ellipsis = "..." if len(self.value)>MAX_LEN else ""
        self.name = self.value[:MAX_LEN] + ellipsis
        self.icon = "align-left"

class ImageNode(MyNode):
    __type__ = "image"

    def __init__(self, data=None):
        super().__init__(data)
        self.value = data.get("value","")
        self.name = "img"
        self.icon = "image"

NODE_TYPES = {
    "section": SectionNode,
    "text": TextNode,
    "image": ImageNode,
}