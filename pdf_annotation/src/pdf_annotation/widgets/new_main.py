import io
from pathlib import Path
import json

import ipywidgets as ipyw
import pytesseract as tess
from traitlets import observe

from .widget_canvas import PdfCanvas
from .tree import DataNode, TreeWidget
from ..image_utils import fit, scale, pil_2_widget, ImageContainer, scale_coords


class App(ipyw.HBox):

    def __init__(self, indir, bulk_render=False):
        super().__init__()

        self.bulk_render = bulk_render
        self.file_dd = ipyw.Dropdown(
            options=[
                (str(x).replace("\\","/"), x) 
                for x in Path(indir).rglob("*.pdf")
                ]
            )

        self.file_dd.observe(self.new_file, "value")

        self.ch, self.cw = 1000, 900
        self.canvas = PdfCanvas(height=self.ch, width=self.cw)
        self.canvas.active_layer.on_mouse_up(self.parse_current_selection)

        self.prev_page_button = ipyw.Button(
            icon="arrow-left",
            layout={"width":"50px"}
        )
        self.prev_page_button.on_click(self.prev_page)
        self.undo_button = ipyw.Button(
            icon="undo",
            layout={"width":"50px"}
        )
        self.undo_button.on_click(self.undo)
        self.next_page_button = ipyw.Button(
            icon="arrow-right",
            layout={"width":"50px"}
        )
        self.next_page_button.on_click(self.next_page)
        self.save_page_button = ipyw.Button(
            icon="save",
            layout={"width":"50px"}
        )
        self.save_page_button.on_click(self.save)
        self.draw_bboxes_checkbox = ipyw.Checkbox(
            value=False,
            description="Show all Boxes",
            tooltip="Draws bounding boxes over selected section. Also acts as a hyperlink to jump to the start of the selected section."
        )
        self.draw_bboxes_checkbox.observe(self.on_selection_change,"value")
        self.tool_selector = ipyw.Dropdown(
            options=[
                ("Text", self.handle_textblock),
                ("Image", self.handle_image),
                ("Table", self.handle_table)
            ],
            description="Tool"
        )

        self.btns = ipyw.HBox(
            [
                self.prev_page_button, 
                self.undo_button, 
                self.next_page_button, 
                self.tool_selector,
                self.draw_bboxes_checkbox,
                self.save_page_button,
            ]
        )

        # Load the first file
        self.new_file()

    def new_file(self, event=None):
        """
        Render the pdf selected in `file_dd` and load in any JSON file which
        may have been previously generated for it.
        """
        self.draw_bboxes_checkbox.value = False

        fname = self.file_dd.value

        self.imgs = ImageContainer(fname, bulk_render=self.bulk_render)
        self.n_pages = self.imgs.info["Pages"]

        if Path(fname).with_suffix('.json').exists():
            with Path(fname).with_suffix('.json').open() as f:
                self.doc_tree = DataNode().from_dict(json.load(f))
        else:
            self.doc_tree = DataNode(str(fname))

        self.tree_visualizer = TreeWidget(
            self.doc_tree, 
            on_selection_change=self.on_selection_change
        )
        self.children = [
            self.canvas, 
            ipyw.VBox(
                [
                    self.file_dd,
                    self.btns,
                    self.tree_visualizer,
                ]
            ),
        ]

        self.fname = fname
        self.img_index = 0
        self.load()
        self.changes = []
        
    def on_selection_change(self, node):
        if isinstance(node, dict): # happens when called via checkbox value change
            path = self.tree_visualizer.path_to_selected()
            if not path:
                return
            node = self.doc_tree[self.tree_visualizer.path_to_selected()]
        if self.draw_bboxes_checkbox.value:
            if node.content and not node.content[0]["page"] == self.img_index:
                self.img_index = node.content[0]["page"]
            self.load()

    def undo(self,_=None):
        if self.changes:
            self.canvas.pop()
            path = self.changes.pop()
            if path is not None:
                self.tree_visualizer[path].pop()

    def next_page(self, _=None):
        if self.img_index < self.n_pages-1:
            self.img_index +=1
            self.load()

    def prev_page(self, _=None):
        if self.img_index > 0:
            self.img_index -=1
            self.load()

    def init_canvas(self):
        self.canvas._canvases = self.canvas._canvases[:2]
    
    def load(self):
        self.full_img = self.imgs[self.img_index]
        self.scaling_factor = fit(self.full_img, self.canvas.width, self.canvas.height)

        img = scale(self.full_img, self.scaling_factor)
        self.init_canvas()
        self.canvas.add_image(pil_2_widget(img))

        if self.draw_bboxes_checkbox.value:
            node = self.tree_visualizer.selected().node
            for item in node.content:
                if item["page"] == self.img_index:
                    x1, x2, y1, y2 = item["coords"]
                    w,h = self.full_img.width, self.full_img.height
                    s = self.scaling_factor
                    coords = [int(w*x1*s), int(h*y1*s), int(w*x2*s), int(h*y2*s)]
                    # Draw the rect on current canvas
                    self.canvas.rect = coords
                    self.canvas.draw_rect
                    # Mimic a mouse_up event
                    self.canvas.bboxes.append(coords)
                    self.canvas.add_layer()

    def add_layer(self, _):
        self.canvas.add_layer()


    def parse_current_selection(self,x,y):
        x1,y1,x2,y2 = [int(x/self.scaling_factor) for x in self.canvas.bboxes[-1]]
        x1, x2 = sorted([x1,x2])
        y1, y2 = sorted([y1,y2])
        coords = x1,y1,x2,y2
        w,h = self.full_img.width, self.full_img.height
        rel_coords = [x1/w, x2/w, y1/h, y2/h]
        self.tool_selector.value(coords, rel_coords)
    

    def handle_image(self, coords, rel_coords):
        self.tree_visualizer.selected().add_content(
            {
                "type":"image",
                "value":None,
                "page": self.img_index,
                "coords":rel_coords
            }
        )


    def handle_table(self, coords, rel_coords):
        self.tree_visualizer.selected().add_content(
            {
                "type":"table",
                "value":None,
                "page": self.img_index,
                "coords":rel_coords
            }
        )


    def handle_textblock(self, coords, rel_coords):
        text = tess.image_to_string(self.full_img.crop(coords))

        selected_node = self.tree_visualizer.selected()
        if selected_node.node.label == "":
            # NOTE: the renaming accordion boxes is funny, this would be difficult
            #       to make selected_node.rename(item) work correctly
            selected_node.label = text.strip()

            # store the coords of the headding for training purposes
            item = {
                "type":"label",
                "value":text.strip(),
                "page": self.img_index,
                "coords":rel_coords
            }
            selected_node.add_content(item)

            # TODO: this should probably reset the label to "" or the last value
            self.changes.append(None) # Delete the box only
        else:
            item = {
                "type":"text",
                "value":text,
                "page": self.img_index,
                "coords":rel_coords
            }
            selected_node.add_content(item)
            self.changes.append(self.tree_visualizer.path_to_selected())

    def save(self,_=None):
        out_path = Path(self.fname).with_suffix('.json')
        with out_path.open(mode="w") as f:
            json.dump(self.doc_tree.to_dict(), f)
