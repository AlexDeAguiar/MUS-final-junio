import numpy as np
import sounddevice as sd   # modulo de conexión con portAudio
import kbhit
import re

class OsciladorSeno:
    def __init__(self, bitRate, chunkSize, listaFreqsNotas=[], vol=1):
        self.bitRate = bitRate # ~= SRATE
        self.chunkSize = chunkSize
        self.vol = vol

        #Frecuencia por defecto
        self.listaFreqsNotas = listaFreqsNotas

        # Posición actual del bit a rellenar en el frame que vayamos a devolver (para saber si empezar a generar las ondas en fase 0 (si es el primer bit) o en otra fase si ya hemos generado chunks anteriores)
        self.fase = 0


    def setListaFreqsNotas(self, listaFreqsNotas):
        self.listaFreqsNotas = listaFreqsNotas
    
    def getListaFreqsNotas(self):
        return self.listaFreqsNotas
    
    def addFreqNota(self, freqNota):
        self.listaFreqsNotas.append(freqNota)
  
    def setVol(self, vol):
        self.vol = vol

    def getVol(self):
        return self.vol

    def getNextChunk(self):
        currChunk = np.arange(self.chunkSize)
        samples = np.zeros(self.chunkSize,dtype=np.float32) #TO DO: revisar porque se hace + currPos

        freq = self.listaFreqsNotas[0]
        samples = np.sin(currChunk*2*np.pi*freq/self.bitRate  + self.fase )
    
        numOndas = freq*self.chunkSize/self.bitRate
        faseOndas = self.fase /(2*np.pi)
        faseOndas += numOndas
        faseOndas -= np.trunc(faseOndas)
        self.fase = faseOndas * 2*np.pi
        
        return samples * self.vol

#---------------------------------------------------------------------------------------------------------------------------------

class FmSimple:
    def __init__(self, bitRate, chunkSize, factorMod = 1, listaFreqsNotas=[], vol=1):
        self.bitRate = bitRate # ~= SRATE
        self.chunkSize = chunkSize
        self.vol = vol

        #Frecuencia por defecto
        self.listaFreqsNotas = listaFreqsNotas
        self.beta = 1
        self.factorMod = factorMod
        self.faseMod = 0
        self.faseRes = 0

        # Posición actual del bit a rellenar en el frame que vayamos a devolver (para saber si empezar a generar las ondas en fase 0 (si es el primer bit) o en otra fase si ya hemos generado chunks anteriores)
        self.currPos = 0


    def setListaFreqsNotas(self, listaFreqsNotas):
        self.listaFreqsNotas = listaFreqsNotas
    
    def getListaFreqsNotas(self):
        return self.listaFreqsNotas
    
    def addFreqNota(self, freqNota):
        self.listaFreqsNotas.append(freqNota)
  
    def setVol(self, vol):
        self.vol = vol

    def getVol(self):
        return self.vol

    def getNextChunk(self):
        currChunk = np.arange(self.chunkSize)

        fc = self.listaFreqsNotas[0]
        self.fm = fc*self.factorMod
        mod = (self.bitRate*self.beta) * np.sin(2*np.pi*self.fm*currChunk/self.bitRate + self.faseMod)
        res = np.sin((2*np.pi*fc*currChunk+ mod)/self.bitRate   + self.faseRes)
    
        numOndasMod = self.fm*self.chunkSize/self.bitRate
        faseOndasMod = self.faseMod /(2*np.pi)
        faseOndasMod += numOndasMod
        faseOndasMod -= np.trunc(faseOndasMod)
        self.faseMod = faseOndasMod * 2*np.pi

        numOndasRes = fc*self.chunkSize/self.bitRate
        faseOndasRes = self.faseRes /(2*np.pi)
        faseOndasRes += numOndasRes
        faseOndasRes -= np.trunc(faseOndasRes)
        self.faseRes = faseOndasRes * 2*np.pi


        self.currPos += self.chunkSize
        return res * self.vol

