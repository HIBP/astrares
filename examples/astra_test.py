# -*- coding: utf-8 -*-
"""
Created on Mon Jan 31 12:43:41 2022

@author: reonid
"""

from astrares import ResFile

class TestFailed(Exception):
    pass

def test_resfile(filename, expected_version, expected_last_profile): 
    res = ResFile(filename)
    ver = res.header.version.split()[1][0]
    
    if ver != expected_version: 
        raise TestFailed('Version expected to be %d' % expected_version)

    if res.rad_names[-1] != expected_last_profile: 
        raise TestFailed('Last profile not reached %s' % res.rad_names[-1])

    if res.filesize != res._last_file_pos:
        raise TestFailed('The end of the res-file not reached')
    
    rr, t, yy = res.find_profile(expected_last_profile, index=0)
    
    print('test ', filename, ' passed')


def test_GG2(): 
    test_resfile("res/GG2", '7', '#last')  # ??? Unknown profile at the end ???

def test_test(): 
    test_resfile("res/test", '7', 'nT')

def test_33957a(): 
    test_resfile("res/33957a", '6', 'hev')

def test_t15conOH3(): 
    test_resfile("res/t15conOH3", '6', 'car2')

test_33957a()
test_t15conOH3()

test_GG2()  # WARNING is OK
test_test()
