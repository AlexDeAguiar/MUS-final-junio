print("hola")





class OscWaveTable:
    def __init__(self, bitRate, chunkSize):
        self.bitRate = bitRate
        self.chunkSize = chunkSize
        

        # un ciclo completo de seno en [0,2pi)
        t = np.linspace(0, 1, num=chunkSize)
        self.waveTable = np.sin(2 * np.pi * t)

        # arranca en 0
        self.fase = 0

        #Frecuencia por defecto
        self.freq = 440

        # paso en la wavetable en funcion de frec y RATE
        self.step = self.size/(SRATE/self.frec)

    def setFrec(self,frec): 
        self.frec = frec
        self.step = self.size/(SRATE/self.frec)

    def getFrec(self): 
        return self.frec    

    def setVol(self, vol):
        self.vol = vol

    def getVol(self):
        return self.vol

    def getChunk(self):
        samples = np.zeros(CHUNK,dtype=np.float32)
        cont = 0
        #print("RATE ",RATE, "   frec ",self.frec)
        
        while cont < CHUNK:
            self.fase = (self.fase + self.step) % self.size

            # con truncamiento, sin redondeo
            # samples[cont] = self.waveTable[int(self.fase)]

            # con redondeo
            #x = round(self.fase) % self.size
            #samples[cont] = self.waveTable[x]
                        
            # con interpolacion lineal                                    
            x0 = int(self.fase) % self.size
            x1 = (x0 + 1) % self.size
            y0, y1 = self.waveTable[x0], self.waveTable[x1]            
            samples[cont] = y0 + (self.fase-x0)*(y1-y0)/(x1-x0)

            cont = cont+1
    
        return np.float32(self.vol*samples)





# sintesis fm con osciladores variables

import numpy as np         # arrays    
import sounddevice as sd   # modulo de conexión con portAudio
import soundfile as sf     # para lectura/escritura de wavs
import kbhit
import os            


SRATE = 44100       # sampling rate, Hz, must be integer
CHUNK = 1024


# fc, carrier = pitch, fm frecuencia moduladora, beta = indice de modulacion
def oscFM(fc,fm,beta,vol,frame):
    # sin(2πfc+βsin(2πfm))   http://www.mrcolson.com/2016/04/21/Simple-Python-FM-Synthesis.html
    sample = np.arange(CHUNK)+frame
    mod = beta*np.sin(2*np.pi*fm*sample/SRATE)
    res = np.sin(2*np.pi*fc*sample/SRATE + mod)
    return vol*res
    
stream = sd.OutputStream(samplerate=SRATE,blocksize=CHUNK,channels=1)  
stream.start()



kb = kbhit.KBHit()
c = ' '

fc = 440
fm = 300
beta = 1
vol = 0.8
frame = 0

while c!='q':
    samples = oscFM(fc,fm,beta,vol,frame)
   
    stream.write(np.float32(0.5*samples)) 

    
    frame += CHUNK

    if kb.kbhit():
        os.system('clear')
        c = kb.getch()
        print(c)        
        if c =='q': break
        elif c=='C': fc += 1
        elif c=='c': fc -= 1    
        elif c=='M': fm += 1    
        elif c=='m': fm -= 1            
        elif c=='B': beta += 0.1    
        elif c=='b': beta -= 0.1            

        print("[C/c] Carrier (pitch): ", fc)
        print("[M/m] Frec moduladora: ", fm)
        print("[B/b] Factor (beta): ",beta)
        print("q quit")

stream.stop()














# sintesis fm con multiples moduladores

import numpy as np         # arrays    
import sounddevice as sd   # modulo de conexión con portAudio
import soundfile as sf     # para lectura/escritura de wavs
import kbhit
import os


SRATE = 44100       # sampling rate, Hz, must be integer
CHUNK = 16


