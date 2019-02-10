BLE Mailbox Monitor
-------------------

This uses an nRF52832 to monitor my mailbox for a switch to change status.
It sends back a Bluetooth Low Energy message containing the following data.

* VDD LSB
* VDD MSB
* The number of times pin 20 has changed status.
* Is pin 20 currently grounded?
* The temperature, in 2-'s compliment units of .5C.
* The number of times the data payload has changed.

The VDD is a value between 0x000 and 0xFFF, where 0xFFF is nominally 3.6V.
