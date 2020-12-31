import io
from collections import defaultdict

import ipywidgets as ipyw
import pytesseract as ocr
from traitlets import Int, Unicode, List, link

from .widget_canvas import PdfCanvas, BboxColorPicker
from ..image_utils import fit, scale, pil_2_widget, ImageContainer
from ..settings import SETTINGS


class App(ipyw.HBox):
    active_category = Int().tag(sync=True)
    pdf_viewer_shape = List().tag(sync=True)

    def __init__(self, fname):
        super().__init__()

        self.imgs = ImageContainer(fname)
        self.text_stack = defaultdict(list)

        self.canvas = PdfCanvas(height=900, width=800)
        self.canvas.active_layer.on_mouse_up(self.parse_current_selection)

        self.color_picker = BboxColorPicker()
        self.output_field = ipyw.Textarea(layout={"width":"90%"})
        self.undo_button = ipyw.Button(icon="undo")
        self.undo_button.on_click(self.undo)
        self.next_page_button = ipyw.Button(icon="arrow-right")
        self.next_page_button.on_click(self.next_page)
        self.btns = ipyw.HBox([self.undo_button, self.next_page_button])
        self.children = [self.canvas, ipyw.VBox([self.btns, self.color_picker, self.output_field])]

        
        link((self.color_picker,"value"),(self.canvas,"stroke_style"))
        link((self.color_picker,"selection"),(self.canvas,"stroke_style_idx"))

        self.img_index = 0
        self.load()


    def undo(self,_=None):
        self.output_field.value=""
        self.text_stack[self.img_index].pop()
        self.canvas.pop()

    def next_page(self, _=None):
        self.img_index +=1
        self.canvas._canvases = self.canvas._canvases[:2]
        self.load()

    def load(self):

        idx = self.img_index
        self.scaling_factor = fit(self.imgs[idx], self.canvas.width, self.canvas.height)

        img = scale(self.imgs[idx], self.scaling_factor)
        self.canvas.add_image(pil_2_widget(img))

    def add_layer(self, _):
        self.canvas.add_layer()

    def parse_current_selection(self,x,y):
        x1,y1,x2,y2 = [int(x/self.scaling_factor) for x in self.canvas.bboxes[-1]]
        x1, x2 = sorted([x1,x2])
        y1, y2 = sorted([y1,y2])
        coords = x1,y1,x2,y2
        text = ocr.image_to_string(self.imgs[self.img_index].crop(coords))
        self.output_field.value = text
        self.text_stack[self.img_index].append((self.canvas.stroke_style_idx, text))

    def export_current_page(self):
        res = defaultdict(list)
        for idx, text in self.text_stack[self.img_index]:
            res[self.color_picker.categories[idx].name].append(text)
        return res

    def export(self):
        text_stack_full = defaultdict(list)
        for page_num, ts in self.text_stack.items():
            for idx, text in ts:
                text_stack_full[self.color_picker.categories[idx].name].append(text)
        return text_stack_full