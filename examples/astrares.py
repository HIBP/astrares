# -*- coding: utf-8 -*-
"""
Created on Fri Sep 13 12:21:09 2019

@author: reonid
mailto: reonid@yahoo.com

Reads data from ASTRA res-file, result of modelling of code ASTRA* 
  *Automated System for TRansport Analysis (c) G.V.Pereverzev, P.N.Yushmanov

Res-file has the following general structure:
    Signature
    Text (Model + Log)
    Header 
    Frames[]

Versions of Astra: 
    6.2.1 - OK
    7.0   - OK ??? only a few files hes been tested

Example of using
    res = ResFile("GG2")

    # time signal
    tt, yy = res.find_signal('<ne>')
    plt.plot(tt, yy)

    # profile one-by-one
    rr, t, yy = res.find_profile('Te', time=0.00198729)
    plt.plot(rr, yy)

"""
import os.path  # os.path.getsize(path)
import numpy as np
import struct
from textwrap import wrap
#import matplotlib.pyplot as plt

ASTRA_NRD = 501
ASTRA_NRW = 128
ASTRA_NCONST = 256
ASTRA_NARRX = 67
ASTRA_NSBMX = 20
ASTRA_NRDX = 200
ASTRA_NTVAR = 25000
ASTRA_NTARR = 25000
ASTRA_NEQNS = 19

ASTRA_RES_SIGNATURE = '^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^'

RELATIVE_POS = 1
ABSOLUTE_POS = 0

class AstraResError(Exception):
    pass

class NotAString(Exception):
    pass

class EndOfFile(Exception):
    pass

class ProfileNotFound(Exception):
    pass

class ProfileOutOfIndex(Exception):
    pass


#%%   common read utils

def little_endian(type_):
    return np.dtype(type_).newbyteorder('<')
    
def read_long(file): 
    b = file.read(4)  # ??? returns 0 if file exhausted
    if len(b) == 0: 
        raise EndOfFile
    #return int.from_bytes(b, byteorder='little', signed=True)
    return struct.unpack("<l", b)[0]

def read_byte(file): 
    b = file.read(1)
    #return int.from_bytes(b, byteorder='little')
    return struct.unpack("<b", b)[0]


def read_double(file): 
    b = file.read(8)
    tpl = struct.unpack("<d", b)
    return tpl[0]

def dump(filename, src_file=None, size=None, data_bytes=None): 
    with open(filename, 'wb') as dumpfile: 
        if src_file is not None: 
            pos = src_file.tell()
            b = src_file.read(size)
            dumpfile.write(b)
            src_file.seek(pos, ABSOLUTE_POS)
        else:
            dumpfile.write(data_bytes)

#%%   specific read utils
    
def read_packet_size(file, previous=None, max_size=None):
    size = read_long(file)
    if (previous is not None) and (size != previous): 
        raise AstraResError('Wrong packet format (%d != %d)' % (previous, size))
    if (max_size is not None) and (size > max_size): 
        raise AstraResError('Too big packet')
    return size

def _read_packet(file): 
    N = read_packet_size(file)
    b = file.read(N)
    if len(b) == 0: 
        raise EndOfFile
    _ = read_packet_size(file, N)
    return b

def read_str_packet(file): 
    N = read_packet_size(file)  # 4 bytes   packet size
    L = read_byte(file)         # 1 byte    string length 
    if N != L+1: 
        file.seek(-5, RELATIVE_POS)  # moves the file position back
        raise NotAString

    b = file.read(L)

    _ = read_packet_size(file, N)
    return b.decode('cp1252')

def read_signature_packet(file): 
    N = read_packet_size(file, None, 32) # to prevent problems with files of other formats
    b = file.read(N)
    _ = read_packet_size(file, N)

    s = b.decode('cp1252')
    if s != ASTRA_RES_SIGNATURE: 
        raise AstraResError('Signature not found in the beginning of the file')
    return s