#---------------------------------------------------------------------------------------------------------------------------------

class FmCompuesto:
    def __init__(self, bitRate, chunkSize, listaFactorYBeta=[], listaFreqsNotas=[], vol=1):
        self.bitRate = bitRate # ~= SRATE
        self.chunkSize = chunkSize
        self.vol = vol

        #Frecuencia por defecto
        self.listaFreqsNotas = listaFreqsNotas
        self.setListaFactorYBeta(listaFactorYBeta)
        self.faseRes = 0

        # Posición actual del bit a rellenar en el frame que vayamos a devolver (para saber si empezar a generar las ondas en fase 0 (si es el primer bit) o en otra fase si ya hemos generado chunks anteriores)
        self.currPos = 0

    def setListaFactorYBeta(self, listaFactorYBeta):
        self.listaFactorYBeta = listaFactorYBeta
        self.listaFaseMod = [0]
        for i in range(len(self.listaFactorYBeta)):
            self.listaFaseMod.append(0)

    def setListaFreqsNotas(self, listaFreqsNotas):
        self.listaFreqsNotas = listaFreqsNotas
    
    def getListaFreqsNotas(self):
        return self.listaFreqsNotas
    
    def addFreqNota(self, freqNota):
        self.listaFreqsNotas.append(freqNota)
  
    def setVol(self, vol):
        self.vol = vol

    def getVol(self):
        return self.vol
    
    def getNextChunk(self):
        currChunk = np.arange(self.chunkSize)
        samples = np.zeros(self.chunkSize) + self.currPos

        fc = self.listaFreqsNotas[0]


        listaFcYFm = [[fc, self.vol]]
        for factorYBeta in self.listaFactorYBeta:
            listaFcYFm.append([factorYBeta[0]*fc,factorYBeta[1]])

        for i in range (len(listaFcYFm)-1, -1, -1):
            samples = listaFcYFm[i][1] * np.sin(2*np.pi*listaFcYFm[i][0]*currChunk/self.bitRate + samples + self.listaFaseMod[i])

            numOndasMod = listaFcYFm[i][0]*self.chunkSize/self.bitRate
            faseOndasMod = self.listaFaseMod[i] /(2*np.pi)
            faseOndasMod += numOndasMod
            faseOndasMod -= np.trunc(faseOndasMod)
            self.listaFaseMod[i] = faseOndasMod * 2*np.pi

        self.currPos += self.chunkSize
        return samples

class Partitura: 
    def __init__(self, bitRate, chunkSize, listaNotas, tPorBeat): #sintaxis lista: [[freq, dur]] dur = 1 es una negra, dur = 2 es una blanca, dur = 0.5 es una corchea...
        self.bitRate = bitRate # ~= SRATE
        self.chunkSize = chunkSize

        
        self.currPos = 0
        self.tPorBeat = tPorBeat
        self.bitsPerBeat = self.bitRate * self.tPorBeat

        self.listaNotasConMomentos = []

        ini = 0
        for nota in listaNotas:
            mid = ini + (nota[1] * 0.95) * self.bitsPerBeat
            self.listaNotasConMomentos.append([nota[0], ini, mid]) #Duracion de la nota (ligeramente reducida)
            self.listaNotasConMomentos.append([0, mid , mid + (nota[1] * 0.05) * self.bitsPerBeat]) #Mini silencio entre nota y nota (para que se note la diferencia entre 2 notas consecutivas iguales)
            ini += nota[1] * self.bitsPerBeat


    def getNextChunk(self):
        currNotas = []
        for nota in self.listaNotasConMomentos:
            if nota[1] <= self.currPos and nota[2] > self.currPos: #Para cada nota que se tenga que tocar en este chunk
                currNotas.append(nota[0]) #Añade su frecuencia

        self.currPos += self.chunkSize
        return currNotas

