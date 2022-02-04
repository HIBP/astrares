# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 22:18:01 2020

@author: reonid

Simple Viewer based only on matplotlib

"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import AxesWidget, Button #, TextBox, RadioButtons


UP_TEXT = '<<...' 
DOWN_TEXT = '...>>' 
MAX_LABELS = 100


def in_rect(pt, rct):
    return rct.get_window_extent().contains(pt[0], pt[1])
    
def hit_textobj(textobj, axes, x, y):
    #return textobj.get_window_extent().contains(x, y)

    txt_ext = textobj.get_window_extent()
    y0, dy = txt_ext.bounds[1], txt_ext.bounds[2]
    if y < y0-5 or y > y0 + dy+5: 
        return False

    x, y = axes.transAxes.inverted().transform_point((x, y))
    return (0.0  <= x <= 1.0)

def label_get_text(obj): 
    if obj is None:
        return None
    else: 
        return obj.get_text()

def get_xylimits(plotline): 
    xx = plotline.get_xdata()
    yy = plotline.get_ydata()
    xmin, xmax = np.nanmin(xx), np.nanmax(xx)
    ymin, ymax = np.nanmin(yy), np.nanmax(yy)
    return xmin, ymin, xmax, ymax
    


last_clicked_listbox = None
    
class ListBox(AxesWidget):
    def __init__(self, ax, items, active=0):
        AxesWidget.__init__(self, ax)

        self.items = items

        self.item_active = active

        self.item_first = 0
        self.item_last = len(items)

        self.label_displayed = 10
        self.label_first = 0
        self.label_last = self.item_last
        self.label_up = None
        self.label_down = None

        
        fmx = ax.figure.canvas.fontMetrics()
        #self.label_step = int(fmx.height()*1.55) # 20
        self.label_step = int(fmx.height()*1.9) 
        
        try: # doesn't work in some versions...
            wext = ax.get_window_extent()
            wext.bounds = wext.bounds
        except:
            pass
        
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_navigate(False)
        #axcolor = ax.get_axis_bgcolor()

        #N = 10
        #dy = 1.0 / (N + 1)
        #ys = np.linspace(1 - dy, dy, N)
        cnt = 0
        
        #bnds = ax.get_window_extent().bounds
        #x0 = bnds[0] + 6
        #y0 = bnds[1] + 6*2
        #y1 = bnds[1] + bnds[3] - 6*2
        x0, y0, y1 = self._getxy()
        
        self.labels = []
        for i in range(MAX_LABELS):
            #y = ys[i]
            y = y1 - i*self.label_step
            lbl = ax.text(x0, y, '', transform=None, #transform=ax.transAxes,
                        horizontalalignment='left',
                        verticalalignment='center', 
                        color='black', 
                        backgroundcolor='white')
            if y < y0: 
                lbl.set_visible(False)
            else: 
                self.label_displayed = i+1

            self.labels.append(lbl)
            #ax.add_patch(rct)
            cnt += 1

        self.connect_event('button_press_event', self._clicked)
        self.connect_event('key_press_event', self._keypressed)
        #self.connect_event('motion_notify_event', self._clicked)
        self.connect_event('resize_event', self._resized)

        self.cnt = 0
        self.observers = {}
        self._update()

    def _getxy(self): 
        bnds = self.ax.get_window_extent().bounds        
        x0 = bnds[0] + 6
        y0 = bnds[1] + 6*2
        y1 = bnds[1] + bnds[3] - 6*2 
        
        d = 11
        x0 = bnds[0] + d
        y0 = bnds[1] + d*2
        y1 = bnds[1] + bnds[3] - d*2 
        
        return x0, y0, y1
    
    def move(self, delta):  # +1, -1
        self.item_active += delta

        if self.item_active <= -1: 
            self.item_active = 0

        elif self.item_active >= len(self.items): 
            self.item_active = len(self.items)-1
            #return # do nothing 
            
        elif self.item_active < self.item_first: 
            self.item_first = self.item_active

        elif self.item_active > self.item_last: 
            self.item_first += 1 + (self.item_first == 0)
        
        self._update()
        
        if self.drawon: 
            self.ax.figure.canvas.draw()

        if not self.eventson:
            return

        active_text = self.items[self.item_active]  
        for cid, func in self.observers.items():
            func(active_text)

        plt.draw()
    

    def _keypressed(self, event):
        if self.ignore(event):
            return
        #if event.inaxes != self.ax:
        #    return
        global last_clicked_listbox    
        if self != last_clicked_listbox: 
            return 
         
        if event.key == 'up': 
            self.move(-1)
        if event.key == 'down': 
            self.move(1)

            

    def _update(self): 
        N = len(self.items)
        NN = self.label_displayed

        i0, i1 = self.item_first, self.item_first + NN
        ii0, ii1 = 0, NN
        self.label_up, self.label_down = None, None
                
        #for lbl in self.labels:
        #    lbl.set_text('')
        #    lbl.set_visible('False')

        if N <= NN: 
            i0 = 0
            i1 = N
            ii0 = 0
            ii1 = i1

        if i0 > 0: 
            i1 -= 1
            ii0 += 1
            self.label_up = 0
            self.labels[self.label_up].set_text(UP_TEXT)
            self.labels[self.label_up].set_color('black')
            self.labels[self.label_up].set_backgroundcolor('white')

        if N - i0 > NN - (self.label_up is not None): 
            i1 -= 1
            ii1 -= 1
            self.label_down = NN-1
            self.labels[self.label_down].set_text(DOWN_TEXT)
            self.labels[self.label_down].set_color('black')
            self.labels[self.label_down].set_backgroundcolor('white')
            
        if i0 == 1: 
            i0 = 0
            ii0 = 0
            self.label_up = None
            

        if i1 > N: #???
            i1 = N
            ii1 = ii0 + N        

        ii1 = ii0 + (i1 - i0)        
        
        self.item_first, self.item_last = i0, i1-1
        self.label_first, self.label_last = ii0, ii1-1
        
        for lbl, txt, i in zip(self.labels[ii0:ii1], 
                               self.items[i0:i1], 
                               range(i0, i1)): 

            #if i == self.item_active: # ??? in some cases there can be a bug
            if listbox_active_item_name(self) == txt: 
                bgcolor = 'blue'
                txtcolor = 'white'
            else: 
                bgcolor = 'white'
                txtcolor = 'black'
                
            lbl.set_text(txt)
            lbl.set_visible(True)

            lbl.set_color(txtcolor)
            lbl.set_backgroundcolor(bgcolor)


        d = (self.label_down is not None)
        for lbl in self.labels[ii1+d:self.label_displayed]:
            lbl.set_text('')


    def _resized(self, event): 
        #bnds = self.ax.get_window_extent().bounds
        #x0 = bnds[0] + 6
        #y0 = bnds[1] + 6*2
        #y1 = bnds[1] + bnds[3] - 6*2
        x0, y0, y1 = self._getxy()
        
        for i in range(MAX_LABELS):
            lbl = self.labels[i]
            y = y1 - i*self.label_step
            if y < y0: 
                lbl.set_visible(False)
            else: 
                lbl.set_x(x0)
                lbl.set_y(y)
                lbl.set_visible(True)
                self.label_displayed = i+1
        self._update()
    
    def _clicked(self, event):        
        if self.ignore(event):
            return
        if event.button != 1:
            return
        if event.inaxes != self.ax:
            return
  
        global last_clicked_listbox
        last_clicked_listbox = self
        
        #xy = self.ax.transAxes.inverted().transform_point((event.x, event.y))
        #pclicked = np.array([xy[0], xy[1]])

        active_lbl = None
        for txt in self.labels:
            #if txt.get_window_extent().contains(event.x, event.y):
            if hit_textobj(txt, self.ax, event.x, event.y):
                active_lbl = txt
                break
        else:
            pass # return

        clicked_text = label_get_text(active_lbl)
        if clicked_text == UP_TEXT: 
            self.item_first -= 1
        elif clicked_text == DOWN_TEXT: 
            if self.item_first == 0: 
                self.item_first = 2
            else:
                self.item_first += 1

        try: 
            self.item_active = self.items.index(clicked_text) 
            active_text = clicked_text
        except:
            active_text = self.items[self.item_active]
     
        self._update()

        if self.drawon: 
            self.ax.figure.canvas.draw()

        if not self.eventson:
            return

        for cid, func in self.observers.items():
            func(active_text)



    def on_clicked(self, func):
        """
        When the button is clicked, call *func* with button label

        A connection id is returned which can be used to disconnect
        """
        cid = self.cnt
        self.observers[cid] = func
        self.cnt += 1
        return cid

    def disconnect(self, cid):
        """remove the observer with connection id *cid*"""
        try:
            del self.observers[cid]
        except KeyError:
            pass

