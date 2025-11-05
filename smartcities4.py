from machine import ADC, Pin
from ws2812 import WS2812
from time import ticks_ms, ticks_diff, sleep
import urandom

LED_PIN = 18
NUM_LEDS = 1
led = WS2812(LED_PIN, NUM_LEDS)
mic = ADC(1)

SHORT_SIZE = 5
LONG_SIZE = 50
THRESHOLD = 1.15
MIN_INTERVAL = 120
MIC_OFFSET = 50
SAMPLE_DELAY = 0.005

COLORS = [
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
EFFECTS = ["flash", "pulse", "rainbow"]

short_window = []
long_window = []
last_beat = 0
fade_value = 0
fade_direction = 1

bpm_buffer = []
MAX_BPM_SAMPLES = 5
MIN_BPM = 30
MAX_BPM = 200

print(">>> Détection de rythme prête...")

def get_mic_value():
    # Lecture filtrée du micro
    val = mic.read_u16() // 256
    return val if val > MIC_OFFSET else 0

def update_windows(val):
    # Met à jour les fenêtres courte et longue
    short_window.append(val)
    long_window.append(val)
    if len(short_window) > SHORT_SIZE:
        short_window.pop(0)
    if len(long_window) > LONG_SIZE:
        long_window.pop(0)

def avg(window):
    return sum(window) / len(window) if window else 0

def variance(window):
    # Variance pour détecter les pics de son
    m = avg(window)
    return sum((x - m) ** 2 for x in window) / len(window) if window else 0

def random_color():
    return COLORS[urandom.getrandbits(3) % len(COLORS)]

def led_flash(color):
    # Clignotement rapide
    led.pixels_fill(color)
    led.pixels_show()
    sleep(0.05)
    led.pixels_fill((0, 0, 0))
    led.pixels_show()

def led_pulse(color, intensity=1.0):
    # Pulse doux selon l'intensité
    r, g, b = color
    r = int(r * intensity)
    g = int(g * intensity)
    b = int(b * intensity)
    led.pixels_fill((r, g, b))
    led.pixels_show()

def led_rainbow(step=0):
    # Rainbow cycle simulé sur 1 LED
    r = (1 + urandom.getrandbits(8)) % 256
    g = (128 + urandom.getrandbits(7)) % 256
    b = (255 - r) % 256
    led.pixels_fill((r, g, b))
    led.pixels_show()

while True:
    sound_level = get_mic_value()
    if sound_level:
        update_windows(sound_level)
        avg_short = avg(short_window)
        avg_long = avg(long_window)
        var_short = variance(short_window)
        now = ticks_ms()

        # Détection de beat
        if avg_short > avg_long * THRESHOLD and var_short > 50 and (now - last_beat) > MIN_INTERVAL:
            interval_ms = ticks_diff(now, last_beat)
            last_beat = now

            # Calcul BPM seulement si plausible
            if 300 < interval_ms < 2000:
                bpm = 60000 / interval_ms

                # Ajout dans le buffer filtré
                bpm_buffer.append(bpm)
                if len(bpm_buffer) > MAX_BPM_SAMPLES:
                    bpm_buffer.pop(0)

                bpm_filtered = sum(bpm_buffer) / len(bpm_buffer)
                print(f"BPM filtré: {bpm_filtered:.1f}")

            # Effet visuel synchronisé
            effect = EFFECTS[urandom.getrandbits(2) % len(EFFECTS)]
            color = random_color()

            if effect == "flash":
                led_flash(color)
            elif effect == "pulse":
                fade_value = 0
                fade_direction = 1
                for i in range(10):
                    fade_value += fade_direction * 0.1
                    if fade_value >= 1:
                        fade_direction = -1
                    if fade_value <= 0:
                        fade_direction = 1
                    led_pulse(color, fade_value)
                    sleep(0.02)
            elif effect == "rainbow":
                led_rainbow()

            print("Beat détecté ! niveau:", int(sound_level), "effet:", effect)

    sleep(SAMPLE_DELAY)
