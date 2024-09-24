# Example using PIO to drive a set of WS2812 LEDs.

import array, time
from machine import Pin, Timer
import rp2

# set the system frequency to a multiple of 60**2
machine.freq(102400000)

# Configure the number of WS2812 LEDs.
NUM_LEDS = 8
PIN_NUM = 2
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

hr_col2 = array.array("I", [0 for _ in range(3)])
for i,c in enumerate(day_color):
    r = int((c[0] & 0xFF) * brightness_hour*0.5)
    g = int((c[1] & 0xFF) * brightness_hour*0.5)
    b = int((c[2] & 0xFF) * brightness_hour*0.5)
    hr_col2[i] = (g<<16) + (r<<8) + b

bm_col = array.array("I", [0 for _ in range(3)])
for i,c in enumerate(day_color):
    r = int((c[0] & 0xFF) * brightness_binute)
    g = int((c[1] & 0xFF) * brightness_binute)
    b = int((c[2] & 0xFF) * brightness_binute)
    bm_col[i] = (g<<16) + (r<<8) + b

dim_col = (0X1<<16) + (0X1<<8) +  0X1
day_col = (0XB2<<16) + (0XB2<<8) + 0XB2
week_col = (0X0<<16) + (0X7D<<8) + 0XB2

season_color = [BLUE, GREEN, YELLOW, ORANGE_RED]
season_col = array.array("I", [0 for _ in range(4)])
for i,c in enumerate(season_color):
    r = int((c[0] & 0xFF) * brightness_hour)
    g = int((c[1] & 0xFF) * brightness_hour)
    b = int((c[2] & 0xFF) * brightness_hour)
    season_col[i] = (g<<16) + (r<<8) + b

