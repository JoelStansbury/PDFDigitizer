from collections import deque

from ipywidgets import VBox
from ipyevents import Event


class Deque(VBox):
    """
    This widget provides the ability to scroll through an arbitrarily
    long list of widgets. Your custom widget must contain an update method
    which accepts one record as an argument. A record can be whatever you like.
    """

    def __init__(self, widget, records, to_show=5, **kwargs):
        """
        widget <Class>: Object used to display a record. Must have an update method
        records <list>: List of whatever you pass the update method. Each record
            represents one of the arbitrarily many items which the user can scroll through
        to_show <Int>: Number of widgets to show at once. (default 5)
        """

        super().__init__(**kwargs)
        self.add_class("hil-pdf-digitizer-deque")
        d  = Event(source=self, watched_events=["wheel"])
        d.on_dom_event(self.event_handler)

        self.to_show = to_show
        self.num_rows = min(len(records), to_show)

        self.idx = 0

        self.records = records
        self.rows = deque([widget() for i in range(self.num_rows)])
        for i,row in enumerate(self.rows):
            row.update(self.records[i])

        self.children = list(self.rows)[0:self.to_show]


    def scroll(self, deltaY):
        N = len(self.records)
        nr = self.num_rows
        
        n = max(min((N-nr)-self.idx, deltaY//100), -self.idx)
        self.idx += n
        
        self.rows.rotate(-n)
        if n > 0:
            i = nr-n
            j = nr
        else:
            i = 0
            j = min(abs(n),nr)
        for k in range(i,j):
            x = min(self.idx+k, N-1)
            self.rows[k].update(self.records[x])
        self.children = [self.rows[i] for i in range(self.to_show)]
    

    def event_handler(self, event):
        if "deltaY" in event:
            self.scroll(event["deltaY"])