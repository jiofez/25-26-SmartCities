import machine
import time

a = 0
Val = 0
LED = machine.Pin(18, machine.Pin.OUT)
BOUTTON = machine.Pin(16, machine.Pin.IN, machine.Pin.PULL_UP)  

boutton3 = 0

def bouton_handler(pin):
    global boutton3, a  
    boutton3 += 1
    if boutton3 > 2:  
        a += 1
        boutton3 = 0
    if a > 3:
        a = 1

def cligotement():
    for _ in range(1):
        LED.value(1)
        time.sleep(0.1)
        LED.value(0)
        time.sleep(0.1)
        LED.value(1)
        time.sleep(0.1)
        LED.value(0)
        time.sleep(0.1)

BOUTTON.irq(trigger=machine.Pin.IRQ_FALLING, handler=bouton_handler)

code = 0
code1 = 0
code2 = 0

while True:
    Val = BOUTTON.value()
    print(Val)
    print(a)

    if a == 1:
        code2=0
        code += 1
        if code == 1:
            cligotement()
        LED.value(1)
        time.sleep(1)
        LED.value(0)
        time.sleep(0.5)
        Val = BOUTTON.value()
    elif a == 2:
        code=0
        code1 += 1
        if code1 == 1:
            cligotement()
        LED.value(1)
        time.sleep(0.5)
        LED.value(0)
        time.sleep(0.5)
        Val = BOUTTON.value()
    elif a == 3:
        code1=0
        code2 += 1
        if code2 == 1:
            cligotement()
        Val = BOUTTON.value()
        LED.value(0)
        a = 0


 