

def DictToFile(Dict,fout):
    f=open(fout,"w")
    Lkeys=Dict.keys()
    
    for key in Lkeys:
        keyw=key
        f.write("%s = %s\n"%(keyw,Dict[key]))
    f.close()

def FormatValue(ValueIn):

    if "#" in ValueIn:
        ValueIn=ValueIn.split("#")[0]
    MayBeInt=False
    if not("." in ValueIn): MayBeInt=True
    if "True" in ValueIn:
        Value=True
    elif "False" in ValueIn:
        Value=False
    elif "None" in ValueIn:
        Value=None
    elif '"' in ValueIn:
        Value=ValueIn.replace(" ","").replace('"',"")
    elif ("[" in ValueIn):

        Value0=ValueIn[1:-1].split(",")
        try:
            Value=[float(v) for v in Value0]
        except:
            Value=Value0
    elif ("," in ValueIn):
        Value0=ValueIn.split(",")
        try:
            Value=[float(v) for v in Value0]
        except:
            Value=Value0
        
    else:
        try:
            Value=float(ValueIn)
            if MayBeInt: Value=int(Value)
        except:
            Value=ValueIn
            Value=Value.replace(" ","")
    return Value


def setValue(Dico,key,Value):
    keys=key.split(".")
    Nlev=len(keys)
    ZeroKey=keys[0]

    if Nlev==1:
        Dico[ZeroKey]=Value
    else:
        NewKey=".".join(keys[1::])
        if not(ZeroKey in Dico.keys()):
            Dico[ZeroKey]={}
        setValue(Dico[ZeroKey],NewKey,Value)


def FileToDict(fname,DicoKeys=None):
    if DicoKeys==None:
        DicoDefault={}
    else:
        DicoDefault=DicoKeys
    Dict={}


    f=file(fname,"r")
    ListOut=f.readlines()
    order=[]
    i=0
    for line in ListOut:
        if line=='\n': continue
        if line[0]=="#": continue
        if line[0]=="$":
            key,val=line[1::].split("=")
            DicoDefault[key]=val
            continue
        if line[0:5]=="input":
            _,a=line[5::].split('{')
            subfile,_=a.split('}')
            FileToDict(subfile,AppendToDico=Dict)
            continue
        key,val=line[0:-1].split("=")
        key=key.replace(" ","")
        key=key.replace("\t","")
        val=val.replace(" ","")
        if val[0]=="$":
            VarName=val[1::]
            if VarName in DicoDefault.keys():
                val=DicoDefault[VarName]

        valFormat=FormatValue(val)


        Dict[key]=valFormat
        #setValue(Dict,key,valFormat)
    return Dict

def test():
    D=FileToDict("Templates/NDPPP.parset",DicoKeys={"MS_IN":"lala"})
    DictToFile(D,"TestParset")

