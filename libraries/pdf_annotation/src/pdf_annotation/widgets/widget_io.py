import ipywidgets as ipyw
from traitlets import (
    observe, default, Unicode, Dict, List, Int, Bool, Bytes, CaselessStrEnum, Set
)


'''
TODO: Fix the multiple upload bug. Allow for multiple files
'''
class IOWidget(ipyw.HBox):
    selection = Unicode().tag(sync=True)
    value = Bytes().tag(sync=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.file_label = ipyw.Label()
        self.file_uploader = ipyw.FileUpload(multiple=False)

        self.file_uploader.observe(self.onchange_upload, "_counter")
        self.file_uploader.observe(self.onerror_upload, "error")

        ### HAVING ISSUES WITH multiple=True ###
        # self.file_selector = ipyw.Select()
        # self.file_selector.observe(self.onchange_selection, "value")

        self.children = [self.file_label, self.file_uploader]

    def onchange_upload(self, change):
        fnames = list(self.file_uploader.value.keys())
        if fnames:
            self.file_label.value = fnames[0]
            self.value = self.file_uploader.value[fnames[0]]["content"]
            # self.value = change["content"]
        # if fnames:
        #     self.file_selector.options = fnames
        # else:
        #     self.file_selector.options = "None"

    # def onchange_selection(self, change):
    #     print("selction_changed")
    #     self.set_trait('selection', self.file_selector.value)
    #     self.set_trait('value', self.file_uploader.value[self.selection]["content"])
        
    def onerror_upload(self):
        print(self.file_uploader.error)