def read_packet(file, dtype): 
    if   dtype == 'str':  
        return read_str_packet(file)
    elif dtype == '^^^': 
        return read_signature_packet(file)
    elif dtype == '?': 
        return _read_packet(file)

    #--------------------- 
    b = _read_packet(file)
        
    if dtype == 'double': 
        return struct.unpack("<d", b)[0]
    elif dtype == 'long':  
        try: 
            return struct.unpack("<l", b)[0]
        except: 
            print('read_packet(file, "long"):   len(b) = %d (should be 4)' % len(b))
            raise EndOfFile
    elif dtype == 'double[]': 
        arr_len = len(b) // 8
        #return np.frombuffer(b, np.float64, arr_len)
        return np.frombuffer(b, little_endian(np.float64), arr_len)

def read_bin(file, dtype, length): 
    if dtype == 'str': 
        return file.read(length*1).decode('cp1252')

    elif dtype == 'char[4][]':
        s = file.read(length*4).decode('cp1252')
        return wrap(s, 4)     # [s[i:i+3] for i in range(0, len(s), 3)]
    elif dtype == 'char[6][]':
        s = file.read(length*6).decode('cp1252')   #, errors='ignore')
        return wrap(s, 6)     

    elif dtype == 'long[]':
        b = file.read(length*4)
        return np.frombuffer(b, little_endian(np.int32), length)
    elif dtype == 'short[]':
        b = file.read(length*2)
        return np.frombuffer(b, little_endian(np.int16), length)

    elif dtype == 'double[]':
        b = file.read(length*8)
        return np.frombuffer(b, little_endian(np.float64), length)
    elif dtype == 'float[]':
        b = file.read(length*4)
        return np.frombuffer(b, little_endian(np.float32), length)


#%%  Res file structure objects

def _convert(x, down, scale):
    return down + (32768 + x)*scale/65535.0

class ResProfile: 
    def __init__(self, file): 
        packet_size = read_packet_size(file)
        
        if packet_size == 4: # start of new Frame !!!
            file.seek(-4, RELATIVE_POS)  # moves the file position back
            raise ProfileNotFound

        self.scale = read_double(file)
        self.down = read_double(file)
         
        n = (packet_size - 2*8) // 2    # 8 = sizeof(double)
        self.raw_array = read_bin(file, 'short[]', n)
        self.array = np.empty(len(self.raw_array), dtype=little_endian(np.float64))
        self.array = _convert(self.raw_array, self.down, self.scale)

        _ = read_packet_size(file, packet_size)

#------------------------------------------------------------------------------

class ResFrame:     
    def __init__(self, file):    #def __init__(self, file, nprof): 
        # ------ 0, 1 or several slices of time signals -----
        # each with its own time instant
        nslices = read_packet(file, 'long')

        if nslices > 0: 
            merged_slices = read_packet(file, 'double[]')
            N = len(merged_slices) // nslices
            self.time_slices = [np.array(merged_slices[i*N:i*N+N]) for i in range(nslices)]
        else: 
            self.time_slices = []

        self.prof_time_stamp = read_packet(file, 'double') 
        self.const_values = read_packet(file, 'double[]')
        self.unknown_packet = read_packet(file, '?') #  usually filled with zero except the first byte 

        # ------ profiles -----
        self.profiles = []
        
        #for _ in range(nprof): 
        while True: 
            try: 
                prof = ResProfile(file)
                self.profiles.append(prof)
            except ProfileNotFound:    # in version 7 can be 6 or 7 unnamed profiles ???
                break # New Frame starts
            except EndOfFile: 
                break


#------------------------------------------------------------------------------

class ResOutputInfo: 
    def __init__(self, file, unmentioned_names): #, vers_1st_dig=None): 
        unmentioned_names = unmentioned_names.split(',')

        _nout = read_long(file)
        _names = read_bin(file, 'char[4][]', _nout)
        _scales = read_bin(file, 'double[]', _nout)

        k = len(unmentioned_names)
        self.names = [name.strip() for name in unmentioned_names + _names]
        self.scales = k*[1.0] + list(_scales)
        
        #if (vers_1st_dig == '6')or(vers_1st_dig is None): 
        #    k = len(unmentioned_names)
        #    self.names = [name.strip() for name in unmentioned_names + _names]
        #    self.scales = k*[1.0] + list(_scales)
        #elif vers_1st_dig == '7':   # ??? I'm not sure that one of unnamned shoul be added th the end... It's just a guess  
        #    k = len(unmentioned_names)
        #    self.names = [name.strip() for name in unmentioned_names + _names]
        #    self.names.append('#last')
        #    self.scales = k*[1.0] + list(_scales) + [1.0]
            
