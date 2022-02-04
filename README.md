# astrares

ASTRA res-file reader

Reads data from ASTRA res-file, result of modelling of code ASTRA* 
  *Automated System for TRansport Analysis (c) G.V.Pereverzev, P.N.Yushmanov

Allows to extract from the res-file the text of model and 
the data of the temporal signals and radial profiles. 

Res-file has the following general structure:
    Signature
    Text (Model + Log)
    Header 
    Frames[]

From the point of view of low level structure file is a sequence of packets. 
Each packet starts from its datalength (4-byte integer, little endian), further contains some data of specified length (in bytes)
and ends with the repetition of its datalength (the same 4-byte integer as in the beginning). 

One of the common packet types is the string packet. 
Its data block starts from the length of string (1-byte). 
Thus its datalength (4-byte) is always equal to the first data byte plus one. 
This criterion was taken to separate the text (model + log) from the header packet. 

The header consists of two packets
    The first packet contains model name, ASTRA version, names of the temporal signals and names of the profiles. 

    The second packet looks not important for the extracting the data and skipped. 

The data packed in frames. Each frame contains one or several temporal slices of the temporal signals
and set of the profiles at the fixed time instance. 
Thus every temporal signal is scattered over all the frames. 

The number of stored temporal signals and radial profiles differs from number of corresponding names keeped in header. 
    For the temporal signals this differense is 1, and first signal is obviously identified as time. Labeled "#time". 
    
    For the radial profiles this differense can be 7 or 8. 
    The first profile is idenfified as normalized radius (rho) and labeled as "#radius" 
    The next profiles (labeled "#1", "#2", "#3", "#4", "#5", "#6") looks like some magnetic coordinates. 

    In some res-files (found only in v7) there is one more unmentioned profile. 
    I labeled it "#last" and suppose that it is placed on the end of the sequence. It is only guess. 

All the profiles in one frame have the same length, 
but for the profiles in the different frames it is not always true. 
(Such cases are rare but can happen). 
Radial mesh also can differ for the different frames. 
 

Versions of Astra: 
    6.2.1 - OK
    7.0   - OK ??? only a few files were tested

Example of using
    res = ResFile("GG2")

    # time signal                                                                 
    tt, yy = res.find_signal('<ne>')
    plt.plot(tt, yy)

    # profile one-by-one
    rr, t, yy = res.find_profile('Te', time=0.00198729)
    plt.plot(rr, yy)