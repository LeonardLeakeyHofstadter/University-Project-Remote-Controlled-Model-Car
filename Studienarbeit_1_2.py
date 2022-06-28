'''Initialisierungen'''

#Bibliotheken
from evdev import InputDevice, ecodes
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
import time
import multiprocessing as mp

#Sequenz zum Ansteuern der Motoren
StepCount = 8
Seq = list(range(0, StepCount))
Seq[0] = [0,1,0,0]
Seq[1] = [0,1,0,1]
Seq[2] = [0,0,0,1]
Seq[3] = [1,0,0,1]
Seq[4] = [1,0,0,0]
Seq[5] = [1,0,1,0]
Seq[6] = [0,0,1,0]
Seq[7] = [0,1,1,0]

#Zeitverzögerung bei Schrittmotoren
delay = 0.0009

#Pins für Schrittmotoren
p1_1 = 24
p1_2 = 4
p1_3 = 23
p1_4 = 25
p2_1 = 18
p2_2 = 22
p2_3 = 17
p2_4 = 27

#Pin für Servomotor
s1 = 26

#Codes für die Eingabe der einzelnen Eingabeelemente
up = 17 #Steuerkreuz hoch -> Kippladefläche hoch
down = 17 #Steuerkreuz runter -> Kippladefläche runter
accelerateBw = 10 #Trigger links hinten -> Nach hinten beschleunigen
accelerateFw = 9 #Trigger rechts hinten -> Nach vorne beschleunigen
left = 0 #linker Stick nach links -> nach links einschlagen
right = 0 #rechter Stick nach rechts -> nach rechts einschlagen


'''Klassen'''

class Schrittmotor():
    def __init__(self, pin1, pin2, pin3, pin4):
        self.pin1 = pin1
        self.pin2 = pin2
        self.pin3 = pin3
        self.pin4 = pin4
        GPIO.setup(self.pin1, GPIO.OUT)
        GPIO.setup(self.pin2, GPIO.OUT)
        GPIO.setup(self.pin3, GPIO.OUT)
        GPIO.setup(self.pin4, GPIO.OUT)

    def clockwise(self, steps):
        for i in range(steps):
            for j in range(StepCount):
                ControlPins(self.pin1, self.pin2, self.pin3, self.pin4, Seq[j][0], Seq[j][1], Seq[j][2], Seq[j][3])
                time.sleep(delay)

    def c_clockwise(self, steps):
        for k in range(steps):
            for l in reversed(range(StepCount)):
                ControlPins(self.pin1, self.pin2, self.pin3, self.pin4, Seq[l][0], Seq[l][1], Seq[l][2], Seq[l][3])
                time.sleep(delay)

class Servomotor():
    def __init__(self, pin5):
        self.pin5 = pin5
        GPIO.setup(self.pin5, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pin5, 50)

    def rotate(self, speed):
        self.stop()
        self.pwm.start(7.5)
        self.pwm.ChangeDutyCycle(speed)

    def stop(self):
        self.pwm.ChangeDutyCycle(0)


'''Methoden'''

#die Pins ansteuern für die Schrittmotoren
def ControlPins(p1, p2, p3, p4, a, b, c, d):
    GPIO.output(p1, a)
    GPIO.output(p2, b)
    GPIO.output(p3, c)
    GPIO.output(p4, d)

#Schrittmotor 1 spannungslos schalten
def ResetPinsX1():
    GPIO.output(p1_1,0)
    GPIO.output(p1_2,0)
    GPIO.output(p1_3,0)
    GPIO.output(p1_4,0)

#Schrittmotor 2 spannungslos schalten
def ResetPinsX2():
    GPIO.output(p2_1,0)
    GPIO.output(p2_2,0)
    GPIO.output(p2_3,0)
    GPIO.output(p2_4,0)

#Position der Kippladefläche speichern
def writeKLF(datei, currently_up):
    datei.seek(0)
    datei.write(currently_up)
    datei.truncate()

#Position der Lenkung speichern
def writeLNK(datei, links_außen, links_mitte, rechts_mitte, rechts_außen):
    datei.seek(0)
    datei.write(links_außen+'\n'+links_mitte+'\n'+rechts_mitte+'\n'+rechts_außen)
    datei.truncate()


'''Methoden für die Steuerung mit dem Xbox-Controller'''

def Prozess_Kippladeflaeche():
    #Eingabe des Controllers
    #mit maus und tastatur: event6; ohne: event0
    xbox = InputDevice('/dev/input/event6')

    #lokal die Datei öffnen
    with open('/home/pi/Daten_Kippladeflaeche', 'r+') as datei:
        currently_up = datei.readline().rstrip()

        for key in xbox.read_loop():
            if key.type == ecodes.EV_ABS:
                if key.code == up or key.code == down:
                    #nach oben -> Kippladefläche erhöhen
                    if key.value == -1 and currently_up == 'False':
                        schrittmotorX1.c_clockwise(7000)
                        ResetPinsX1()
                        currently_up = 'True'
                        writeKLF(datei, currently_up)

                    #nach unten -> Kippladefläche senken
                    if key.value == 1 and currently_up == 'True':
                        schrittmotorX1.clockwise(7000)
                        ResetPinsX1()
                        currently_up = 'False'
                        writeKLF(datei, currently_up)

