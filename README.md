# binutes_clock
Binary clock that shows time, and date using 8 LEDS.

Instead of using 60 min, 60 seconds time reference, the time is represented in
units that are powers of 2. 

One hour is 64 binutes, and one binute is 64 binary seconds.

The clock represents:
Hour: as a unique solid LED in the 8-array, each position
      representing 1Hr, together with a 3-color code to 
      make 3 x 8 = 24 hr.

       0   1   2   3   4   5   6   7  = Pale Blue
       8   9  10  11  12  13  14  15  = Yellow
      16  17  18  19  20  21  22  23  = Red
      [ ] [ ] [ ] [ ] [ ] [x] [ ] [ ]

Binutes: To code the 64, the clock should use 6 bit. The idea 
     is to use the rest of the leds to code the minutes in 
     binary, relative to the position of the Hour. To differenciate
     minutes from hours, all the leds representing binutes are 
     blinking.
     Instead of 6-bit, it uses only 4 bit, to represent the time in 
     binutes with 4 binutes precission:
     1 position to left:  +4 binutes.
     2 position to left:  +8 binutes.
     3 position to left: +16 binutes.
     4 position to left: +32 binutes.

     From the binute 33, the representation changes to represent minutes
     left to next hour:
     5 position to left: -16 binutes.
     6 position to left:  -8 binutes.
     7 position to left:  -4 binutes.

     With this redundancy however, the leds start to blink from the right
     to symbolize how closer we get to the next hour. 
     + When we reach the binute 64, the last and unique blinking led turns 
       solid.
     + A unique led blinking will represent one half**2 of the time, making easy
       to figure out time. either is half and hour, or one quarter, or half quarter,
       or hal of half quarter (ie, 4 binutes)
     + Half hour is represented with the diameter opposite led of the Hr, so its easy
       to spot. Also, this led will always blink alone.

     Binutes are blinking with the same color as the Hr, but slightly dimmed, so the 
     reading is easier.

     The other 2 bits of information to complete the 64 binutes precission are missing, 
     but the base 4 binute is represented with a faster blinking led in position 
     plus/minus 1,2 or 3.

     So, for example 13:01, 13:04 and 13:05 have the same LED configuration: one led
     blinking to the left of the solid led at position 6.
     + 13:01 blinks fast, representing 1 binute over the base4 time.
     + 13:04 blinks slow, as is the first minute in the base4 (position -1)
     + 13:05 blinks with both patterns, slow to represent 4 binutes, in position -1
             and fast, to represent 1 minute over the 4 minutes.

     NOTE: Hour position represent a decimal integer, while the blinking slow leds 
     represent a binary number representing the binutes>>2 (multiples of 4). The fast blinking 
     led is again a decimal integer for the first 3 binutes.

     
DATE:
    The Day of the month, the month and the day of the week are shown periodically 
    (every 64 binutes). It consists on opposite pattern as time, with only one led blinking
    and rest solid.
    
    Month: The two right most leds represent month on the seasson, with no null combination:
      [x] [ ] 1st month  April
      [ ] [x] 2nd month  May
      [x] [x] 3rd month  June
    Seasson is represented with color: 
    Spring: green,  starting in April
    Summer: Yellow, starting in July
    Autum:  Orange-red, Starting in October
    Winter: Blue, starting in January

    The Day of the month is represented in binary from the left most LED, using 5 bits (32 days)
    The position of the week is a blinking led in the first 7 leds.

    There is one LED free, between the 5bit-day and the 2bit-month, this is used to represent
    the value of the led taken by the blinking led.


Instructions: Every hour, the leds blink and move and change colors to show the possibilities 
of the clock.



Numeration:  To ease the readout, a single row with numbers are plot on top of the 
             LEDS:
   
      16   9    2    19   12   5    22   15  
     [ ]  [ ]  [ ]  [ ]  [ ]  [ ]  [ ]  [ ]


Examples: [X] meaning solid , [0], [1], [2] and [3] blinking with respective pattern.
 
    blue     [X]  [ ]  [ ]  [ ]  [0]  [ ]  [ ]  [ ]    00:30
    yellow   [ ]  [ ]  [ ]  [ ]  [1]  [ ]  [X]  [ ]    14:17
    red      [ ]  [ ]  [X]  [1]  [1]  [ ]  [ ]  [ ]    18:53
    red      [ ]  [ ]  [X]  [4]  [ ]  [ ]  [ ]  [ ]    18:63
    blue     [ ]  [ ]  [1]  [ ]  [ ]  [ ]  [ ]  [X]    18:63


OR: instead of blinking patters, the binutes blink slowly, and at the same time a very fast 
blink overlaps in the 1, 2, or 3rd position to left, to indicate the extra binutes.


