from time import sleep
import re

from ipywidgets import VBox, HTML, Accordion, Button, HBox, Textarea, Text
from traitlets import observe, link, Any, Int, HasTraits, Unicode



class DataNode:


    def __init__(self, label=""):
        if isinstance(label, dict):
            self.from_dict(label)
        else:
            self.label = " ".join(label.split())
            self.children = []
            self.content = []


    def add(self, *args, **kwargs):
        self.children.append(DataNode(*args, **kwargs))


    def append(self, item):
        self.content.append(item)


    def rename(self, label):
        self.label = label


    def __getitem__(self, path):
        if isinstance(path, int):
            return self.children[path]
        if len(path) == 1:
            return self.children[path[0]]
        return self.children[path[0]][path[1:]]


    def __repr__(self):
        return self.__show()


    def __show(self, prefix=""):
        """Implements Depth-First-Search to construct a string of Node labels"""
        
        s = f"{prefix}{self.label}"
        for c in self.children:
            s += f"\n{c.__show(prefix + '  ')}"
        return s


    def to_dict(self, root=True):
        r = {
            "label": self.label,
            "children":[c.to_dict(False) for c in self.children],
            "content": self.content
        }
        return r


    def from_dict(self, d):
        self.label = d["label"]
        self.content = d["content"]
        self.children = [DataNode().from_dict(c) for c in d["children"]]
        return self


    def walk(self, path=None):
        if path is None:
            path = []
        yield path, self
        for i, child in enumerate(self.children):
            yield from child.walk(path+[i])


    def search(self, label):
        for path, node in self.walk():
            if node.label == label:
                return path, node
        return None, None


    def to_string(self, include_labels=True):
        if include_labels:
            s = "".join([c["value"] for c in self.content if c["type"] == "text" or c["type"] == "label"])
        else:
            s = "".join([c["value"] for c in self.content if c["type"] == "text"])
        
        for c in self.children:
            s += c.to_string(include_labels)
        return s

