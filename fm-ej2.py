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
