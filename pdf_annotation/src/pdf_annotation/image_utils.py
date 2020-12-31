import io

from ipywidgets import Image
from pdf2image import convert_from_path

def fit(img, w, h):
    w_old = img.width
    h_old = img.height
    return min(w/w_old, h/h_old)

def scale(img, factor):
    w_old = img.width
    h_old = img.height
    return img.resize(size=(int(w_old*factor), int(h_old*factor)), resample=1)

def pil_2_widget(img, format="png"):
    imgByteArr = io.BytesIO()
    img.save(imgByteArr, format=format)
    return Image(value=imgByteArr.getvalue())

class ImageContainer:
    def __init__(self, fname, bulk_render=True):
        self.bulk_render = bulk_render
        if bulk_render:
            self.imgs = convert_from_path(fname, dpi=300)
        else:
            self.fname = fname
    def __getitem__(self, i):
        if self.bulk_render:
            return self.imgs[i]
        return convert_from_path(self.fname, first_page=i, last_page=i)[0]
