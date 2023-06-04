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
        
        #TODO: ver que pasa con esta linea
        #self.currPos += self.chunkSize
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
                currNotas.append([nota[0], 0.5]) #Añade su frecuencia

        self.currPos += self.chunkSize
        return currNotas

class AbcInput:
    def __init__(self):
        return

    def setIndiceMelodia(self, X): #1, 2, 3...
        self.IndiceMelodia = X

    def setTitulo(self, T):
        self.titulo = T

    def setCompas(self, M): #2/4, 3/4, 4/4, 6/8, ... 
        self.compas = M

    def setDuracionNotaPorDefecto(self, L): #si no se indica lo contrario, esta sera la duracion de cualquier nota que se indique (ejemplo: 1/8, 1/4, ...)
        self.duracionNotaPorDefecto = L

    def setTipoMelodia(self, R):
        self.tipoMelodia = R
        
    def setKey(self, K): #clave de sol, de fa...
        self.key = K

    def setNotas(self, notas):
        self.notas = notas

    def getNotas(self):
        return self.notas

def isNum(c):
    return c.isnumeric()

def getNum(c):
    return int(c)

def leeArchivo(pathArchivo):
    file = open(pathArchivo, "r")
    archivoStr = file.read()
    lineas = archivoStr.splitlines()

    abc = AbcInput()
    #            Do       RE       MI       FA       SOL      LA      SI      do'     re'     mi'     fa'     sol'     la'      si'
    notasExpI = {"C": -9, "D": -7, "E": -5, "F": -4, "G": -2, "A": 0, "B": 2, "c": 3, "d": 5, "e": 7, "f":8 , "g":10 , "a": 12, "b": 14}

    notas = []
    for linea in lineas:      
        if (len(linea) >= 3 and linea[1] == ":"): #Headers
            aux = linea.split(":")
            parteIzq = aux[0]
            parteDer = aux[1]

            if (parteIzq == "X"):
                abc.setIndiceMelodia(parteDer)
            elif (parteIzq == "T"):
                abc.setTitulo(parteDer)
            elif (parteIzq == "M"):
                abc.setCompas(parteDer)
            elif (parteIzq == "L"):
                abc.setDuracionNotaPorDefecto(parteDer)
            elif (parteIzq == "R"):
                abc.setTipoMelodia(parteDer)
            elif (parteIzq == "K"):
                abc.setKey(parteDer)
            else:
                print("---ERROR---"),
                print("No se ha podido proicesar la linea:")
                print(linea)
                print("==========")
        else:
            #seccion con notas
            prevChar = ""
            for c in linea:
                if isNum(c):
                    if prevChar == "|":
                        prevChar = c
                        continue #Numero para marcar que compas tocar en una repeticion
                    else:
                        freq = notas[-1][0]
                        notas[-1] = [freq, getNum(c)]
                if c in notasExpI:
                    i = notasExpI[c]
                    freq = 440 * (2 ** (i / 12)) #440 * 2^(i/12)
                    notas.append([freq,1])
                prevChar = c

    abc.setNotas(notas)
    return abc


        
    



##[[220, 1][440, 2]], 100


def main(abc):
    SRATE = 44100       # sampling rate, Hz, must be integer
    CHUNK = 128
    stream = sd.OutputStream(samplerate=SRATE,blocksize=CHUNK,channels=1)  
    stream.start()

    kb = kbhit.KBHit()
    c = ' '

    myFm = Fm(SRATE, CHUNK, vol = 0.05)
    myPartitura = Partitura(SRATE, CHUNK, abc.getNotas() , 60)


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
    abc = leeArchivo("input.txt")
    main(abc)