#------------------------------------------------------------------------------

class ResHeader: 
    def __init__(self, file): 
        file_pos = file.tell()
        # first packet of the header -------------------
        packet_size1 = read_packet_size(file)  
        
        self.rd_name = read_bin(file, 'str', 40).strip()
        self.eq_name = read_bin(file, 'str', 40).strip()
        self.version = read_bin(file, 'str', 32).strip(' \0') # ???
        self.xline1 = read_bin(file, 'str', 132).strip()
        
        #vers_1st_dig = self.version.split()[1][0]
        
        self.year = read_long(file)
        self.month = read_long(file)
        self.day = read_long(file)
        self.hour = read_long(file)
        self.minute = read_long(file)

        self.n_cf_nam = read_long(file)    
        self.n_pr_nam = read_long(file)
        
        self.rad_out_info = ResOutputInfo(file, "#radius, #x1, #x2, #x3, #x4, #x5, #x6")
                                              
        self.time_out_info = ResOutputInfo(file, "#time")
        
        b = file.read(8 + 4*4)
        self.hro, self.nb1, self.nsbr, self.ngr, self.nxout = struct.unpack("<dllll", b)

        self.leq = read_bin(file, 'long[]', 7)    # Note Change the cycle in NEQNS,(LEQ(j),j=1,NEQNS)
        
        _ = read_packet_size(file, packet_size1) # end of the first packet
        
        # second packet of the header -------------------
        _ = read_packet_size(file)     # packet_size2
        
        if self.nxout > 0: 
            self.kto = read_bin(file, 'long[]', self.ngr)
            self.ngridx = read_bin(file, 'long[]', self.ngr)
            self.ntypex = read_bin(file, 'long[]', self.ngr)
            self.timex = read_bin(file, 'double[]', self.ngr)
            self.gdex = read_bin(file, 'long[]', self.ngr)
            self.gdey = read_bin(file, 'long[]', self.ngr)
            self.datarr = read_bin(file, 'float[]', self.gdey[self.ngr-1] + self.ngridx[self.ngr-1]-1) 
            self.namex = read_bin(file, 'char[6][]', ASTRA_NARRX)
            self.nwindx = read_bin(file, 'long[]', ASTRA_NARRX) 
            self.kogda = read_bin(file, 'long[]', ASTRA_NARRX)
        else:
            self.kto, self.ngridx, self.ntypex, self.timex = None, None, None, None
            self.gdex, self.gdey = None, None
            self.datarr, self.namex, self.nwindx, self.kogda = None, None, None, None
        
        # ??? we do not reach the end of the second packet yet
        # but the rest of the second packet is ignored
        
        #ntout = len(self.time_out_info.names)-1
        #nrout = len(self.rad_out_info.names)-7
        
        # ??? 
        #self.jtout = read_long(file)
        #if self.jtout != 0: 
        #    ltouto = ???
        #    ltout = ltouto + self.jtout - 1 # ???
        #    
        #    for i in range(ntout): 
        #        ttout = read_double(file)
        #        tout = read_bin(file, 'double[]', ltout - ltouto)  # J=LTOUTO, LTOUT-1
        


        # 
        file.seek(file_pos, ABSOLUTE_POS)
        self._packet0 = read_packet(file, '?')
        
        file_pos = file.tell()
        self._packet1 = read_packet(file, '?')
        if len(self._packet1) == 4: 
            file.seek(file_pos, ABSOLUTE_POS)
    
    def display(self): 
        print('------- ASTRA res-file header -------')
        print('  ', self.rd_name)
        print('  ', self.eq_name)
        print('  ', self.version)
        print('  ', self.xline1)
       

def get_const_names(str_list): 
    result = []
    section = 0
    for s in str_list: 
        if s.lower().find('constants:') > -1: 
            section += 1
        elif (section == 1)and(s.find('=') == -1): 
            section += 1
        elif section == 1:
            cname = s.split('=')[0]
            cname = cname.strip()
            result.append(cname)
    
    return result

