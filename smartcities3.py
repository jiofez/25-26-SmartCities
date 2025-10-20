from machine import Pin, PWM, ADC, I2C
from time import ticks_ms, ticks_diff, sleep
from ldc1602 import LCD1602
from dht20 import DHT20
import time

# --- Matériel ---

buzzer = PWM(Pin(20))       # Buzzer
pot = ADC(2)                # Potentiomètre (consigne température)
led = PWM(Pin(18))          # LED
led.freq(1000)              # Fréquence LED

# I2C pour LCD et capteur
i2c_lcd = I2C(0, scl=Pin(9), sda=Pin(8), freq=400000)
i2c_dht = I2C(1, scl=Pin(7), sda=Pin(6), freq=400000)

lcd = LCD1602(i2c_lcd, 2, 16)
lcd.display()
dht20 = DHT20(i2c_dht)

# --- Variables ---

pos_alarm = 0
last_temp_measure = time.ticks_ms()
led_state = False
last_blink = time.ticks_ms()
last_alarm_scroll = time.ticks_ms()
last_dimmer = time.ticks_ms()
dimmer_step = 1000
brightness = 0
mode_transition = 0

# --- Fonctions ---

def lire_consigne():
    # Convertit le potentiomètre en consigne 15–35 °C
    val = pot.read_u16()
    consigne = 15 + (val / 65535) * (35 - 15)
    return round(consigne, 1)

def mesurer_temperature():
    # Retourne température DHT20
    return round(dht20.dht20_temperature(), 1)

def afficher_lcd(consigne, temp, alarm=False):
    # Affiche la consigne et température ou ALARM
    global pos_alarm, last_alarm_scroll, mode_transition

    lcd.setCursor(0, 0)
    lcd.print("Set: " + str(consigne) + " C")

    if alarm:
        now = time.ticks_ms()
        if time.ticks_diff(now, last_alarm_scroll) >= 2000:
            if mode_transition == 0:
                lcd.clear()
                mode_transition += 1
            lcd.setCursor(pos_alarm, 1)
            lcd.print("ALARM")
            pos_alarm = (pos_alarm + 1) % (16 - len("ALARM") + 1)
            last_alarm_scroll = now
    else:
        lcd.setCursor(0, 1)
        lcd.print("Ambient: " + str(temp) + " C")
        pos_alarm = 0
        mode_transition = 0

def alarme_active():
    # Active le buzzer
    buzzer.freq(1000)
    buzzer.duty_u16(30000)

def alarme_desactive():
    # Désactive le buzzer
    buzzer.duty_u16(0)

def clignoter_led(periode_s):
    # Fait clignoter la LED
    global last_blink, led_state
    now = time.ticks_ms()
    if time.ticks_diff(now, last_blink) >= int((periode_s * 1000) / 2):
        led_state = not led_state
        led.duty_u16(65535 if led_state else 0)
        last_blink = now

def dimmer():
    # Fait varier la luminosité de la LED
    global brightness, dimmer_step, last_dimmer
    now = time.ticks_ms()
    if time.ticks_diff(now, last_dimmer) >= 20:
        led.duty_u16(brightness)
        brightness += dimmer_step
        if brightness <= 0 or brightness >= 65535:
            dimmer_step = -dimmer_step
        last_dimmer = now

# --- Boucle principale ---

temperature = mesurer_temperature()

while True:
    consigne = lire_consigne()

    # Mise à jour température toutes les 1 s
    now = time.ticks_ms()
    if time.ticks_diff(now, last_temp_measure) > 1000:
        temperature = mesurer_temperature()
        last_temp_measure = now
        lcd.clear()

    # Gestion des états
    if temperature > consigne + 3:
        afficher_lcd(consigne, temperature, alarm=True)
        alarme_active()
        dimmer()
    elif temperature > consigne:
        afficher_lcd(consigne, temperature, alarm=False)
        alarme_desactive()
        clignoter_led(2)
    else:
        afficher_lcd(consigne, temperature, alarm=False)
        alarme_desactive()
        led.duty_u16(0)
