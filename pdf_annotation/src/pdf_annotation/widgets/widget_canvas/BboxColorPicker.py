import ipywidgets as ipyw
from traitlets import Unicode, Int, link, observe, Bool

class BboxColor(ipyw.HBox):
    value = Unicode().tag(sync=True)
    name = Unicode().tag(sync=True)
    disabled = Bool().tag(sync=True)

    def __init__(self, name="", value="black", **kwargs):
        super().__init__()

        self.color_picker = ipyw.ColorPicker(concise=True)
        self.label = ipyw.Text()

        link((self.color_picker, "value"), (self, "value"))
        link((self.color_picker, "disabled"), (self, "disabled"))
        link((self.label, "value"), (self, "name"))
        link((self.label, "disabled"), (self, "disabled"))

        self.name = name
        self.value = value

        self.children = [self.label, self.color_picker]

class BboxColorPicker(ipyw.VBox):
    categories = []
    buttons = []
    hboxes = []
    btn_idx = {}

    add_group_button = ipyw.Button(icon="plus")
    selection = Int().tag(sync=True)
    value = Unicode().tag(sync=True)
    name = Unicode().tag(sync=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.categories = []
        self.add_group_button.on_click(self.add_group)
        self.add_group_button.click()
        self.categories[0].name="Default"
        self.children = self.hboxes + [self.add_group_button]
        # self.selection = 0
        
    
    def add_group(self, _):
        cat = BboxColor()
        btn = ipyw.Button(icon="circle")
        hbox = ipyw.HBox([btn, cat])

        idx = len(self.categories)
        cat.idx = idx
        btn.on_click(self.cat_click)
        self.btn_idx[btn] = idx

        self.hboxes.append(hbox)
        self.categories.append(cat)
        self.buttons.append(btn)
        self.children = self.hboxes + [self.add_group_button]

        cat.observe(self.cat_update)
        self.selection = idx # select the new group

    def cat_update(self, change):
        if change["owner"].idx == self.selection:
            self.value = change["owner"].value
            self.name = change["owner"].name


    def cat_click(self, btn):
        self.selection = self.btn_idx[btn]

    @observe("selection")
    def select(self, change):
        self.buttons[change["old"]].icon = "none"
        self.buttons[change["new"]].icon = "circle"
        self.value = self.categories[change["new"]].value
        self.name = self.categories[change["new"]].name