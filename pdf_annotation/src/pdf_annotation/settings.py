SETTINGS = {
        "PDF Render dpi": {
            "type":"int",
            "min":100,
            "max":1000,
            "default":300,
            "value":300,
            "tooltip":
                "Determines the resolution of images sent to the OCR engine. "+
                "Higher values will increase accuracy, but will take longer to load "+
                "and process. (Requires re-upload to take effect)",
            "disabled":False},
        
        "Bulk Conversion": {
            "type":"bool",
            "default":True,
            "value":True,
            "tooltip":
                "If True, will render a PIL image of every page in the PDF document upon initial upload. "+
                "Otherwise, each page will be rendered whenever it is displayed. Very large documents will need "+
                "this option set to False in order to avoid memory errors. (Requires re-upload to take effect)",
            "disabled":False},
    }