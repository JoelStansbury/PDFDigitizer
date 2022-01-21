import PIL.Image as pil
import pytesseract as tess
import pandas as pd
import numpy as np
import cv2


def img_2_cells(img, approximate_cell_height=20, approximate_cell_width=150):
    """
    img <PIL.Image>: image of a table
    approximate_cell_height (pixels) <int>: This is used as a lower bound for
        valid cells. It is also used to distinguish between different rows for
        the purpose of ordering items in the output
    approximate_cell_width (pixels) <int>: This is used as a lower bound for
        valid cells. It is also used to distinguish between different columns
        for the purpose of ordering items in the output

    return <list<tuple(cv2_coords, text)>>: A list of tuples containing the
        bbox and text of detected cells. The elements are ordered first by
        column, then by row.
    """
    
    img = np.array(img)
    img = cv2.rectangle(
        img=img, 
        pt1=(1,1), 
        pt2=(len(img[0])-1, len(img)-1), 
        color=(0, 0, 0), 
        thickness=2
    )
    imgray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(
        src=imgray, 
        thresh=180, 
        maxval=255, 
        type=cv2.THRESH_BINARY_INV
    )
    
    kernel = np.ones((5,5),np.uint8)
    dilated_value = cv2.dilate(thresh, kernel, iterations = 1)
    
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    items = []
    for contour, hierarchy in zip(contours, hierarchy[0]):
        x, y, w, h = cv2.boundingRect(contour)
        if w>approximate_cell_width and h>approximate_cell_height:
            text = tess.image_to_string(pil.fromarray(img).crop((x,y,x+w,y+h)), config="--psm 1").strip()
            cv2_coords = x, y, w, h
            items.append((cv2_coords,text))
    items.sort(key = lambda x: (x[0][1] // approximate_cell_height, x[0][0] // approximate_cell_width))
    return items

def contains(coords, px, py):
    x,y,w,h = coords
    return x<px and x+w>px and y<py and y+h>py


def cells_2_table(cells, approximate_cell_height=20, approximate_cell_width=20):
    # find the shortest height dx
    # find the find column positions
    #   because we divide by approx_cell_width, we expect the number of unique
    #   x_0 to be the number of columns
    #   NOTE: this should be the approximate midpoint not the approximate start
    # start at 0,0
    # intersects(x,y) -> return the cell which contains the point (x,y)
    # x = 0
    # rows = []
    # while x < x_max
    #   x += dx
    #   rows.append([intersects(x,y) for y in column_positions])
    # df = pd.DataFrame(rows)
    # df.drop_duplicates()

    column_positions = set()
    row_positions = set()
    for cv2_coords, text in cells:
        column_positions.add(approximate_cell_width*(cv2_coords[0]//approximate_cell_width))
        column_positions.add(approximate_cell_width*((cv2_coords[0] + cv2_coords[2])//approximate_cell_width))
        row_positions.add(approximate_cell_height*(cv2_coords[1]//approximate_cell_height))
        row_positions.add(approximate_cell_height*((cv2_coords[1] + cv2_coords[3])//approximate_cell_height))
    
    cp = sorted(list(column_positions))
    cp = [cp[i]+(cp[i+1]-cp[i])/2 for i in range(len(cp)-1)]
    rp = sorted(list(row_positions))
    rp = [rp[i]+(rp[i+1]-rp[i])/2 for i in range(len(rp)-1)]

    rows = []
    for y in rp:
        row = []
        for x in cp:
            # find all potential cells which could be used for this position
            candidate_cells = [cell for cell in cells if contains(cell[0], x, y)]
            # sort by area
            candidate_cells.sort(key = lambda cell: cell[0][2]*cell[0][3])
            # use the text contained within the smallest cell as the value
            if candidate_cells:
                row.append(candidate_cells[0])
            else:
                row.append((None,""))
        rows.append(tuple(row))
    
    unique = []
    for r in rows:
        if not r in unique:
            unique.append(r)
    rows = unique
    rows = [
        [cell[1].strip() for cell in r]
        for r in rows
    ]
    rows = [r for r in rows if not all([x==r[0] for x in r])]
    if len(set(rows[0])) == len(rows[0]):
        return pd.DataFrame(rows[1:], columns=rows[0])
    return pd.DataFrame(rows)
