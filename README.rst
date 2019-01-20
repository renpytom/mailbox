BLE Mailbox Monitor
-------------------

This uses an nRF52832 to monitor my mailbox for a switch to change status.
It sends back a Bluetooth Low Energy message containing the following data.

* VDD LSB
* VDD MSB
* The number of times pin 20 has changed status.
* Is pin 20 currently grounded?

The VDD is a value between 0x000 and 0xFFF, where 0xFFF is 3.6V.
