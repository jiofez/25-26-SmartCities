from machine import Pin, PWM, ADC
from time import ticks_ms, ticks_diff, sleep

buzzer = PWM(Pin(27))             # Buzzer sur la pin 27
ROTARY_ANGLE_SENSOR = ADC(2)      # Capteur rotatif pour le volume
BOUTTON = Pin(16, Pin.IN, Pin.PULL_UP)  # Bouton avec résistance Pull-Up
LED = Pin(18, Pin.OUT)            # LED pour indication visuelle
LED.value(1)                       # LED allumée au démarrage


# Mélodie 1
notes_a = [523, 587, 659, 698, 784, 880, 988, 1047]      # Fréquences des notes
durations_a = [0.3, 0.3, 0.3, 0.3, 0.4, 0.4, 0.4, 0.6]   # Durées correspondantes

# Mélodie 2
notes_b = [440, 440, 440, 349, 440, 349, 440, 349, 440, 440, 440, 349]
durations_b = [0.5, 0.5, 0.5, 0.35, 0.5, 0.35, 0.5, 0.35, 0.5, 0.5, 0.5, 0.35]

current_melody = 'B'     # Mélodie actuelle
last_button_state = 1    # État précédent du bouton
note_index_a = 0         # Index de la note pour la mélodie A
note_index_b = 0         # Index de la note pour la mélodie B

while True:
    # Lecture de l'état du bouton
    button_state = BOUTTON.value()
    print(button_state)

    # Détection du front descendant (appui du bouton)
    if last_button_state == 1 and button_state == 0:
        # Changer de mélodie
        if current_melody == 'B':
            current_melody = 'A'
        else:
            current_melody = 'B'
        
        # Repartir au début de la mélodie choisie
        if current_melody == 'A':
            note_index_a = 0
        else:
            note_index_b = 0

    # Mettre à jour l'état précédent du bouton
    last_button_state = button_state

    # Sélection de la mélodie courante
    if current_melody == 'A':
        notes = notes_a
        durations = durations_a
        note_index = note_index_a
    else:
        notes = notes_b
        durations = durations_b
        note_index = note_index_b

    # Jouer la note courante
    freq = notes[note_index % len(notes)]
    dur = durations[note_index % len(durations)]
    buzzer.freq(freq)
    start = ticks_ms()      # Début du chronomètre
    LED.value(1)            # Allumer la LED pendant la note

    # Boucle de durée de la note (permet de vérifier le bouton et le volume en temps réel)
    while ticks_diff(ticks_ms(), start) < dur * 1000:
        # Interruption si le bouton est pressé
        if BOUTTON.value() == 1:
            break

        # Lecture du volume via le capteur rotatif
        volume = ROTARY_ANGLE_SENSOR.read_u16()
        volume = min(max(volume, 0), 45000)   # Limitation pour éviter la saturation
        duty = int((volume / 45000) * 3000)  # Conversion en duty cycle pour le buzzer
        buzzer.duty_u16(duty)
        sleep(0.01)

    # Couper la note après la durée
    buzzer.duty_u16(0)
    LED.value(0)        # Éteindre la LED
    sleep(0.05)         # Petit délai avant la prochaine note

    # Passer à la note suivante
    if current_melody == 'A':
        note_index_a += 1
    else:
        note_index_b += 1
