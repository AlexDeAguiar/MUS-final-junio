import numpy as np
import sounddevice as sd   # modulo de conexión con portAudio
import soundfile as sf     # para lectura/escritura de wavs
import kbhit

class Fm:
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
        
        self.currPos += self.chunkSize
        return samples * self.vol
    
class Partitura: 
    def __init__(self, bitRate, chunkSize, listaNotas, bpm): #sintaxis lista: [[freq, dur]] dur = 1 es una negra, dur = 2 es una blanca, dur = 0.5 es una corchea...
        self.bitRate = bitRate # ~= SRATE
        self.chunkSize = chunkSize

        
        self.currPos = 0
        self.bpm = bpm
        self.bitsPerBeat = self.bitRate/(self.bpm/60)

        self.listaNotasConMomentos = []

        ini = 0
        for nota in listaNotas:
            self.listaNotasConMomentos.append([nota[0], ini, ini + nota[1] * self.bitsPerBeat]) #nota[0] -> freq, nota[1] -> duracion en negras
            ini += nota[1] * self.bitsPerBeat


    def getNextChunk(self):
        currNotas = []
        for nota in self.listaNotasConMomentos:
            if nota[1] <= self.currPos and nota[2] > self.currPos: #Para cada nota que se tenga que tocar en este chunk
                currNotas.append([nota[0], 1]) #Añade su frecuencia

        self.currPos += self.chunkSize
        return currNotas
            

        

        
    



##[[220, 1][440, 2]], 100


def main():
    SRATE = 44100       # sampling rate, Hz, must be integer
    CHUNK = 128
    stream = sd.OutputStream(samplerate=SRATE,blocksize=CHUNK,channels=1)  
    stream.start()

    kb = kbhit.KBHit()
    c = ' '

    myFm = Fm(SRATE, CHUNK, vol = 0.2)
    myPartitura = Partitura(SRATE, CHUNK, [[220,1], [440, 2], [220,1], [330, 2]], 60)


    # [(fc,vol),(fm1,beta1),(fm2,beta2),...]
    #frecs = [[220,0.8],[220,0.5],[110,0.3]]

    #fc, fm = 220, 220
    #frecs = [[fc,0.8],[fc+fm,0.5],[fc+2*fm,0.3],[fc+3*fm,0.2]]

    while True:
        myFm.setListaFreqs(myPartitura.getNextChunk())
        samples = myFm.getNextChunk()
        stream.write(np.float32(samples)) 


        if kb.kbhit():
            c = kb.getch()
            if c =='q': break
        

    stream.stop()

#Ejecutar el programa:------------------------------------
if __name__ == "__main__":
    main()