'''
# fc, carrier = pitch, fm frecuencia moduladora, beta = indice de modulacion
def oscFM(fc,fm,beta,vol,frame):
    # sin(2πfc+βsin(2πfm))   http://www.mrcolson.com/2016/04/21/Simple-Python-FM-Synthesis.html
    interval = np.arange(CHUNK)+frame
    mod = beta*np.sin(2*np.pi*fm*interval/RATE)
    res = np.sin(2*np.pi*fc*interval/RATE + mod)
    return (vol*res).astype(np.float32)
'''    

# [(fc,vol),(fm1,beta1),(fm2,beta2),...]
def oscFM(frecs,frame):
                                          # sin(2πfc+βsin(2πfm))  
    chunk = np.arange(CHUNK)+frame
    samples = np.zeros(CHUNK)+frame
    # recorremos en orden inverso
    
    for i in range(len(frecs)-1,-1,-1):
        samples = frecs[i][1] * np.sin(2*np.pi*frecs[i][0]*chunk/SRATE + samples)
    return samples

    '''
    mod = frecs[i][1] * np.sin(2*np.pi*frecs[i][0]*chunk/RATE)
    res = np.sin(2*np.pi*fc*interval/RATE + mod)
    return (vol*res).astype(np.float32)
    '''

stream = sd.OutputStream(samplerate=SRATE,blocksize=CHUNK,channels=1)  
stream.start()

kb = kbhit.KBHit()
c = ' '


# [(fc,vol),(fm1,beta1),(fm2,beta2),...]
#frecs = [[220,0.8],[220,0.5],[110,0.3]]

fc, fm = 220, 220
frecs = [[fc,0.8],[fc+fm,0.5],[fc+2*fm,0.3],[fc+3*fm,0.2]]

frame = 0

while True:
    samples = oscFM(frecs,frame)   
    stream.write(np.float32(0.9*samples)) 

    frame += CHUNK

    if kb.kbhit():
        os.system('clear')
        c = kb.getch()
        
        if c =='z': break
        elif (c>='a' and c<='x'):
            v = ord(c)-ord('a')
            if v<len(frecs): frecs[v][1] = max(0,frecs[v][1]-0.01)
        elif (c>='A' and c<='X'):
            v = ord(c)-ord('A')
            if v<len(frecs): frecs[v][1] = min(3,frecs[v][1]+0.01) 
        print("z quit")
        for i in range(len(frecs)): 
            print("["+str(chr(ord('A')+i))+"/"+str(chr(ord('a')+i))+"] ", " Frec " , frecs[i][0],"  beta: ",frecs[i][1])
      

stream.stop()











class OscWaveTable:
    def __init__(self, frec, vol, size):
        self.frec = frec
        self.vol = vol
        self.size = size
        # un ciclo completo de seno en [0,2pi)
        t = np.linspace(0, 1, num=size)
        self.waveTable = np.sin(2 * np.pi * t)
        # arranca en 0
        self.fase = 0
        # paso en la wavetable en funcion de frec y RATE
        self.step = self.size/(SRATE/self.frec)

    def setFrec(self,frec): 
        self.frec = frec
        self.step = self.size/(SRATE/self.frec)

    def getFrec(self): 
        return self.frec    

    def setVol(self, vol):
        self.vol = vol

    def getVol(self):
        return self.vol

    def getChunk(self):
        samples = np.zeros(CHUNK,dtype=np.float32)
        cont = 0
        #print("RATE ",RATE, "   frec ",self.frec)
        
        while cont < CHUNK:
            self.fase = (self.fase + self.step) % self.size

            # con truncamiento, sin redondeo
            # samples[cont] = self.waveTable[int(self.fase)]

            # con redondeo
            #x = round(self.fase) % self.size
            #samples[cont] = self.waveTable[x]
                        
            # con interpolacion lineal                                    
            x0 = int(self.fase) % self.size
            x1 = (x0 + 1) % self.size
            y0, y1 = self.waveTable[x0], self.waveTable[x1]            
            samples[cont] = y0 + (self.fase-x0)*(y1-y0)/(x1-x0)

            cont = cont+1
    
        return np.float32(self.vol*samples)