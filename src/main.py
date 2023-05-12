#-----------------------------------------------------------------------------
# Test program.
#
# The program supports two modes:
#
# timer-mode: blink the onboard LED for 10 seconds, then goe to sleep
#             and wakes up again after 15 seconds.
#
# alarm-mode: blink the onboard LED for 10 seconds, then goe to sleep
#             and wake up at the start of the next minute
#
# The countdown-timer of the RTC and works on a PCF8563 up to
# 15300 seconds (i.e. 255m or 4h15m). For longer intervals than
# 255 minutes use the alarm or switch to the PCF8523.
#
# Author: Bernhard Bablok
#
# Website: https://github.com/pcb-pico-en-control
#-----------------------------------------------------------------------------

OFF_MODE_TIMER = 0      # 0: use alarm, 1: use timer

import time
import board
import alarm
from digitalio import DigitalInOut, Direction, Pull

# imports for PCF8563
import busio
if OFF_MODE_TIMER:
  from adafruit_pcf8563.timer import Timer as PCF_RTC
else:
  from adafruit_pcf8563.pcf8563 import PCF8563 as PCF_RTC

# --- configuration   --------------------------------------------------------

PIN_DONE = board.GP4   # connect to 74HC74 CLK
PIN_SDA  = board.GP2   # connect to RTC
PIN_SCL  = board.GP3   # connect to RTC

LED_TIME = 0.5         # blink-duration
ON_TIME  = 10          # seconds on (blinking)
OFF_TIMER = 15         # seconds off (<= 15300 == 255*60)
OFF_ALARM = 1          # wake up in x minutes

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
    rtc.timer_frequency = rtc.TIMER_FREQ_1HZ
    rtc.timer_value = secs
  else:
    rtc.timer_frequency = rtc.TIMER_FREQ_1_60HZ
    rtc.timer_value = min(255,int(secs/60)+1)
  
  # enable timer and interrupt
  rtc.timer_interrupt = True
  rtc.timer_enabled   = True

# --- set alarm   ------------------------------------------------------------

def set_alarm(minutes):
  alarm_time = time.mktime(rtc.datetime) + 60*minutes
  rtc.alarm  = (time.localtime(alarm_time),"daily")
  rtc.alarm_interrupt = True

# --- main program   ---------------------------------------------------------

# disable timer interrupt and clear timer/alarm
if OFF_MODE_TIMER:
  rtc.timer_status    = False
  rtc.timer_pulsed    = False
  rtc.timer_interrupt = False
  rtc.timer_enabled   = False
else:
  rtc.alarm_status     = False
  rtc.alarm_interrupt  = False
  rtc.clockout_enabled = False
  if rtc.lost_power:
    rtc.datetime =time.struct_time((2022,10,3,13,5,12,0,277,-1))

# Simulate some work by blinking the LED
active_until = time.monotonic() + ON_TIME
print("working...")
while time.monotonic() < active_until:
  blink()

# finished working, set timer or alarm and exit
if OFF_MODE_TIMER:
  set_timer(OFF_TIMER)
else:
  set_alarm(OFF_ALARM)

done.value = 1 # signal "done" to external circuit - this should turn us off
time.sleep(0.2)
done.value = 0
time.sleep(0.5)

# this won't happen (it should not)
blink(LED_TIME/3,4)
time.sleep(2)
