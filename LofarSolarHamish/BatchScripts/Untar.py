import glob
ll=glob.glob("SRM*tar")
for f in ll:
    NameMS=f.split("2F")[-1]
    os.system("mv %s %s"%(f,NameMS))
    os.system("tar -xvf %s"%NameMS)
