from machine import Pin, PWM, ADC, I2C
from time import ticks_ms, ticks_diff
from ldc1602 import LCD1602
from dht20 import DHT20

class Config:
    PIN_BUZZER = 27
    PIN_POT = 2
    PIN_LED = 18
    PIN_I2C0_SCL = 9
    PIN_I2C0_SDA = 8
    
    TEMP_MIN = 15
    TEMP_MAX = 35
    TEMP_SEUIL_ALERTE = 0  # temp > consigne
    TEMP_SEUIL_ALARME = 3  # temp > consigne + 3
    
    INTERVALLE_LECTURE = 1000     
    INTERVALLE_AFFICHAGE = 500     
    INTERVALLE_LED_NORMAL = 2000   
    INTERVALLE_LED_ALARME = 250    
    
    LCD_COLS = 16
    LCD_ROWS = 2
    I2C_FREQ = 400000


class Hardware:
    
    def __init__(self):
        try:
            # LED
            self.led = Pin(Config.PIN_LED, Pin.OUT)
            self.led.value(0)
            
            # Potentiomètre
            self.pot = ADC(Config.PIN_POT)
            
            # Buzzer
            self.buzzer = PWM(Pin(Config.PIN_BUZZER))
            self.buzzer.freq(1000)
            self.buzzer.duty_u16(0)
            
            self.i2c0 = I2C(0, scl=Pin(Config.PIN_I2C0_SCL), 
                           sda=Pin(Config.PIN_I2C0_SDA), 
                           freq=Config.I2C_FREQ)
            
            # LCD
            self.lcd = LCD1602(self.i2c0, Config.LCD_ROWS, Config.LCD_COLS)
            self.lcd.display()
            
            # I2C pour DHT20
            self.i2c1 = I2C(1)
            
            # Capteur température
            self.dht20 = DHT20(self.i2c1)
            
            print("Matériel initialisé avec succès")
            
        except Exception as e:
            print(f"Erreur initialisation matériel: {e}")
            raise
    
    def lire_consigne(self):
        try:
            val = self.pot.read_u16()
            consigne = Config.TEMP_MIN + (val / 65535) * (Config.TEMP_MAX - Config.TEMP_MIN)
            return round(consigne, 1)
        except Exception as e:
            print(f"Erreur lecture potentiomètre: {e}")
            return 25.0  # Valeur par défaut
    
    def lire_temperature(self):
        try:
            temp = self.dht20.dht20_temperature()
            return round(temp, 1)
        except Exception as e:
            print(f"Erreur lecture température: {e}")
            return None
    
    def set_led(self, state):
        self.led.value(1 if state else 0)
    
    def set_buzzer(self, active):
        if active:
            self.buzzer.duty_u16(2000)
        else:
            self.buzzer.duty_u16(0)
    
    def afficher_lcd(self, consigne, temp, etat):
        try:
            self.lcd.clear()
            
            self.lcd.setCursor(0, 0)
            self.lcd.print(f"Set: {consigne} C")
            
            self.lcd.setCursor(0, 1)
            if temp is not None:
                self.lcd.print(f"Amb: {temp} C")
            else:
                self.lcd.print("Amb: ERR")
            
            if etat == "ALARME":
                self.lcd.setCursor(11, 1)
                self.lcd.print("ALARM")
            elif etat == "ALERTE":
                self.lcd.setCursor(11, 1)
                self.lcd.print("ALERT")
                
        except Exception as e:
            print(f"Erreur affichage LCD: {e}")


class SystemeControle:
    
    def __init__(self, hardware):
        self.hw = hardware
        self.etat = "NORMAL"  # NORMAL, ALERTE, ALARME
        
        # Timestamps pour gestion non-bloquante
        self.last_lecture = 0
        self.last_affichage = 0
        self.last_led_toggle = 0
        self.led_state = False
        
        # Données courantes
        self.consigne = 25.0
        self.temperature = None
    
    def determiner_etat(self):
        if self.temperature is None:
            return "NORMAL"
        
        diff = self.temperature - self.consigne
        
        if diff > Config.TEMP_SEUIL_ALARME:
            return "ALARME"
        elif diff > Config.TEMP_SEUIL_ALERTE:
            return "ALERTE"
        else:
            return "NORMAL"
    
    def gerer_led(self, now):
        if self.etat == "ALARME":
            intervalle = Config.INTERVALLE_LED_ALARME
        elif self.etat == "ALERTE":
            intervalle = Config.INTERVALLE_LED_NORMAL
        else:
            self.hw.set_led(False)
            return
        
        if ticks_diff(now, self.last_led_toggle) >= intervalle:
            self.led_state = not self.led_state
            self.hw.set_led(self.led_state)
            self.last_led_toggle = now
    
    def gerer_buzzer(self):
        self.hw.set_buzzer(self.etat == "ALARME")
    
    def update(self):
        now = ticks_ms()
        
        # Lecture des capteurs
        if ticks_diff(now, self.last_lecture) >= Config.INTERVALLE_LECTURE:
            self.consigne = self.hw.lire_consigne()
            self.temperature = self.hw.lire_temperature()
            self.etat = self.determiner_etat()
            self.last_lecture = now
        
        # Mise à jour affichage LCD
        if ticks_diff(now, self.last_affichage) >= Config.INTERVALLE_AFFICHAGE:
            self.hw.afficher_lcd(self.consigne, self.temperature, self.etat)
            self.last_affichage = now
        
        # Gestion LED et buzzer
        self.gerer_led(now)
        self.gerer_buzzer()


def main():
    print("=" * 40)
    print("Système de contrôle température")
    print("=" * 40)
    
    try:
        # Initialisation
        print("\nInitialisation du matériel...")
        hw = Hardware()
        
        print("Démarrage du système de contrôle...")
        systeme = SystemeControle(hw)
        
        # Message de démarrage sur LCD
        hw.lcd.clear()
        hw.lcd.setCursor(0, 0)
        hw.lcd.print("Systeme pret")
        hw.lcd.setCursor(0, 1)
        hw.lcd.print("Demarrage...")
        
        print("\n		Système opérationnel")
        print("Appuyez sur Ctrl+C pour arrêter\n")
        
        # Boucle principale
        while True:
            systeme.update()
            
    except KeyboardInterrupt:
        print("\n\nArrêt demandé par l'utilisateur")
        cleanup(hw)
        
    except Exception as e:
        print(f"\nErreur critique: {e}")
        try:
            cleanup(hw)
        except:
            pass
        raise


def cleanup(hw):
    print("Nettoyage...")
    try:
        hw.set_buzzer(False)
        hw.set_led(False)
        hw.lcd.clear()
        hw.lcd.setCursor(0, 0)
        hw.lcd.print("Systeme arrete")
        print("Nettoyage terminé")
    except Exception as e:
        print(f"Erreur lors du nettoyage: {e}")


# ==================== EXÉCUTION ====================
if __name__ == "__main__":
    main()