class AbcInput:
    def __init__(self):
        #+-2 menos en saltos de SI-DO y MI-FA
        self.notasExpSol = {"C": -9, "D": -7, "E": -5, "F": -4, "G": -2, "A": 0, "B": 2, "c": 3, "d": 5, "e": 7, "f":8 , "g":10 , "a": 12, "b": 14} #En clave de sol: el LA es 440
        self.notasExpFa = {"E": -29, "F": -28,"G": -26, "A": -24, "B": -22, "c": -21, "d": -19, "e": -17, "f": -16, "g": -14, "a": -12, "b": -10, "c'": -9} 
        self.notasExpDo = {"D": -19, "E": -17, "F": -16, "G": -14, "A": -12, "B": -10,"c": -9, "d": -7, "e": -5, "f": -4, "g": -2, "a": 0, "b": 2}
        #Clave de Sol:
        # DO RE MI FA SOL LA(440) SI DO RE MI FA SOL LA(880)
        # C  D  E  F  G   A       B  c  d  e  f  g   a
        #Clave de Fa:
        # MI FA SOL LA(110) SI DO RE MI FA SOL LA(220) SI DO    
        # E  F  G   A       B  c  d  e  f  g   a       b  c'
        #Clave de Do:
        # RE MI FA SOL LA(220) SI DO RE MI FA SOL LA(440) SI
        # D  E  F  G   A       B  c  d  e  f  g   a       b

        #Default speed
        self.tPorRedonda = 15 #60bpm en negras
        return

    def setIndiceMelodia(self, X): #1, 2, 3...
        self.IndiceMelodia = X

    def setTitulo(self, T):
        self.titulo = T

    def setCompas(self, M): #2/4, 3/4, 4/4, 6/8, ... 
        auxCompas = M.split("/")
        self.compasStr = M
        self.compasParteIzq = getNum(auxCompas[0])
        self.compasParteDer = getNum(auxCompas[1])

    def setDuracionNotaPorDefecto(self, L): #si no se indica lo contrario, esta sera la duracion de cualquier nota que se indique (ejemplo: 1/8, 1/4, ...)
        auxDuracionDefault = L.split("/")
        self.duracionDefaultStr = L
        self.duracionDefaultParteIzq = getNum(auxDuracionDefault[0])
        self.duracionDefaultDer = getNum(auxDuracionDefault[1])
        self.fracNotaPorDefecto = self.duracionDefaultParteIzq / self.duracionDefaultDer

    def setTipoMelodia(self, R):
        self.tipoMelodia = R
        
    def setKey(self, K): #clave de sol, de fa...
        self.key = K

    def setNotas(self, notas):
        self.notas = notas

    def getNotas(self):
        return self.notas
    
    def setTiempoPorRedonda(self, tPorRedonda):
        self.tPorRedonda = tPorRedonda

    def getTiempoPorRedonda(self):
        return self.tPorRedonda
    
    def getDuracionDefaultParteIzq(self):
        return self.duracionDefaultParteIzq
    
    def getFracNotaPorDefecto(self):
        return self.fracNotaPorDefecto

    def getFreqParaNota(self, notaStr):
        if(self.key == "G"):
            if notaStr == "z":
                return 0 #Silencios
            elif notaStr in self.notasExpSol:
                i = self.notasExpSol[notaStr]
                return 440 * (2 ** (i / 12)) #440 * 2^(i/12)
            else:
                print("error, nota no reconocida en esta escala")
                return None
        elif(self.key == "F"):
            if notaStr == "z":
                return 0 #Silencios
            elif notaStr in self.notasExpFa:
                i = self.notasExpFa[notaStr]
                return 440 * (2 ** (i / 12)) #440 * 2^(i/12)
            else:
                print("error, nota no reconocida en esta escala")
                return None
        elif(self.key == "C"):
            if notaStr == "z":
                return 0 #Silencios
            elif notaStr in self.notasExpDo:
                i = self.notasExpDo[notaStr]
                return 440 * (2 ** (i / 12)) #440 * 2^(i/12)
            else:
                print("error, nota no reconocida en esta escala")
                return None
        else:
            print("error, escala no reconocida")
            return None

