#!/usr/bin/env python

import numpy as np
from Tools import ClassMS
import numpy.linalg
from Tools import ModColor
import lofar.stationresponse as lsr
import sys
import os
from Tools.progressbar import ProgressBar
import tables
from Tools import ModLinAlg

class HDF5():
    def __init__(self,FileIn,Mode="APR"):
        self.hdf5file=FileIn
        self.Mode=Mode
        self.Load()

    def Load(self):
        self.T=tables.open_file(self.hdf5file,"r")
        self.ShapeSol=self.T.root.sol000.amplitude000.val.shape
        self.Npol, self.Ndir, self.na, self.nf, self.nt=self.ShapeSol
        self.times=self.T.root.sol000.amplitude000.time[:]
        self.freqs=self.T.root.sol000.amplitude000.freq[:]
        self.amplitudes=self.T.root.sol000.amplitude000.val
        self.rotation=self.T.root.sol000.rotation000.val
        self.phases=self.T.root.sol000.phase000.val


    def GiveJones(self,timeIn,freqs):
        Mode=self.Mode
        time=np.mean(timeIn)
        Dt=np.abs(time-self.times)
        indt=np.argmin(Dt)
        DF=np.abs(self.freqs.reshape(self.freqs.size,1)-freqs.reshape(1,freqs.size))
        indf=np.argmin(DF,axis=0)
        DF/=1e6


        if "A" in Mode:
            AmpRead=self.T.root.sol000.amplitude000.val[:,:,:,:,indt][:,0,:,:][:,:,indf].T.copy()
            Amp=np.zeros((freqs.size, self.na, 2, 2),dtype=np.float32)
            Amp[:,:,0,0]=AmpRead[:,:,0]
            Amp[:,:,1,1]=AmpRead[:,:,1]
        else:
            Amp=np.zeros((freqs.size, self.na, 2, 2),dtype=np.float32)
            Amp[:,:,0,0]=1
            Amp[:,:,1,1]=1

        if "P" in Mode:
            PhasesRead=self.T.root.sol000.phase000.val[:,:,:,:,indt][:,0,:,:][:,:,indf].T.copy()
            Phases=np.zeros((freqs.size, self.na, 2, 2),dtype=np.float32)
            Phases[:,:,0,0]=PhasesRead[:,:,0]
            Phases[:,:,1,1]=PhasesRead[:,:,1]
        else:
            Phases=np.zeros((freqs.size, self.na, 2, 2),dtype=np.float32)


        Jones=Amp*np.exp(1j*Phases)

        DicoOut={"AP":Jones}


        if "R" in Mode:
            RotRead=self.T.root.sol000.rotation000.val[:,:,:,indt][:,:,indf].T.copy()#*np.pi/180
        
            RotRead=-RotRead[:,:,0]
            RotMat=np.zeros((freqs.size, self.na, 2, 2),dtype=Jones.dtype)
            RotMat[:,:,0,0]=np.cos(RotRead)
            RotMat[:,:,1,1]=np.cos(RotRead)
            RotMat[:,:,0,1]=np.sin(RotRead)
            RotMat[:,:,1,0]=-np.sin(RotRead)
            #Jones=ModLinAlg.BatchDot(Jones,RotMat)

        DicoOut["R"]=RotMat


        return DicoOut



def ApplySols(MS=None,MSName="/media/tasse/data/TestSolarHamish/ApplySols/L242544_SB108_uv.dppp.MS.dppp/",
              InCol="DATA",OutCol="CORRECTED_DATA",
              HDF5Table="sun.h5",Mode="A",
              BeamParms=(True,-1)):


    if MS==None:
        MS=ClassMS.ClassMS(MSName,GetBeam=True,Col=InCol)
        MS.PutCasaCols()

    ApplyBeam,DtBeam=BeamParms
    if DtBeam==-1:
        DtBeam=MS.dt
    else:
        DtBeam*=60.
    
    Tmin,Tmax=MS.F_times.min(),MS.F_times.max()
    NTsols=int((Tmax-Tmin)/DtBeam)


    H=HDF5(HDF5Table)
    TimeSols=H.times
    DtSol=TimeSols[1]-TimeSols[0]




    

    pBAR= ProgressBar('white', block='=', empty=' ',Title="Beam Calc")

    nch=MS.ChanFreq.size
    

    for it in range(TimeSols.shape[0]):
        ThisSolTime=TimeSols[it]
        t0=ThisSolTime-DtSol/2.
        t1=ThisSolTime+DtSol/2.
        indSelMS=np.where((MS.times_all>t0)&(MS.times_all<t1))[0]
        ThisData=MS.data[indSelMS].copy()
        

        # Jones=np.zeros((MS.na,nch,2,2),dtype=np.complex128)
        # Jones[:,:,0,0]=1
        # Jones[:,:,1,1]=1

        DicoJonesHDF5=H.GiveJones(ThisSolTime,MS.ChanFreq.flatten())
        
        JonesAP=DicoJonesHDF5["AP"]
        JonesAP=np.swapaxes(JonesAP,0,1)
        Jones=JonesAP

        if ApplyBeam:
            Beam=MS.GiveBeam(ThisSolTime)[0]
            Jones=ModLinAlg.BatchDot(Jones,Beam)

        if "R" in DicoJonesHDF5.keys():
            JonesR=DicoJonesHDF5["R"]
            JonesR=np.swapaxes(JonesR,0,1)
            Jones=ModLinAlg.BatchDot(Jones,JonesR)

        JonesH=ModLinAlg.BatchH(Jones)
        Jones=ModLinAlg.BatchInverse(Jones)
        JonesH=ModLinAlg.BatchInverse(JonesH)

        A0=MS.A0[indSelMS]
        A1=MS.A1[indSelMS]

        P0=ModLinAlg.BatchDot(Jones[A0,:,:],ThisData)
        dataCorr=ModLinAlg.BatchDot(P0,JonesH[A1,:,:])

        nrow,nch,_,_=dataCorr.shape

        MS.data[indSelMS]=dataCorr.reshape((nrow,nch,4))



        pBAR.render(int(100*float(it+1)/TimeSols.shape[0]), '%i/%i' % (it+1,TimeSols.shape[0]))



    MS.SaveVis(Col=OutCol)


if __name__=="__main__":
    import optparse
    desc="""Applysols Questions and suggestions: cyril.tasse@obspm.fr"""
    opt = optparse.OptionParser(usage='Usage: %prog --ms=somename.MS <options>',version='%prog version 1.0',description=desc)
    group = optparse.OptionGroup(opt, "* ", "Won't work if not specified.")
    group.add_option('--ms',help='Input MS to draw [no default]',default='')
    group.add_option('--HDF5Table',help='Name of the HDF5 file [no default]',default='')
    group.add_option('--HDF5Mode',help='What to apply from the HDF5 file. "A" for Amplitude, "R" for Rotation, "P" for Phase [default %default]',default='A')
    group.add_option('--ApplyBeam',help='Apply the beam model [default %default]',default='1')
    group.add_option('--DtBeam',help='Time insterval [no default]',default='10')
    group.add_option('--InOut',help='Input output comuln [default %default]',default='DATA,CORRECTED_DATA')
    opt.add_option_group(group)
    O, arguments = opt.parse_args()
    InCol,OutCol=O.InOut.split(",")

    Am I 

    BeamParms=((O.ApplyBeam=="1"),float(O.DtBeam))

    ApplySols(MSName=O.ms,
              InCol=InCol,OutCol=OutCol,
              HDF5Table=O.HDF5Table,Mode=O.HDF5Mode,
              BeamParms=(O.ApplyBeam,-1))

