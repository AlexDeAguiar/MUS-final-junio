import numpy as np
import sounddevice as sd   # modulo de conexión con portAudio
import soundfile as sf     # para lectura/escritura de wavs
import kbhit

class fm:
    def __init__(self, bitRate, chunkSize, listaFreqs=[], vol=1):
        self.bitRate = bitRate # ~= SRATE
        self.chunkSize = chunkSize
        self.vol = vol

        #Frecuencia por defecto
        self.listaFreqs = listaFreqs

        # Posición actual del bit a rellenar en el frame que vayamos a devolver (para saber si empezar a generar las ondas en fase 0 (si es el primer bit) o en otra fase si ya hemos generado chunks anteriores)
        self.currPos = 0


    def setListaFreqs(self, listaFreqs):
        self.listaFreqs = listaFreqs
    
    def getListaFreqs(self):
        return self.listaFreqs
    
    def addFreq(self, freq):
        self.listaFreqs.append(freq)
  
    def setVol(self, vol):
        self.vol = vol

    def getVol(self):
        return self.vol

    def getNextChunk(self):
        currChunk = np.arange(self.chunkSize) + self.currPos
        samples = np.zeros(self.chunkSize,dtype=np.float32) + self.currPos #TO DO: revisar porque se hace + currPos

        for i in range(len(self.listaFreqs)-1,-1,-1):
            samples = self.listaFreqs[i][1] * np.sin(2*np.pi*self.listaFreqs[i][0]*currChunk/self.bitRate + samples)
        
        return samples * self.vol
    


def main():
    SRATE = 44100       # sampling rate, Hz, must be integer
    CHUNK = 128
    stream = sd.OutputStream(samplerate=SRATE,blocksize=CHUNK,channels=1)  
    stream.start()

    kb = kbhit.KBHit()
    c = ' '

    myFm = fm(SRATE, CHUNK, listaFreqs=[[220,0.8]], vol = 0.1)


    # [(fc,vol),(fm1,beta1),(fm2,beta2),...]
    #frecs = [[220,0.8],[220,0.5],[110,0.3]]

    #fc, fm = 220, 220
    #frecs = [[fc,0.8],[fc+fm,0.5],[fc+2*fm,0.3],[fc+3*fm,0.2]]

    while True:
        samples = myFm.getNextChunk()
        stream.write(np.float32(samples)) 


        if kb.kbhit():
            c = kb.getch()
            if c =='q': break
        

    stream.stop()

#Ejecutar el programa:------------------------------------
if __name__ == "__main__":
    main()
