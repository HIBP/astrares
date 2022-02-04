# -*- coding: utf-8 -*-
"""
Created on Thu Oct 10 15:51:12 2019

@author: reonid
"""


#import numpy as np
#import os.path  # os.path.getsize(path)
import matplotlib.pyplot as plt

from astrares import ResFile


def plot_one_profile_all_times(res_file, prof_name, skip_unnamed=True): 
    n = res_file.get_frame_count()
    for i in range(n): 
        rr, t, yy = res_file.find_profile(prof_name, index=i)
        label = 't=%f' % t
        if (skip_unnamed)&(label.startswith('#')): 
            continue; 
        plt.plot(rr, yy, label=label)
    plt.legend()
    plt.title('%s profiles' % prof_name)

def plot_all_temporal_signals(res_file, skip_unnamed=True): 
    for sig_name in res_file.time_names: 
        tt, yy = res_file.find_signal(sig_name)
        label = '%s' % (sig_name)
        if (skip_unnamed)&(label.startswith('#')): 
            continue; 
        plt.plot(tt, yy, label=label)
    plt.legend()
    plt.title('Temporal signals')

def plot_all_profile_at_fixed_time(res_file, desired_time, skip_unnamed=True): 
    for prof_name in res_file.rad_names: 
        rr, actual_time, yy = res_file.find_profile(prof_name, time=desired_time)
        label = '%s' % (prof_name)
        if (skip_unnamed)&(label.startswith('#')): 
            continue; 
        plt.plot(rr, yy, label=label)
    plt.legend()
    plt.title('Profiles t=%f' % actual_time)

def print_const_names(resfile): 
    names = resfile.const_names; 
    print('------- CONSTANTS: ------------------')    
    print(' '.join(names))


#             v6.2.1       v6.2.1    v7.0    v7.0
#resnames = ["t15conOH3", "33957a", "test", "GG2"]

res = ResFile("res/test")


res.header.display()
print_const_names(res)

plt.figure()
plot_one_profile_all_times(res, 'Ti')

plt.figure()
plot_all_temporal_signals(res) 

plt.figure()
plot_all_profile_at_fixed_time(res, 1.0)

