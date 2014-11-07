import ModParsetType
import glob
import os

def Go():

    D=ModParsetType.ParsetToDict("BatchNDPPP.parset")
    
    ll=sorted(glob.glob("L242544_SB1??_uv.dppp.MS"))

    for f in ll:
        MSIN=f
        MSOUT=f+".dppp"
        D["msin"]["val"]=MSIN
        D["msout"]["val"]=MSOUT
        D["steps"]["val"]="[preflag,flag1,avg1]"
        ModParsetType.DictToParset(D,"tmpParset")
        os.system("NDPPP tmpParset")
