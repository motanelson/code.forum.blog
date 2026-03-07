import matplotlib.pyplot as plt
from scipy import stats
import copy
plt.style.use('dark_background')

# Dados

# Dados

def calcX(i:int):
   ii=[]
   for n in range(i):
       nn=[]
       ii.append(copy.copy(float(n)))
       xx=float(n)*2.25
       ii.append(copy.copy(xx))
       
   return ii
def calcY(X):
    ii=[]
    counter=0
    for n in range(0,len(X),2):
        xx=X[n+0]+X[n+1]
        ii.append(copy.copy(xx))
        ii.append(copy.copy(xx))
    return ii

X=calcX(20)
y=calcY(X)
# Gráfico
plt.scatter(X, y)
plt.show()
