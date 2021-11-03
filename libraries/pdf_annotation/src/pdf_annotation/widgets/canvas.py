from ipycanvas import Canvas, MultiCanvas

class PdfCanvas(MultiCanvas):

    def __init__(self, **kwargs):
        super().__init__(3, **kwargs)
        self.add_class("pdf-canvas")

        self.bboxes = []

        self.bg_layer = self[0]
        self.fixed_layer = self[1]
        self.animated_layer = self[2]

        self.animated_layer.on_mouse_down(self.mouse_down)
        self.animated_layer.on_mouse_move(self.mouse_move)
        self.animated_layer.on_mouse_up(self.mouse_up)

        self.rect = None
        self.mouse_is_down = False

    def update(self):
        """
        I don't know why, but this is needed in order to allow animated_layer
        to update correctly after making a change to any other layer
        """
        self._canvases = [self.bg_layer, self.fixed_layer, self.animated_layer]

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

    def draw_rect(self):
        self.animated_layer.clear_rect(0,0,self.width, self.height)
        self.animated_layer.stroke_rect(*self.xywh())
        self.add_class("pdf-canvas")

    def clear(self):
        self.fixed_layer.clear_rect(0,0,self.width, self.height)

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
        self.mouse_is_down = False
        self.animated_layer.clear_rect(0,0,self.width, self.height)
        self.fixed_layer.stroke_rect(*self.xywh())
        self.update()

    def add_image(self, img):
        ":param img: raw byte data of image"
        self.bg_layer.draw_image(img)
        self.update()

