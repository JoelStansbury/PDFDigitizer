# TODO: remove this when no longer needed
def clean(node):
    if "label" in node:
        node["type"] = "section"
        for n in node["children"]:
            if "type" in n and n["type"] == "label":
                node["value"] = n["value"]
                node["coords"] = n["coords"]
                node["page"] = n["page"]
                node["children"] = [
                    n for n in node["children"] 
                    if not ("type" in n and n["type"]=="label")
                    ]
                break
        else:
            node["value"] = node["label"]
        

    if not "children" in node:
        node["children"] = []


    if "content" in node:
        node["children"] = node["content"] + node["children"]

    for n in node["children"]:
        clean(n)
