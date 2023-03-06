#-----------------------------------------------------------------------------
# Test program.
#
# The program blinks the onboard LED for 10 seconds, then goes to sleep
# and wakes up again after 15 seconds.
#
# The program uses the countdown-timer of the RTC and works on a PCF8563 up to
# 15300 seconds (i.e. 255m or 4h15m). For longer intervals than
# 255 minutes use the alarm or switch to the PCF8523.
#
# Author: Bernhard Bablok
#
# Website: https://github.com/pcb-pico-en-control
#-----------------------------------------------------------------------------

import time
import board
import alarm
from digitalio import DigitalInOut, Direction, Pull

# imports for PCF8563
import busio
from adafruit_pcf8563 import PCF8563 as PCF_RTC

# --- configuration   --------------------------------------------------------

PIN_DONE = board.GP4   # connect to 74HC74 CLK
PIN_SDA  = board.GP2   # connect to RTC
PIN_SCL  = board.GP3   # connect to RTC

LED_TIME = 0.5         # blink-duration
ON_TIME  = 10          # seconds on (blinking)
OFF_TIME = 15          # seconds off (<= 15300 == 255*60)

# --- create hardware objects   ----------------------------------------------

led            = DigitalInOut(board.LED)
led.direction  = Direction.OUTPUT

done           = DigitalInOut(PIN_DONE)
done.direction = Direction.OUTPUT
done.value     = 0

i2c = busio.I2C(PIN_SCL,PIN_SDA)
rtc = PCF_RTC(i2c)

# --- simulate work   --------------------------------------------------------

def blink(dur=LED_TIME,repeat=1):
  while repeat:
    led.value = 1
    time.sleep(dur)
    led.value = 0
    time.sleep(dur)
    repeat -= 1

# --- set timer   ------------------------------------------------------------

def set_timer(secs):
  if secs < 256:
    rtc.timerA_frequency = rtc.TIMER_FREQ_1HZ
    rtc.timerA_value = secs
  else:
    rtc.timerA_frequency = rtc.TIMER_FREQ_1_60HZ
    rtc.timerA_value = min(255,int(secs/60)+1)
  
  # enable timer and interrupt
  rtc.timerA_interrupt = True
  rtc.timerA_enabled   = True

# --- main program   ---------------------------------------------------------

# disable timer interrupt and clear timer
rtc_timerA_status  = False
rtc.timerA_pulsed  = True

# Simulate some work by blinking the LED
active_until = time.monotonic() + ON_TIME
print("working...")
while time.monotonic() < active_until:
  blink()

# finished working, set timer and exit
set_timer(OFF_TIME)
done.value = 1 # signal "done" to external circuit - this should turn us off
time.sleep(0.2)
done.value = 0
time.sleep(0.5)

# this won't happen (it should not)
blink(LED_TIME/3,4)
time.sleep(2)
