# JCS 06/07/14
# BLE iBeaconScanner based on https://github.com/adamf/BLE/blob/master/ble-scanner.py
# https://github.com/pauloborges/bluez/blob/master/tools/hcitool.c for lescan
# https://kernel.googlesource.com/pub/scm/bluetooth/bluez/+/5.6/lib/hci.h for opcodes
# https://github.com/pauloborges/bluez/blob/master/lib/hci.c#L2782 for functions used by lescan

# performs a simple device inquiry, and returns a list of ble advertizements
# discovered device


def hex_bytes(g, sep=' '):
    """
    Returns the hexadecimal bytes that comprise g, which can be an iterator
    or iterable, separated with sep.
    """

    return sep.join("{:02x}".format(i) for i in g)


class Packet:

    def __init__(self, data):
        self.data = data
        self.pos = 0

        # Debug print of packet.
        # print(" ".join("{:02x}".format(i) for i in data))

        self.read_byte()  # Number of packets (always 1).
        self.read_byte()  # Event type.
        self.read_byte()  # Mac type.

        mac = self.read_bytes(6)
        self.mac = hex_bytes(reversed(mac), ":")

        # A map from attr byte to value.
        self.attr = { }

        # The number of remaining bytes of payload.
        remaining = self.read_byte()

        while remaining:
            attr_len = self.read_byte()
            tag = self.read_byte()
            content = self.read_bytes(attr_len - 1)

            remaining -= attr_len + 1

            self.attr[tag] = content

        self.rssi = self.read_byte() + -256

    def read_byte(self):
        rv = self.data[self.pos]
        self.pos += 1
        return rv

    def read_bytes(self, length):
        rv = self.data[self.pos:self.pos+length]
        self.pos += length
        return rv


import sys
import struct
import bluetooth._bluetooth as bluez  # @UnresolvedImport

LE_META_EVENT = 0x3e
LE_PUBLIC_ADDRESS=0x00
LE_RANDOM_ADDRESS=0x01
LE_SET_SCAN_PARAMETERS_CP_SIZE=7
OGF_LE_CTL=0x08
OCF_LE_SET_SCAN_PARAMETERS=0x000B
OCF_LE_SET_SCAN_ENABLE=0x000C
OCF_LE_CREATE_CONN=0x000D

LE_ROLE_MASTER = 0x00
LE_ROLE_SLAVE = 0x01

# these are actually subevents of LE_META_EVENT
EVT_LE_CONN_COMPLETE=0x01
EVT_LE_ADVERTISING_REPORT=0x02
EVT_LE_CONN_UPDATE_COMPLETE=0x03
EVT_LE_READ_REMOTE_USED_FEATURES_COMPLETE=0x04

# Advertisment event types
ADV_IND=0x00
ADV_DIRECT_IND=0x01
ADV_SCAN_IND=0x02
ADV_NONCONN_IND=0x03
ADV_SCAN_RSP=0x04

# hci_le_set_scan_enable(dd, 0x01, filter_dup, 1000);
# memset(&scan_cp, 0, sizeof(scan_cp));
#uint8_t         enable;
#       uint8_t         filter_dup;
#        scan_cp.enable = enable;
#        scan_cp.filter_dup = filter_dup;
#
#        memset(&rq, 0, sizeof(rq));
#        rq.ogf = OGF_LE_CTL;
#        rq.ocf = OCF_LE_SET_SCAN_ENABLE;
#        rq.cparam = &scan_cp;
#        rq.clen = LE_SET_SCAN_ENABLE_CP_SIZE;
#        rq.rparam = &status;
#        rq.rlen = 1;

#        if (hci_send_req(dd, &rq, to) < 0)
#                return -1;


# def hci_le_set_scan_parameters(sock):
#     old_filter = sock.getsockopt( bluez.SOL_HCI, bluez.HCI_FILTER, 14)
#
#     SCAN_RANDOM = 0x01
#     OWN_TYPE = SCAN_RANDOM
#     SCAN_TYPE = 0x01


def generate_le_scan():

    sock = bluez.hci_open_dev(0)

    def hci_toggle_le_scan(sock, enable):
        cmd_pkt = struct.pack("<BB", enable, 0x00)
        bluez.hci_send_cmd(sock, OGF_LE_CTL, OCF_LE_SET_SCAN_ENABLE, cmd_pkt)

    # Enable the scan.
    hci_toggle_le_scan(sock, 0x01)

    old_filter = sock.getsockopt( bluez.SOL_HCI, bluez.HCI_FILTER, 14)

    try:

        # perform a device inquiry on bluetooth device #0
        # The inquiry should last 8 * 1.28 = 10.24 seconds
        # before the inquiry is performed, bluez should flush its cache of
        # previously discovered devices
        flt = bluez.hci_filter_new()
        bluez.hci_filter_all_events(flt)
        bluez.hci_filter_set_ptype(flt, bluez.HCI_EVENT_PKT)
        sock.setsockopt( bluez.SOL_HCI, bluez.HCI_FILTER, flt )

        while True:
            pkt = sock.recv(255)
            ptype, event, plen = struct.unpack("BBB", pkt[:3])

            if event == bluez.EVT_INQUIRY_RESULT_WITH_RSSI:
                i =0
            elif event == bluez.EVT_NUM_COMP_PKTS:
                i =0
            elif event == bluez.EVT_DISCONN_COMPLETE:
                i =0
            elif event == LE_META_EVENT:
                subevent = pkt[3]
                pkt = pkt[4:]
                if subevent == EVT_LE_CONN_COMPLETE:
                    pass
                elif subevent == EVT_LE_ADVERTISING_REPORT:
                    yield Packet(pkt)

    finally:

        sock.setsockopt( bluez.SOL_HCI, bluez.HCI_FILTER, old_filter )
        hci_toggle_le_scan(sock, 0x00)


import time
import requests
import traceback


def notify(message):
    try:
        requests.post("https://api.simplepush.io/send", data={ "key" : "HeS3cQ", "title" : "Mbx", "msg": message })
    except:
        traceback.print_exc()


def twos_comp(val, bits):
    """compute the 2's complement of int value val"""
    if (val & (1 << (bits - 1))) != 0:  # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)        # compute negative value
    return val


def main():

    last_changes = -1
    last_serial = -1

    for p in generate_le_scan():
        if p.mac != "de:f6:93:86:32:b1":
            continue

        data = p.attr[0xff]

        now = time.strftime("%Y-%m-%d %H:%M:%S")

        # The voltage from the battery.
        voltage = 3.6 * ((data[3] << 8) | data[2]) / 0xfff

        # The number of times the switch has changed.
        changes = data[4]

        # The current state of the switch (0=closed, 1=open).
        state = data[5]

        # The temperature.
        temp_c = twos_comp(data[6], 8) / 2.0
        temp_f = 32 + 9.0 * temp_c / 5.0

        # A serial number that increments each time the BLE payload changes.
        serial = data[7]

        # print(list(data))

        message = f"{now} voltage={voltage:.3f} changes={changes} state={state} temp={temp_f:.1f} serial={serial}"
        print(message, end='\r')

        if changes != last_changes:
            if last_changes != -1:
                notify(message)
            last_changes = changes

        if serial != last_serial:
            with open("blelog.txt", "a") as f:
                print(f'{now}\t{changes}\t{voltage:.3f}\t{temp_f:.1f}\t{serial}\t{p.rssi}', file=f)

            if last_serial != -1:
                print()

            last_serial = serial

        sys.stdout.flush()


if __name__ == "__main__":
    main()