#%%  Res file main object

class ResFile: 
    def __init__(self, filename): 
        self.filename = filename
        self.filesize = os.path.getsize(filename)
        
        self.log = []
        self.model = []
        self.frames = [] 
        with open(filename, "rb") as file: 
            # read signature ------------------------------
            _ = read_signature_packet(file)
            
            # read model and log --------------------------
            section = 0
            while True: 
                try:
                    s = read_packet(file, 'str')
                    if s == ASTRA_RES_SIGNATURE: # diveider between model section and log section
                        section += 1
                    elif section == 0: 
                        self.model.append(s)
                    elif section == 1: 
                        self.log.append(s)
                    else: 
                        continue
                    
                except NotAString: 
                    break
                
            self.const_names = get_const_names(self.log)
               
            # read header  (2 packets) --------------------
            self.header = ResHeader(file)

            # read frames  --------------------------------
            while True: 
                try: 
                    # frame = ResFrame(file, len(self.rad_names)) # ??? I don't know the exact number of the unnamed profiles 
                    frame = ResFrame(file) 
                    self.frames.append(frame)
                except EndOfFile:
                    break   #OK                    
                except BaseException as e: 
                    print(type(e).__name__, ": '", e, "'")
                    print('WARNING! Not all the frames has been readed!')
                    break
            
            self._last_file_pos = file.tell()
            if self._last_file_pos != self.filesize: 
                print('WARNING! End of the file not reached!')
                
            
            # ---------------------------------------------
            self._actualize_profile_name_list()

            self.rad_times = self.extract_time_array('rad')
            self.time_times = self.extract_time_array('time')

            self.rad_names = self.header.rad_out_info.names
            self.time_names = self.header.time_out_info.names
   
    def _actualize_profile_name_list(self): 
        # correction of the rad names -----------------
        n = self.get_profile_count()
        n_ = len(self.header.rad_out_info.names)                
        if n_ > n: 
            print('WARNING! Actual profile number is less the expected number')
            self.header.rad_out_info.names = self.header.rad_out_info.names[0:n]  # remove "#last" if needed
            self.header.rad_out_info.scales = self.header.rad_out_info.scales[0:n]
        elif n_ < n: 
            # Just for the case. 
            print('WARNING! Actual profile number exceeds the expected number')
            self.header.rad_out_info.names.extend(['#last', '#last2', '#last3', '#last4', '#last5'][0:n-n_])
            self.header.rad_out_info.scales.extend( [1.0]*(n-n_) )

    def extract_time_array(self, kind): 
        tt = []
        if kind == 'time': 
            for fr in self.frames: 
                for time_slice in fr.time_slices: 
                    tt.append(time_slice[0])
        elif kind == 'rad': 
            for fr in self.frames: 
                tt.append(fr.prof_time_stamp)
        return np.array(tt)

    def get_frame_count(self): 
        return len(self.frames)  # len(self.rad_times)

    def get_signal_count(self): 
        return len(self.header.time_names)
        
    def get_profile_count(self): 
        # return len(self.header.rad_names)
        if len(self.frames) == 0: 
            return 0
        else:
            return len(self.frames[0].profiles)

    def find_profile(self, name, index=None, time=None):   
        name_idx = name if isinstance(name, int) else self.rad_names.index(name)
        if name_idx == -1: 
            raise AstraResError('no radial rpofile ' + str(name) )
        
        if index is None: 
            index = np.searchsorted(self.rad_times, time)
            if index >= len(self.rad_times): 
                index = len(self.rad_times) - 1
        
        if index >= self.get_frame_count(): 
            raise ProfileOutOfIndex
        
        t = self.rad_times[index]
        rr = self.frames[index].profiles[0].array
        yy = self.frames[index].profiles[name_idx].array
        return rr, t, yy

    def find_signal(self, name): 
        idx = name if isinstance(name, int) else self.time_names.index(name)
        result = []
        for fr in self.frames: 
            for time_slice in fr.time_slices: 
                result.append(time_slice[idx])
        return self.time_times, np.array(result)



#%%  

if __name__ == '__main__':
    pass