def Prozess_Lenkung():
    #Eingabe des Controllers
    #mit maus und tastatur: event6; ohne: event0
    xbox = InputDevice('/dev/input/event6')

    with open('/home/pi/Daten_Lenkung', 'r+') as datei:
        links_außen = datei.readline().rstrip()
        links_mitte = datei.readline().rstrip()
        rechts_mitte = datei.readline().rstrip()
        rechts_außen = datei.readline().rstrip()

        for key in xbox.read_loop():
            if key.type == ecodes.EV_ABS:
                if key.code == left or key.code == right:
                    #links

                    #links außen
                    if key.value <= 16383 and links_außen == 'False':
                        schrittmotorX2.clockwise(100) #vrnl
                        ResetPinsX2()
                        links_außen, links_mitte, rechts_mitte, rechts_außen = 'True', 'False', 'False', 'False'
                        writeLNK(datei, links_außen, links_mitte, rechts_mitte, rechts_außen)

                    #links mitte
                    if key.value > 16383 and key.value < (32767-5000) and links_mitte == 'False':
                        if links_außen == 'True': #vlnr
                            schrittmotorX2.c_clockwise(100)
                        else: #vrnl
                            schrittmotorX2.clockwise(100)
                        ResetPinsX2()
                        links_außen, links_mitte, rechts_mitte, rechts_außen = 'False', 'True', 'False', 'False'
                        writeLNK(datei, links_außen, links_mitte, rechts_mitte, rechts_außen)

                    #mitte
                    if key.value >= (32767-5000) and key.value <= (32767+5000):
                        if links_mitte == 'True': #vlnr
                            schrittmotorX2.c_clockwise(100)
                        elif rechts_mitte == 'True': #vrnl
                            schrittmotorX2.clockwise(100)
                        ResetPinsX2()
                        links_außen, links_mitte, rechts_mitte, rechts_außen = 'False', 'False', 'False', 'False'
                        writeLNK(datei, links_außen, links_mitte, rechts_mitte, rechts_außen)

                    #rechts

                    #rechts mitte
                    if key.value > (32767+5000) and key.value <= 49151 and rechts_mitte == 'False':
                        if rechts_außen == 'True': #vrnl
                            schrittmotorX2.clockwise(100)
                        else: #vlnr
                            schrittmotorX2.c_clockwise(100)
                        ResetPinsX2()
                        links_außen, links_mitte, rechts_mitte, rechts_außen = 'False', 'False', 'True', 'False'
                        writeLNK(datei, links_außen, links_mitte, rechts_mitte, rechts_außen)

                    #rechts außen
                    if key.value > 49151 and rechts_außen == 'False':
                        schrittmotorX2.c_clockwise(100) #vlnr
                        ResetPinsX2()
                        links_außen, links_mitte, rechts_mitte, rechts_außen = 'False', 'False', 'False', 'True'
                        writeLNK(datei, links_außen, links_mitte, rechts_mitte, rechts_außen)

def Prozess_Antrieb():
    #Eingabe des Controllers
    #mit maus und tastatur: event6; ohne: event0
    xbox = InputDevice('/dev/input/event6')

    for key in xbox.read_loop():
        if key.type == ecodes.EV_ABS:
            '''
            Trigger links hinten -> bremsen (dreistufig)
            Eingabewerte gehen von 0 bis 1023 (2*E10-1)
            '''
            if key.code == accelerateBw:
                if key.value >= 0 and key.value < 30:
                    servo.stop()
                if key.value >= 30 and key.value <= 127: #leicht gedrückt
                    servo.rotate(7)
                if key.value > 127 and key.value <= 255:
                    servo.rotate(6.1)
                if key.value > 255 and key.value <= 383:
                    servo.rotate(5.5)
                if key.value > 383 and key.value <= 511:
                    servo.rotate(4.9)
                if key.value > 511 and key.value <= 639:
                    servo.rotate(4.3)
                if key.value > 639 and key.value <= 767:
                    servo.rotate(3.7)
                if key.value > 767 and key.value <= 895:
                    servo.rotate(3.1)
                if key.value > 895 and key.value <= 1023: #durchgedrückt
                    servo.rotate(2.5)

            '''
            Trigger rechts hinten -> gas geben (achtstufig)
            Eingabewerte gehen von 0 bis 1023 (2*E10-1)
            '''
            if key.code == accelerateFw:
                if key.value >= 0 and key.value < 30 :
                    servo.stop()
                if key.value >= 30 and key.value <= 127 : #leicht gedrückt
                    servo.rotate(7.8)
                if key.value > 127 and key.value <= 255:
                    servo.rotate(8.4)
                if key.value > 255 and key.value <= 383:
                    servo.rotate(9)
                if key.value > 383 and key.value <= 511:
                    servo.rotate(9.6)
                if key.value > 511 and key.value <= 639:
                    servo.rotate(10.2)
                if key.value > 639 and key.value <= 767:
                    servo.rotate(10.8)
                if key.value > 767 and key.value <= 895:
                    servo.rotate(11.4)
                if key.value > 895 and key.value <= 1023: #durchgedrückt
                    servo.rotate(12.5)


'''Main'''

if __name__ == "__main__":

    #Objekte der Motoren
    schrittmotorX1 = Schrittmotor(p1_1, p1_2, p1_3, p1_4)
    schrittmotorX2 = Schrittmotor(p2_1, p2_2, p2_3, p2_4)
    servo = Servomotor(s1)

    #Prozesse für die Steuerung erstellen
    process_kippladeflaeche = mp.Process(target=Prozess_Kippladeflaeche)
    process_lenkung = mp.Process(target=Prozess_Lenkung)
    process_antrieb = mp.Process(target=Prozess_Antrieb)

    #Prozesse starten
    process_kippladeflaeche.start()
    process_lenkung.start()
    process_antrieb.start()
