import ipywidgets as ipyw
from ipycanvas import Canvas, MultiCanvas
from traitlets import Unicode, Int, link

class PdfCanvas(MultiCanvas):
    stroke_style = Unicode().tag(sync=True)
    stroke_style_idx = Int().tag(sync=True)

    def __init__(self, **kwargs):
        super().__init__(2, **kwargs)

        self.active_layer = self[1]
        self.bboxes = []

        self.active_layer.on_mouse_down(self.mouse_down)
        self.active_layer.on_mouse_move(self.mouse_move)
        self.active_layer.on_mouse_up(self.mouse_up)
        self.rect = None
        self.mouse_is_down = False

    def xywh(self):
        '''
        ipycanvas requires xywh coords, but ipyevents (and PIL) uses xyxy, 
        so conversion is needed to draw the box on the canvas.
        '''
        x1,y1,x2,y2 = self.rect
        x = min(x1,x2)
        y = min(y1, y2)
        w = abs(x2-x1)
        h = abs(y2-y1)
        return x,y,w,h

    def draw_rect(self, style="black"):
        self.clear()
        if style:
            self.active_layer.stroke_style = style
        else:
            self.active_layer.stroke_style = self.stroke_style
        
        self.active_layer.stroke_rect(*self.xywh())

    def clear(self):
        self.active_layer.clear_rect(0,0,self.width, self.height)

    def mouse_down(self, x, y):
        self.mouse_is_down = True
        self.rect = [x,y,x+1,y+1]
        self.draw_rect()

    def mouse_move(self, x, y):
        if self.mouse_is_down:
            self.rect[2]=x
            self.rect[3]=y
            self.draw_rect()

    def mouse_up(self, x, y):
        # x,y,s = event["relativeX"], event["relativeY"], event["shiftKey"]
        # if s:
        #     print("hello",x,y,s)
        self.mouse_is_down = False
        self.bboxes.append(self.rect)
        self.add_layer()

    def add_layer(self):
        if self.rect:
            self.clear()

            old_layer = Canvas(width=self.width, height=self.height)
            old_layer.stroke_style = "black"
            old_layer.stroke_rect(*self.xywh())
            old_layer.bbox = self.rect

            self._canvases = self._canvases + [old_layer]
            self.rect = None

    def add_image(self, img):
        ":param img: raw byte data of image"
        layer = Canvas(width=self.width, height=self.height)
        layer.draw_image(img)
        self._canvases = [layer] + self._canvases[1:]
    
    def pop(self,_=None):
        if len(self._canvases)>2:
            self._canvases = self._canvases[:-1]
            return True
        return False
