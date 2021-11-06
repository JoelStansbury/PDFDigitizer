from ipywidgets import Tab, HTML, VBox, Button, HBox, Textarea, Label
from traitlets import Unicode, Instance, observe, link, List
from .new_ipytree import MyNode
import spacy

nlp = spacy.load("en_core_web_lg")


NODE_KWARGS = {
    "folder": [0],
    "pdf": [1,5],
    "section": [1,5],
    "text": [3, 4],
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
            TextInsights(node),
            SectionInsights(node),
        ]
        self.titles = [
            "Info",
            "Subsection Tools",
            "Image Tools",
            "Text Block Tools",
            "Insights",
            "Insights",
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


class TextInsights(MyTab):
    def __init__(self, node):
        super().__init__()
        self.node = node
        self.ents = HTML()
        self.children = [
            VBox(
                [
                    HBox(
                        [
                            Label("Entities: "),
                            self.ents,
                        ]
                    ),
                ]
            )
        ]

    def refresh(self, _=None):
        self.ents.value = "<br>".join(
            set([str(x) for x in nlp("".join([x["value"] for x in self.node.content])).ents])
        )

    def set_node(self, node):
        super().set_node(node)
        self.refresh()

from collections import defaultdict
class SectionInsights(MyTab):
    def __init__(self, node):
        super().__init__()
        self.node = node
        self.refresh_btn = Button(icon="refresh")
        self.refresh_btn.add_class("eris-small-btn")
        self.refresh_btn.on_click(self.refresh)
        self.ents = HTML()
        self.children = [
            VBox(
                [
                    # self.refresh_btn,
                    HBox(
                        [
                            Label("Entities: "),
                            self.ents,
                        ]
                    ),
                ]
            )
        ]
    def refresh(self, _=None):
        dd = defaultdict(int)
        for node in self.node.dfs():
            if node._type == "text":
                for ent in nlp(" ".join([x["value"].strip() for x in node.content])).ents:
                    dd[str(ent).strip().lower()]+=1
        results = sorted(list(dd.items()), key=lambda x: x[1], reverse=True)[:5]
        view = "".join([f"<tr><td>{x[0]}</td><td>{x[1]}</td></tr>" for x in results])
        self.ents.value = f"<table>{view}<tr><td>...</td></tr></table>"

    def set_node(self, node):
        super().set_node(node)
        self.refresh()