class TreeWidget(VBox):
    selected_index = Any().tag(sync=True)
    delete_me = Int(-1).tag(sync=True)
    label = Unicode().tag(sync=True)


    def __init__(self, node, idx=0, on_selection_change=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # This value is used to tell the parent which node it should delete
        # in the event that the delete button is clicked
        self.idx = idx

        # Any additional procedure to run when a new section has been selected
        self.on_selection_change = on_selection_change

        # This is a reference to the actual data node which stores info about
        # the section (text, coordinates, ...)
        self.node = node
        self.label = node.label.strip()
        # Accordion selection tool for all of this node's subtrees
        self.subtrees = Accordion(
            [TreeWidget(n,i,on_selection_change=self.on_selection_change) for i,n in enumerate(self.node.children)]
        )

        # Set the label for each accordion item (cannot be done on init)
        # and set up the `delete_me` connection
        for i, n in enumerate(self.node.children):
            self.subtrees.set_title(i, n.label)
            self.subtrees.children[i].observe(
                self.delete_subtree, 
                names=["delete_me",]
            )
            self.subtrees.children[i].observe(
                self.rename_selected,
                names=["label",]
            )
        
        # Interaction Buttons for editing the node
        self.add_section_btn = Button(icon = "plus")
        self.view_btn = Button(description = "View Content")
        self.delete_btn = Button(icon = "remove")
        
        # Button events
        self.add_section_btn.on_click(self.add_subtree)
        self.view_btn.on_click(self.toggle_view)
        self.delete_btn.on_click(self._delete_me)
        
        # Fill this accordion item (the root node is not in an accordion)
        self.controls = HBox(
            [
                self.add_section_btn,
                self.view_btn,
                self.delete_btn,
            ]
        )
        
        # By default, the accordion selects the 0th element on init.
        # In our usage, this corresponds to taking the left-most path until
        # a leaf is found. We only want to show controls for the active node,
        # so unless this is a leaf, we know that we should not draw the controls.
        # All other leafs don't matter as they are hidden because their parent
        # is not expanded (i.e. the parent was not the 0th element of its level).
        if self.node.children:
            self.children = [self.subtrees]
        else:
            self.children = [self.subtrees, self.controls]
        
        # We also could have used 
        # self.subtrees.observe(self.set_btn_visibility, names=["selected_index"])
        # but this is marginally more convenient for finding the selected node
        # from the root level. 
        link((self.subtrees, "selected_index"), (self, "selected_index"))

        self.content = VBox()
        for item in self.node.content:
            self.add_content(item, forward=False)


    @observe("selected_index")
    def set_btn_visibility(self, change):
        "Hide button when a subsection is selected"

        if change["new"] is None:
            self.children = [self.subtrees, self.controls]
            self.do_on_select()
        else:
            self.children = [self.subtrees]
            if len(self.subtrees.children) > change["new"]:
                self.subtrees.children[change["new"]].do_on_select()

  
    def do_on_select(self):
        if self.selected_index is None:
            if self.on_selection_change is not None:
                self.on_selection_change(self.node)
        else:
            if len(self.subtrees.children) > self.selected_index:
                self.subtrees.children[self.selected_index].do_on_select()


    def add_subtree(self, _):
        self.node.add("")
        N = len(self.subtrees.children)
        
        new_widget = TreeWidget(self.node[-1], N, on_selection_change=self.on_selection_change)
        new_widget.observe(self.delete_subtree,names=["delete_me",])
        new_widget.observe(self.rename_selected,names=["label",])
        
        self.subtrees.children = list(self.subtrees.children) + [new_widget]
        self.subtrees.set_title(N, "")
        self.subtrees.selected_index = N


    def add_content(self, item, forward=True):
        if item["type"] == "text":
            w = Textarea(item["value"],layout={"width":"95%"})
            w.observe(self.on_content_edit, names=["value",])
            self.content.children = list(self.content.children) + [w]
        elif item["type"] == "label":
            w = Text(item["value"], description="Label:")
            w.observe(self.on_content_edit, names=["value",])
            self.content.children = list(self.content.children) + [w]
        else:
            self.content.children = list(self.content.children) + [
                HTML(f"({item['type']}) Cannot display this content")
                ]
        
        if forward:
            self.node.content.append(item)


    def on_content_edit(self, _):
        for i,w in enumerate(self.content.children):
            if getattr(w, "value", None) == _["new"]:
                self.node.content[i]["value"] = w.value
                if self.node.content[i]["type"] == "label":
                    self.label = w.value


    def pop(self):
        self.content.children = list(self.content.children)[:-1]
        self.node.content.pop() 


    def toggle_view(self, _):
        if _.description == "View Content":
            _.description = "View Subtrees"
            self.children = [self.content, self.controls]
        else:
            _.description = "View Content"
            self.children = [self.subtrees, self.controls]


    def rename_selected(self, label):
        if isinstance(label, dict):
            label = label["new"]
        path = self.path_to_selected()
        self.node[path].label = label
        leaf = path.pop()
        if path:
            self[path].subtrees.set_title(leaf, label)
        else:
            self.subtrees.set_title(leaf, label)


    def _delete_me(self, _):
        self.delete_me = self.idx


    def __getitem__(self, path):
        """Not really used anywhere"""
        if isinstance(path, int):
            return self.subtrees.children[path]
        if len(path) == 1:
            return self.subtrees.children[path[0]]
        return self.subtrees.children[path[0]][path[1:]]


    def delete_subtree(self, event):
        n = event["new"]
        self.node.children.pop(n)
        tmp = list(self.subtrees.children)
        for c in tmp[n:]:
            c.idx = c.idx - 1
        tmp.pop(event["new"])
        self.subtrees.children = tmp
        for i,w in enumerate(self.subtrees.children):
            self.subtrees.set_title(i, w.label)



    def path_to_selected(self):
        if self.selected_index == None:
            return []
        return [self.selected_index] + self.subtrees.children[self.selected_index].path_to_selected()


    def selected(self):
        if self.path_to_selected():
            return self[self.path_to_selected()]
        return self