#timestamp = 0
#14:30   14:32
timestamp = (5<<12) + (32<<6) + (2<<17) + (0<<22) 
nclicks = 0
"""
Timestamp bits:
    0-5:   64 bsecs
    6-11:  64 binutes
    12-16: 24 Hr           ts
    17-21: 31 days
    22-25: 12 months
    26-31: 64 years from 2024

    leap year is multiple of 4 (year & 0b11)==0  

    ts & (4095 )
"""
num_days = array.array("I", [ 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
binut = 2**12-1
hour = (2**5-1)<<12
day  = (2**5-1)<<17
month = (2**4-1)<<22
year = (2**6-1)<<26


def ndays(ts):
    m = ((ts & month)>>22)%12
    leap = 0
    if (m == 1):
        leap = 0 if ((ts>>26) & 3) else 1
    return num_days[m] + leap


def cycle_timestamp(ts):
    global timestamp
    if ( (timestamp & (binut | hour)) == ((23<<12) + binut) ):
        timestamp+=1
        timestamp &= ~hour
        #timestamp |= (0 & hour) setting the hour to zero doesnt need to OR
        if (((timestamp & day) >> 17) == (ndays(timestamp) -1 ) ):
            timestamp &= ~day
            if (((timestamp & month) >> 22) == 11 ):
                timestamp &= ~ month
                timestamp+= 1<<26
            else:
                timestamp+= 1<<22
        else:
            timestamp+= 1<<17
    else:
        timestamp+=1

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
    #print(timestamp)

sm_ticks.irq(cycle_timestamp)
# Start the StateMachine.
sm_ticks.active(1)

## button state machine
@rp2.asm_pio()
def button_debounce():
    wrap_target()
    label(0)
    wait(0, pin, 0)
    set(x, 31)        
    label(1)
    jmp(pin, 0)
    jmp(x_dec, 1)
    irq( rel(0))

    label(2)
    wait(1, pin, 0)
    set(x, 31)        
    label(3)
    jmp(pin, 2)
    jmp(x_dec, 3)
    wrap()

tim = Timer()

def click(p):
    global nclicks
    nclicks+=1
    print(nclicks)
    if nclicks == 1:
        tim.init(mode=Timer.ONE_SHOT, period=8000, callback=button_timeout)
    else:
        tim.deinit()

def button_timeout(p):
    global nclicks
    nclicks = 0
    print('timeout')

# Instantiate StateMachine(0) with wait_pin_low program on Pin(16).
pin15 = Pin(15, Pin.IN, Pin.PULL_UP)
sm_debounce = rp2.StateMachine(2, button_debounce, freq=2000,  in_base=pin15)
sm_debounce.irq(click)
sm_debounce.active(1)


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
    global timestamp
    leds = array.array("I",[dim_col for _ in range(NUM_LEDS)])
    bs  = timestamp & 0x3F          # bits  0 to  5
    bm  = (timestamp >> 6) & 0x3F   # bits  6 to 11
    bm4 = bm >> 2                   # 4bits  [32, 16, 8, 4]
    bm1 = bm & 0b11                 # 0,1,2 or 3 binutes
    hr  = ((timestamp >> 12) & 0x1F)%24  # bits 12 to 16
    hr8 = hr%8
    hr3 = hr//8
    if (bm >> 5): 
        for n in range(7):
            leds[(hr8 +(n+1))%8] = bm_col[hr3] if (( (0x10 - bm4)>>n) & (bs&1)) else dim_col
    else:
        for n in range(7):
            leds[(hr8 -(n+1))%8] = bm_col[hr3] if ((bm4>>n) & (bs&1)) else dim_col 

    leds[hr8] = hr_col2[hr3] if ((((bs+1) & 0xF)>>1) < bm1) else hr_col[hr3] 
    sm.put(leds, 8)

def date_show():
    global timestamp
    leds = array.array("I",[dim_col for _ in range(NUM_LEDS)])
    dayn = (timestamp & day) >> 17    
    monthn = (timestamp & month) >> 22
    yearn = (timestamp & year) >> 26 
    month3 = (monthn%3)+1
    season = monthn//3
    for n in range(2):
        leds[6+n] = season_col[season] if ((month3 >> n)&1) else dim_col 

    for n in range(5):
        leds[n] =  day_col if (((dayn+1) >> n) & 1) else dim_col

    # day of week, year 0 is 2024
    jan1wd = 0 # 1st Jan 2024 was monday
    yeardays = 0
    for n in range(yearn):
        jan1wd += 1 if (n & 3) else 2
    for n in range(monthn):
        leap = 0
        if (n == 1):
            leap = 0 if (year & 3) else 1
        yeardays += num_days[n] + leap
    yeardays += dayn
    weekday = (jan1wd + yeardays)%7
    if (timestamp & 1):
        leds[weekday] = week_col
    sm.put(leds, 8)

def set_hours():
    global nclicks
    global timestamp
    leds = array.array("I",[dim_col for _ in range(NUM_LEDS)])
    for n in range(24):
        leds[n%8] = hr_col[(n//8)] 
        leds[(n-1)%8] = dim_col
        sm.put(leds, 8)
        time.sleep(1)
        if (nclicks == 3):
            timestamp = (n<<12)
            break
    nclicks = 3

def set_binutes():
    global nclicks
    global timestamp
    leds = array.array("I",[dim_col for _ in range(NUM_LEDS)])
    hr = (timestamp & hour) >> 12
    hr8 = hr%8
    hr3 = hr//8
    for n in range(16):
        leds[hr8] = hr_col[hr3]
        if (n >> 3): 
            for m in range(7):
                leds[(hr8 +(m+1))%8] = bm_col[hr3] if (( (0x10 - n)>>m) & 1) else dim_col
        else:
            for m in range(7):
                leds[(hr8 -(m+1))%8] = bm_col[hr3] if ((n >> m) & 1)  else dim_col 
        sm.put(leds, 8)
        time.sleep(0.87)
        leds = array.array("I",[dim_col for _ in range(NUM_LEDS)])
        leds[hr8] = hr_col[hr3]
        sm.put(leds, 8)
        time.sleep(0.87)
        if (nclicks == 4):
            timestamp = (hr << 12) + (n << 8)
            break
    nclicks = 0



def set_year():
    #print('Setting year')
    pass

def set_month():
    #print('Setting month')
    pass

def set_day():
    #print('Setting day')
    pass

while True:
    if nclicks:
        if nclicks == 1:
            date_show()
        elif nclicks == 2:
            set_hours()
        elif nclicks == 3:
            set_binutes()
        elif nclicks == 4:
            set_year()
        elif nclicks == 5:
            set_month()
        elif nclicks == 6:
            set_day()
        time.sleep(0.5)
    else:
        clock_show()
        time.sleep_ms(100)


