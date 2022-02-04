# -*- coding: utf-8 -*-
"""
Created on Mon Jan 31 14:04:38 2022

@author: reonid
"""

from astrares import ResFile

from myviewer import Viewer, ViewerAdapter

class AstraResViewerAdapter(ViewerAdapter): 
    def __init__(self, res, kind='profiles'):
        self.res = res
        self.displayed_values = kind

    def get_titles(self): 
        if self.displayed_values == 'profiles': 
            return 'rad_names', 'times' 
        else: 
            return 'signal_names', None

    def get_signal(self, name1, name2): 
        if self.displayed_values == 'profiles': 
            r, t, y = self.res.find_profile(name1, time=float(name2))
            return r, y
        else: 
            t, y = self.res.find_signal(name1)
            return t, y


    def get_names1(self): 
        if self.displayed_values == 'profiles': 
            return self.res.rad_names
        else: 
            return self.res.time_names

    def get_names2(self, name1): 
        if self.displayed_values == 'profiles': 
            result = [('%.3f' % t) for t in self.res.rad_times]
            return result
        else: 
            return None
            
#             v6.2.1       v6.2.1    v7.0    v7.0
#resnames = ["t15conOH3", "33957a", "test", "GG2"]

res = ResFile("res/33957a")
res.header.display()
print('last profile name: ', res.rad_names[-1])

#viewer = Viewer(AstraResViewerAdapter(res, 'signals'))
viewer = Viewer(AstraResViewerAdapter(res, 'profiles'))