def listbox_get_active_text(obj): 
    if obj is None: 
        return None
    else: 
        obj.get_text()

def listbox_active_item_name(listbox): 
    if listbox is None: 
        return None
    else: 
        idx = listbox.item_active
        try: 
            name = listbox.items[idx]
        except IndexError: 
            name = None
    
        return name   

class Scroll(AxesWidget):
    def __init__(self, ax):
        AxesWidget.__init__(self, ax)
        
        self.btn_up = None
        self.btn_down = None
        
        

class ViewerAdapter: 
    def __init__(self, obj):
        pass        
        #self.obj = obj
        
    def get_titles(self): 
        return None, None
    
    def get_signal(self, name1, name2): 
        x, y = None, None        
        return x, y
        
    def get_names1(self): 
        return []
        
    def get_names2(self, name1): 
        return []
    
    def init_gui(self, viewer): 
        pass

class Viewer: 
    def __init__(self, adapter): 
        self.adapter = adapter
        col_titles = adapter.get_titles()

        self.buttons = {}

        self.figure, self.ax = plt.subplots()
        x, y = [0, 0], [0, 0]
        self.line, = plt.plot(x, y, lw=2)

        #ax1 = plt.axes([0.02, 0.1, 0.1, 0.8])
        w = 0.13
        ax1 = plt.axes([0.02, 0.05, w, 0.9])
        self.listbox1 = ListBox(ax1, items=adapter.get_names1())
        self.listbox1.on_clicked(self._changed1)
        name1 = adapter.get_names1()[0]

        if col_titles[1] is None: 
            #name2 = None
            self.listbox2 = None
            plt.subplots_adjust(bottom=0.2, left=0.3)
        else:
            ax2 = plt.axes([w + 0.03, 0.05, w, 0.9])
            
            self.listbox2 = ListBox(ax2, items=adapter.get_names2(name1))
            self.listbox2.on_clicked(self._changed2)            
            #name2 = adapter.get_names2(name1)[0]
            plt.subplots_adjust(bottom=0.2, left=0.4)
                    

        self._changed()
        self.adapter.init_gui(self)

    def _changed1(self, text): 
        if self.listbox2 is not None: 
            self.listbox2.items = self.adapter.get_names2(text)
            self.listbox2._update()
            
        self._changed()

    def _changed2(self, text): 
        self._changed()


    def get_active_names(self): 
        name1 = listbox_active_item_name(self.listbox1)
        name2 = listbox_active_item_name(self.listbox2)
        return name1, name2
        
    def _changed(self): 
        name1, name2 = self.get_active_names() 
        
        x, y = self.adapter.get_signal(name1, name2)
        self.line.set_xdata(x)        
        self.line.set_ydata(y)
        
        #plt.sca(self.line.axes)     
        #self.line.axes.set_xlim(-0.1, 1.1)
        #self.line.axes.set_ylim(-1.1, 1.1)
        #plt.autoscale(True)
        
        #x0, y0, x1, y1 = get_xylimits(self.line)
        #self.line.axes.set_xlim(x0, x1)
        #self.line.axes.set_ylim(y0, y1)
        
        #self.line.axes.autoscale(True)
        self.line.axes.relim(True)
        self.line.axes.autoscale_view()
        
        plt.draw()

    def add_btn(self, name, location, action): 
        #ax =  plt.axes([0.7, 0.05, 0.1, 0.075]) 
        ax =  plt.axes(location) 
        b = Button(ax, name)
        b.on_clicked(action)
        self.buttons[name] = b

class TestViewerAdapter(ViewerAdapter): 
    def get_titles(self): 
        return 'Test', 'X' #None
    
    def get_signal(self, name1, name2): 
        if (name1 is None)or(name2 is None): 
            return None, None

        freq = float(name1)
        t = np.arange(0.0, 1.0, 0.001)
        data = np.sin(2*np.pi*freq*t)
        
        k = {'first': 1, 'second': 2, 'third': 3}[name2]
        return t, k*data
        
    def get_names1(self): 
        freqs = np.arange(2, 40, 3)
        return [str(f) for f in freqs]
        
    def get_names2(self, name1): 
        if name1 == '11': 
            return ['first', 'second', 'third']
        else:
            return ['first', 'second']


if __name__ == '__main__': 

    
    vwr = Viewer(TestViewerAdapter(None))
    plt.show()

