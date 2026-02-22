def reports(a:str):
    f1=open(a,"r")
    b=f1.read()
    f1.close()
    
    c=b.split("\n")
    d=[]
    e=[]
    f=[]
    h=[]
    counter=0
    
    for n in c:
        n=n.strip()
        if n!="":
            d=n.split(",")
            counter2=0
            for m in d:
                m=m.strip()
                if counter==0:
                    g=len(m)
                    e=e+[g]
                else:
                    if len(d)!=len(e):
                        print("error")
                        
                if e[counter2]<len(m):
                    e[counter2]=len(m)
                    
                f=f+[m]
                counter2=counter2+1
            h=h+[f]
            f=[]
            counter=counter+1
    counter=0
    #print(e)
    #print(h)
    #exit(0)
    total=len(e)+1
    for n in e:
        total=total+e[counter]
        counter=counter+1
    print("-"*total)
    counter=0    
    for n in h:    
        counter2=0
        print("|",end="")
        for m in n:
            i=e[counter2]-len(m)
            print(m+" "*i+"|",end="")
            counter2=counter2+1
        print("")
            
    print("-"*total)
    