def isNum(c):
    return c.isnumeric()

def getNum(c):
    return int(c)

def getFraccion(fStr):
    piezas = fStr.split("/")
    return getNum(piezas[0]) / getNum(piezas[1])

def leeArchivo(pathArchivo):
    file = open(pathArchivo, "r")
    archivoStr = file.read()
    lineas = archivoStr.splitlines()

    abc = AbcInput()

    notas = []
    comienzoRep = 0
    idxAnteriorCompas = 0
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
            elif (parteIzq == "Q"):
                tmp = parteDer.split("=")
                tmpIzq = tmp[0]  #1/4, 1/8, 3/8,... 1 = redonda, 1/2 = blanca, 1/4 = negra,...   (modificadorDeNota * L/(Qizq*Qder)   t      (L/(Qder *Qizq)    2* 1/120
                tmpDer = tmp[1]  #120, 60, 50,...
                tPorRedonda = 60/(getFraccion(tmpIzq) * getNum(tmpDer))
                abc.setTiempoPorRedonda(tPorRedonda)
            else:
                print("---ERROR---"),
                print("No se ha podido procesar la linea:")
                print(linea)
                print("==========")
        else:
            #seccion con notaS
            while linea != "":
                #Caso: Espacios en blanco
                matchObj = re.match("^\s+", linea)
                if matchObj != None:
                    matchEndPos = matchObj.regs[0][1]
                    linea = linea[matchEndPos:]
                    continue
                
                #Caso: Empezar compas que empieza repeticion
                matchObj = re.match("^\|:(1?)", linea)
                if matchObj != None:
                    matchEndPos = matchObj.regs[0][1]
                    linea = linea[matchEndPos:]
                    comienzoRep = len(notas)
                    idxAnteriorCompas = len(notas)
                    continue

                #Caso: Empezar compas que termina repeticion
                matchObj = re.match("^:\|(2?)", linea)
                if matchObj != None:
                    matchEndPos = matchObj.regs[0][1]
                    linea = linea[matchEndPos:]
                    notas.extend(notas[comienzoRep:idxAnteriorCompas])
                    idxAnteriorCompas = len(notas)
                    continue

                #Caso: Empezar compas
                matchObj = re.match("^\|(1?)", linea)
                if matchObj != None:
                    matchEndPos = matchObj.regs[0][1]
                    linea = linea[matchEndPos:]
                    idxAnteriorCompas = len(notas)
                    continue
                
                #Caso: Fin de partitua
                matchObj = re.match("^\]", linea)
                if matchObj != None:
                    matchEndPos = matchObj.regs[0][1]
                    linea = linea[matchEndPos:]
                    break

                #Caso: Nota
                matchObj = re.match("^(\d?)[A-G,a-g,z]('?)", linea)
                if matchObj != None:
                    matchEndPos = matchObj.regs[0][1]
                    
                    #Parte: modificacion duracion
                    dur = abc.getDuracionDefaultParteIzq()
                    matchObj = re.match("^\d", linea)
                    if matchObj != None:
                        matchEndPos = matchObj.regs[0][1]
                        dur = getNum(linea[:matchEndPos])
                        linea = linea[matchEndPos:]

                    #Parte: letra nota y apostrofe opcional
                    freq = 0
                    matchObj = re.match("^[A-G,a-g,z]('?)", linea)
                    if matchObj != None:
                        matchEndPos = matchObj.regs[0][1]
                        strNota = linea[:matchEndPos]
                        freq = abc.getFreqParaNota(strNota)
                        if freq == None:
                            print("error: freq none")
                            continue
                        linea = linea[matchEndPos:]
                    else:
                        print("Error al parsear la nota")
                        continue

                    notas.append([freq, dur])
                    continue

                else:
                    print("Error: ninguno de los casos ha sido reconocido")
    abc.setNotas(notas)
    return abc


