import io
from collections import defaultdict
from pathlib import Path
import json

import ipywidgets as ipyw
import pytesseract as tess
from traitlets import Int, Unicode, List, link

from .widget_canvas import PdfCanvas, BboxColorPicker
from ..image_utils import fit, scale, pil_2_widget, ImageContainer
from ..settings import SETTINGS


class App(ipyw.HBox):
    active_category = Int().tag(sync=True)
    pdf_viewer_shape = List().tag(sync=True)

    def __init__(self, fname, bulk_render=False):
        super().__init__()

        self.fname = fname
        self.imgs = ImageContainer(fname, bulk_render=bulk_render)
        self.n_pages = self.imgs.info["Pages"]

        self.color_picker = BboxColorPicker()
        self.output_field = ipyw.Textarea(layout={"width":"90%"})

        if Path(fname).with_suffix('.json').exists():
            with Path(fname).with_suffix('.json').open() as f:
                self.data = json.load(f)
                self.color_picker.load(self.data["color_picker_params"])
            # TODO: Consider fixing this automatically
            assert len(self.data["sizes"]) == self.n_pages, "Data file does not match pdf (difference in page numbers)"
        else:
            self.data = {
                "sizes": [() for i in range(self.n_pages)],
                "texts": [[] for i in range(self.n_pages)],
                "categories": [[] for i in range(self.n_pages)],
                "textblocks": [[] for i in range(self.n_pages)],
            }

        self.canvas = PdfCanvas(height=900, width=800)
        self.canvas.active_layer.on_mouse_up(self.parse_current_selection)


        self.prev_page_button = ipyw.Button(icon="arrow-left")
        self.prev_page_button.on_click(self.prev_page)
        self.undo_button = ipyw.Button(icon="undo")
        self.undo_button.on_click(self.undo)
        self.next_page_button = ipyw.Button(icon="arrow-right")
        self.next_page_button.on_click(self.next_page)
        self.save_page_button = ipyw.Button(icon="save")
        self.save_page_button.on_click(self.save)

        self.btns = ipyw.HBox([
            self.prev_page_button, 
            self.undo_button, 
            self.next_page_button, 
            self.save_page_button])
        self.children = [self.canvas, ipyw.VBox([self.btns, self.color_picker, self.output_field])]

        
        link((self.color_picker,"value"),(self.canvas,"stroke_style"))
        link((self.color_picker,"selection"),(self.canvas,"stroke_style_idx"))



        self.img_index = 0
        self.load()

    def undo(self,_=None):
        self.output_field.value=""
        self.data["textblocks"][self.img_index].pop()
        self.data["texts"][self.img_index].pop()
        self.data["categories"][self.img_index].pop()
        self.canvas.pop()

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
        # self.color_picker.selection = -1
        for i,tb in enumerate(self.data["textblocks"][self.img_index]):
            x1,y1,x2,y2 = [int(x*self.scaling_factor) for x in tb]
            coords = x1,y1,x2,y2
            # Select the color
            self.color_picker.selection = self.data["categories"][self.img_index][i]
            # Draw the rect on current canvas
            self.canvas.rect = coords
            self.canvas.draw_rect
            # Mimic a mouse_up event
            self.canvas.bboxes.append(coords)
            self.canvas.add_layer()
    
    def load(self):
        self.full_img = self.imgs[self.img_index]
        self.scaling_factor = fit(self.full_img, self.canvas.width, self.canvas.height)

        # TODO: Resize bboxes if sizes don't match
        if self.data["sizes"][self.img_index]:
            from_data = tuple(self.data["sizes"][self.img_index])
            assert from_data == self.full_img.size, f"{from_data} {self.full_img.size}"
        else:
            self.data["sizes"][self.img_index] = self.full_img.size
        
        img = scale(self.full_img, self.scaling_factor)
        self.init_canvas()
        self.canvas.add_image(pil_2_widget(img))


    def add_layer(self, _):
        self.canvas.add_layer()

    def parse_current_selection(self,x,y):
        x1,y1,x2,y2 = [int(x/self.scaling_factor) for x in self.canvas.bboxes[-1]]
        x1, x2 = sorted([x1,x2])
        y1, y2 = sorted([y1,y2])
        coords = x1,y1,x2,y2
        text = tess.image_to_string(self.full_img.crop(coords))

        self.data["textblocks"][self.img_index].append(coords)
        self.data["texts"][self.img_index].append(text)
        self.data["categories"][self.img_index].append(self.canvas.stroke_style_idx)
        # self.data["charboxes"][self.img_index].append(
        #     tess.image_to_boxes(self.full_img, config="-c tessedit_create_boxfile=1"))

        self.output_field.value = text

    def save(self,_=None):
        out_path = Path(self.fname).with_suffix('.json')
        self.data["color_picker_params"] = self.color_picker.params()
        with out_path.open(mode="w") as f:
            json.dump(self.data, f)

    def to_dict(self):
        cats = [
            [
                self.data['color_picker_params']['names'][j] 
                for j in i
                ] for i in self.data['categories']
            ]
        res = defaultdict(list)
        for i,text in enumerate(self.data["texts"]):
            for j,p in enumerate(text):
                res[cats[i][j]].append(p)
        return res
