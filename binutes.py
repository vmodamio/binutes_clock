# Example using PIO to drive a set of WS2812 LEDs.

import array, time
from machine import Pin, Timer
import rp2

# set the system frequency to a multiple of 60**2
machine.freq(102400000)

# Configure the number of WS2812 LEDs.
NUM_LEDS = 8
PIN_NUM = 2
brightness = 0.05
brightness_hour      = 0.7
brightness_binute   = 0.1

ORANGE_RED = (255, 40, 0)
YELLOW = (255, 180, 10)
BLUE = (15, 80, 255)
GREEN = (0, 255, 40)
day_color = [BLUE, YELLOW, ORANGE_RED]
hr_col = array.array("I", [0 for _ in range(3)])
for i,c in enumerate(day_color):
    r = int((c[0] & 0xFF) * brightness_hour)
    g = int((c[1] & 0xFF) * brightness_hour)
    b = int((c[2] & 0xFF) * brightness_hour)
    hr_col[i] = (g<<16) + (r<<8) + b

bm_col = array.array("I", [0 for _ in range(3)])
for i,c in enumerate(day_color):
    r = int((c[0] & 0xFF) * brightness_binute)
    g = int((c[1] & 0xFF) * brightness_binute)
    b = int((c[2] & 0xFF) * brightness_binute)
    bm_col[i] = (g<<16) + (r<<8) + b

dim_col = (0X1<<16) + (0X1<<8) +  0X1

season_color = [BLUE, GREEN, YELLOW, ORANGE_RED]

#timestamp = 0
#14:30   14:32
timestamp = (14<<12) + (32<<6)

#leds = array.array("I", [0 for _ in range(NUM_LEDS)])
"""
tim = Timer()
bisec = 0
led = Pin("LED", Pin.OUT)

def tick(timer):
    global led
    global bisec
    bisec+=1
    led.toggle()
"""

"""
The clock ticks at 1 binary second rate
"""
@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def bsecond_tick():
    # Cycles: 1 + 1 + 5 + 1 + (27 + 1)*(32+31+1) = 1800
    irq(rel(0))
    set(pins, 0)      [5]          
    set(x, 27)        
    label(0)
    nop()                       [31]
    nop()                       [30]   
    jmp(x_dec, 0)

sm_ticks = rp2.StateMachine(1, bsecond_tick, freq=2048, set_base=Pin(25))

# Set the IRQ handler to print the millisecond timestamp.
#sm.irq(lambda p: print(time.ticks_ms()))

def bsec(p):
    global timestamp
    timestamp+=1
    print(timestamp)

sm_ticks.irq(bsec)
# Start the StateMachine.
sm_ticks.active(1)


"""
The LEDS state machine
"""
@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
def ws2812():
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0)    [T3 - 1]
    jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
    jmp("bitloop")          .side(1)    [T2 - 1]
    label("do_zero")
    nop()                   .side(0)    [T2 - 1]
    wrap()


# Create the StateMachine with the ws2812 program, outputting on pin
sm = rp2.StateMachine(0, ws2812, freq=8_000_000, sideset_base=Pin(PIN_NUM))

# Start the StateMachine, it will wait for data on its FIFO.
sm.active(1)


##########################################################################


def clock_show():
    leds = array.array("I",[dim_col for _ in range(NUM_LEDS)])
    bs  = timestamp & 0x3F          # bits  0 to  5
    bm  = (timestamp >> 6) & 0x3F   # bits  6 to 11
    bm4 = bm >> 2                   # 4bits  [32, 16, 8, 4]
    bm1 = bm & 0b11                 # 0,1,2 or 3 binutes
    hr  = (timestamp >> 12) & 0x1F  # bits 12 to 16
    hr8 = hr%8
    hr3 = hr//8
    if (bm4 >> 8): 
        for n in range(7):
            leds[(hr8 +(n+1))%8] = bm_col[hr3] if (( (0x10 - bm4)>>n) & (bs&1)) else dim_col
    else:
        for n in range(7):
            leds[(hr8 -(n+1))%8] = bm_col[hr3] if ((bm4>>n) & (bs&1)) else dim_col 

    ledss = array.array("I",[((bs>>n)&1)*bm_col[hr3] for n in range(NUM_LEDS)])
    leds[hr8] = hr_col[hr3]
    sm.put(leds, 8)


while True:
    clock_show()
    time.sleep_ms(100)


