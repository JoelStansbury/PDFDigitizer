import cv2
import numpy as np
import pandas as pd
import pytesseract as tess

def img_2_table(img):
    img_contour = np.array(img).copy()
    ret, thresh_value = cv2.threshold(
        src=img_contour, 
        thresh=180, 
        maxval=255, 
        type=cv2.THRESH_BINARY_INV
    )
    kernel = np.ones((5,5),np.uint8)
    dilated_value = cv2.dilate(thresh_value,kernel,iterations = 1)
    contours, hierarchy = cv2.findContours(
        image=dilated_value, 
        mode=cv2.RETR_TREE, 
        method=cv2.CHAIN_APPROX_SIMPLE
    )
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        # bounding the images
        if y < 50:
            table_image = cv2.rectangle(
                img=table_image, 
                pt1=(x, y), 
                pt2=(x + w, y + h), 
                color=(0, 0, 255), 
                thickness=1
            )
    return table_image