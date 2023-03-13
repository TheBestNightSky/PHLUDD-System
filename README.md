# PHLUDD-System
Back end code for smart household flood detection system

This program is intended to be run on a raspberry pi 4B microcomputer with PHLUDD pcb plugged into the GPIO (pcb still under development)

The concept is simple enough, 1-7 water sensors are plugged into the PHLUDD pcb and placed in areas that are likely to experience flooding
ie: your basement

In the event water is detected at one of the sensors an alarm will sound, and notifications will be sent to configured recipients
giving users the early warning they need to prevent water damage from occuring.

The PHLUDD pcb also houses a 9v backup battery that will sound the alarm in the event that power to the raspberry pi is interupted,
And this software will monitor said battery and notify the users when it needs to be replaced.
Typical lifespan of the battery should be close to 1 year
