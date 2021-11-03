from ipywidgets import Tab, HTML

class NodeDetail(Tab):
    def __init__(self):
        super().__init__()
        self.children = [HTML("Select a section for inspection")]
        self.set_title(0, "Info")