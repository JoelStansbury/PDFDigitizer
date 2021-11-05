import io
from pathlib import Path
import json

import ipywidgets as ipyw
import pytesseract as tess
from traitlets import observe

from .widgets.canvas import PdfCanvas
# from .widgets.tree import DataNode, TreeWidget
from .widgets.new_ipytree import TreeWidget
from .widgets.node_detail import NodeDetail
from .widgets.navigation import NavigationToolbar
from .utils.image_utils import fit, scale, pil_2_widget, ImageContainer, scale_coords
from .style.style import CSS

class App(ipyw.HBox):

    def __init__(self, indir, bulk_render=False):
        super().__init__()
        self.add_class("main-app")

        self.bulk_render = bulk_render
        self.fname = ""
        self.active_node = None
        self.active_node_id = None

        self.navigator = NavigationToolbar(indir)
        self.canvas = PdfCanvas(height=1000)
        self.tree_visualizer = TreeWidget(indir)
        self.node_detail = NodeDetail(self.tree_visualizer.root)

        self.tree_visualizer.observe(self.on_selection_change, "selected_nodes")
        self.navigator.prev_page_button.on_click(self.prev_page)
        self.navigator.next_page_button.on_click(self.next_page)
        self.navigator.save_page_button.on_click(self.save)
        # self.navigator.draw_bboxes_checkbox.observe(self.on_selection_change,"value")

        self.canvas.animated_layer.on_mouse_up(self.parse_current_selection)

        # Load the first file
        # self.new_file()
        self.SELECTION_PIPES = {
            "text": self.handle_textblock,
            "image": self.handle_image,
            "table": self.handle_table,
            "section": self.handle_label,
        }


        tree_box = ipyw.VBox([self.tree_visualizer])
        tree_box.add_class("doc-tree-outter")

        self.children = [
            tree_box,
            self.canvas, 
            ipyw.VBox(
                [
                    CSS,
                    self.navigator,
                    self.node_detail,
                ]
            ),
        ]



    def on_selection_change(self, event):
        """
        Render the pdf selected in `file_dd` and load in any JSON file which
        may have been previously generated for it.
        """
        # Selecting a new node causes two events, one for deselecting the old
        # one and another for selecting the new one. We are concerned with the
        # new node so we ignore the first event by asserting that new is not None.
        # print(event["new"])
        if event["new"]:
            node = event["new"][0]

            self.active_node = node
            self.selection_pipe = self.SELECTION_PIPES.get(node._type,None)
            fname = node._path
            self.node_detail.set_node(node)

            if not fname == self.fname and fname.suffix == ".pdf":
                self.imgs = ImageContainer(fname, bulk_render=self.bulk_render)
                self.n_pages = self.imgs.info["Pages"]

                self.fname = fname
                self.img_index = 0 # get index from node
                self.load()
                

    def next_page(self, _=None):
        if self.img_index < self.n_pages-1:
            self.canvas.clear()
            self.img_index +=1
            self.load()

    def prev_page(self, _=None):
        if self.img_index > 0:
            self.canvas.clear()
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

        if self.navigator.draw_bboxes_checkbox.value:
            node = self.active_node
            # for item in node.content:
            #     if item["page"] == self.img_index:
            #         x1, x2, y1, y2 = item["coords"]
            #         w,h = self.full_img.width, self.full_img.height
            #         s = self.scaling_factor
            #         coords = [int(w*x1*s), int(h*y1*s), int(w*x2*s), int(h*y2*s)]
            #         # Draw the rect on current canvas
            #         self.canvas.rect = coords
                    # self.canvas.draw_rect
                    # Mimic a mouse_up event
                    # self.canvas.bboxes.append(coords)
                    # self.canvas.add_layer()

    def parse_current_selection(self,x,y):
        x1,y1,x2,y2 = [int(x/self.scaling_factor) for x in self.canvas.rect]
        x1, x2 = sorted([x1,x2])
        y1, y2 = sorted([y1,y2])
        coords = x1,y1,x2,y2
        w,h = self.full_img.width, self.full_img.height
        rel_coords = [x1/w, x2/w, y1/h, y2/h]
        
        self.selection_pipe(coords, rel_coords)
    

    def handle_image(self, coords, rel_coords):
        self.active_node.add_content(
            {
                "value":None,
                "page": self.img_index,
                "coords":rel_coords
            }
        )


    def handle_table(self, coords, rel_coords):
        self.active_node.add_content(
            {
                "value":None,
                "page": self.img_index,
                "coords":rel_coords
            }
        )


    def handle_label(self, coords, rel_coords):
        text = tess.image_to_string(self.full_img.crop(coords))

        selected_node = self.active_node
        selected_node.name = text.strip()

        # store the coords of the headding for training purposes
        item = {
            "value":text.strip(),
            "page": self.img_index,
            "coords":rel_coords
        }
        selected_node.add_content(item)

    def handle_textblock(self, coords, rel_coords):
        text = tess.image_to_string(self.full_img.crop(coords))
        
        item = {
            "value":text,
            "page": self.img_index,
            "coords":rel_coords
        }
        self.active_node.add_content(item)

    def save(self,_=None):
        out_path = Path(self.fname).with_suffix('.json')
        with out_path.open(mode="w") as f:
            json.dump(self.doc_tree.to_dict(), f)
