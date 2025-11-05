from machine import ADC, Pin
from ws2812 import WS2812
from time import ticks_ms, ticks_diff, sleep
import urandom

BROCHE_LED = 18
NOMBRE_LEDS = 1
led = WS2812(BROCHE_LED, NOMBRE_LEDS)
micro = ADC(1)

TAILLE_FENETRE_COURTE = 5
TAILLE_FENETRE_LONGUE = 50
SEUIL = 1.15
INTERVALLE_MIN = 120
DECALAGE_MICRO = 50
DELAI_ECHANTILLON = 0.005

COULEURS = [
    (255, 0, 0),
    (255, 128, 0),
    (255, 255, 0),
    (0, 255, 0),
    (0, 255, 255),
    (0, 128, 255),
    (128, 0, 255),
    (255, 0, 255),
    (255, 255, 255)
]
EFFETS = ["flash", "pulse", "arc_en_ciel"]

fenetre_courte = []
fenetre_longue = []
dernier_battement = 0
valeur_fondu = 0
direction_fondu = 1

tampon_bpm = []
tampon_bpm_minute = []
ECHANTILLONS_BPM_MAX = 5
BPM_MIN = 30
BPM_MAX = 200
derniere_verif_minute = ticks_ms()

print(">>> Détection de rythme prête...")

def lire_valeur_micro():
    # Lecture filtrée du micro
    val = micro.read_u16() // 256
    return val if val > DECALAGE_MICRO else 0

def maj_fenetres(val):
    # Met à jour les fenêtres courte et longue
    fenetre_courte.append(val)
    fenetre_longue.append(val)
    if len(fenetre_courte) > TAILLE_FENETRE_COURTE:
        fenetre_courte.pop(0)
    if len(fenetre_longue) > TAILLE_FENETRE_LONGUE:
        fenetre_longue.pop(0)

def moyenne(fenetre):
    return sum(fenetre) / len(fenetre) if fenetre else 0

def variance(fenetre):
    # Variance pour détecter les pics de son
    m = moyenne(fenetre)
    return sum((x - m) ** 2 for x in fenetre) / len(fenetre) if fenetre else 0

def couleur_aleatoire():
    return COULEURS[urandom.getrandbits(3) % len(COULEURS)]

def led_flash(couleur):
    # Clignotement rapide
    led.pixels_fill(couleur)
    led.pixels_show()
    sleep(0.05)
    led.pixels_fill((0, 0, 0))
    led.pixels_show()

def led_pulse(couleur, intensite=1.0):
    # Pulse doux selon l'intensité
    r, v, b = couleur
    r = int(r * intensite)
    v = int(v * intensite)
    b = int(b * intensite)
    led.pixels_fill((r, v, b))
    led.pixels_show()

def led_arc_en_ciel(etape=0):
    # Cycle arc-en-ciel simulé sur 1 LED
    r = (1 + urandom.getrandbits(8)) % 256
    v = (128 + urandom.getrandbits(7)) % 256
    b = (255 - r) % 256
    led.pixels_fill((r, v, b))
    led.pixels_show()

while True:
    niveau_son = lire_valeur_micro()
    if niveau_son:
        maj_fenetres(niveau_son)
        moy_courte = moyenne(fenetre_courte)
        moy_longue = moyenne(fenetre_longue)
        var_courte = variance(fenetre_courte)
        maintenant = ticks_ms()

        # Détection de battement
        if moy_courte > moy_longue * SEUIL and var_courte > 50 and (maintenant - dernier_battement) > INTERVALLE_MIN:
            intervalle_ms = ticks_diff(maintenant, dernier_battement)
            dernier_battement = maintenant

            # Calcul BPM seulement si plausible
            if 300 < intervalle_ms < 2000:
                bpm = 60000 / intervalle_ms

                # Ajout dans le tampon filtré
                tampon_bpm.append(bpm)
                if len(tampon_bpm) > ECHANTILLONS_BPM_MAX:
                    tampon_bpm.pop(0)

                bpm_filtre = sum(tampon_bpm) / len(tampon_bpm)
                tampon_bpm_minute.append(bpm_filtre)
                print(f"BPM filtré: {bpm_filtre:.1f}")

            # Effet visuel synchronisé
            effet = EFFETS[urandom.getrandbits(2) % len(EFFETS)]
            couleur = couleur_aleatoire()

            if effet == "flash":
                led_flash(couleur)
            elif effet == "pulse":
                valeur_fondu = 0
                direction_fondu = 1
                for i in range(10):
                    valeur_fondu += direction_fondu * 0.1
                    if valeur_fondu >= 1:
                        direction_fondu = -1
                    if valeur_fondu <= 0:
                        direction_fondu = 1
                    led_pulse(couleur, valeur_fondu)
                    sleep(0.02)
            elif effet == "arc_en_ciel":
                led_arc_en_ciel()

            print("Beat détecté ! niveau:", int(niveau_son), "effet:", effet)

        # Vérification minute écoulée
        if ticks_diff(maintenant, derniere_verif_minute) >= 60000:
            if tampon_bpm_minute:
                bpm_moyen_minute = sum(tampon_bpm_minute) / len(tampon_bpm_minute)
                print(f"Moyenne BPM sur la dernière minute : {bpm_moyen_minute:.1f}")

                # Écriture dans un fichier texte
                try:
                    with open("bpm_log.txt", "a") as f:
                        f.write(f"{bpm_moyen_minute:.1f}\n")
                    print("BPM moyen écrit dans bpm_log.txt")
                except Exception as e:
                    print(" Problemo  :", e)

                tampon_bpm_minute.clear()

            derniere_verif_minute = maintenant

    sleep(DELAI_ECHANTILLON)