def main(abc):
    SRATE = 44100       # sampling rate, Hz, must be integer
    CHUNK = 1024
    stream = sd.OutputStream(samplerate=SRATE,blocksize=CHUNK,channels=1)  
    stream.start()

    kb = kbhit.KBHit()
    c = ' '

    #Elegir sintetizador
    print("Elige sintetizador concreto pulsando una tecla: \n")
    print("a - fm simple;  b - fm compuesto;  s - oscilador seno\n")
    while True:

        if kb.kbhit():
            c = kb.getch()
            if c == 'a':
                print("Has seleccionado el fm simple.\n")
                myModulador = FmSimple(SRATE, CHUNK, factorMod=0.5, vol = 0.5)           
                break
            if c == 'b':
                print("Has seleccionado el fm compuesto.\n")
                kb = kbhit.KBHit()
                c = ' '
                #Elegir instrumento
                print("Elige instrumento concreto pulsando una tecla: \n")
                print("p - piano;  f - flauta dulce;  s - saxofon\n")
                while True:
                    if kb.kbhit():
                        c = kb.getch()
                        if c == 'p':
                            print("Has seleccionado el piano.\n")                  #0.374
                            listaFactoresYBeta = [[1/2, 1.0],[3/4, 0.8],[1/4, 0.5],[187/500,0.1]]
                            break
                        if c == 'f':
                            print("Has seleccionado la flauta dulce.\n")
                            listaFactoresYBeta = [[1/2,0.8],[3/4,0.5],[1/4,0.3],[187/1000, 0.1]]
                            break
                        if c == 's':
                            print("Has seleccionado el saxofon.\n")
                            listaFactoresYBeta = [[1/2, 1.0],[3/4, 0.8],[5/4, 0.6],[3/2, 0.4]]
                            break
                myModulador = FmCompuesto(SRATE, CHUNK, listaFactorYBeta=listaFactoresYBeta, vol = 0.5)
                break
            if c == 's':
                print("Has seleccionado el oscilador seno.\n")
                myModulador = OsciladorSeno(SRATE, CHUNK, vol = 0.5)
                break

    myPartitura = Partitura(SRATE, CHUNK, abc.getNotas() , abc.getTiempoPorRedonda() * abc.getFracNotaPorDefecto() )


    # [[factorModulador1,beta1],[factorModulador2,beta2]],...]
    #factoresYBetas = [[1/2,1],[3/4,0.8],...]

    print("Reproduciendo, puedes pulsar q para pararlo")

    nextChunk = myPartitura.getNextChunk()
    while len(nextChunk) > 0:
        myModulador.setListaFreqsNotas(nextChunk)
        samples = myModulador.getNextChunk()
        stream.write(np.float32(samples))
        nextChunk = myPartitura.getNextChunk() 


        if kb.kbhit():
            c = kb.getch()
            if c =='q':
                print("Has pulsado q, reproduccion parada")
                break
        

    stream.stop()

#Ejecutar el programa:------------------------------------
if __name__ == "__main__":
    print("-----------------------------------------------------------------------------------------")
    print("Escribe a countinuacion el nombre del fichero con la partitura ABC (ejemplo: piratas.txt).")
    print("Notas:")
    print("  - El path es relativo a donde se encuentre este fichero")
    print("  - Intente usar uno de los inputs de ejemplo o modificar uno de ellos con cuidado,")
    print("    porque el parser no reconoce todos los ABC, y headers no reconocidos o espacios")
    print("    de sobra pueden dar errores al parsearlo")
    print("-----------------------------------------------------------------------------------------")
    archivo = input()
    abc = leeArchivo(archivo)
    main(abc)

