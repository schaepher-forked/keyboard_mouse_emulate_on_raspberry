#!/usr/bin/python3
#
# thanhle Bluetooth keyboard/Mouse emulator DBUS Service
#

import dbus

DBUS_OBJ_BTK_NAME = "org.thanhle.btkbservice"
DBUS_OBJ_BTK_PATH = "/org/thanhle/btkbservice"

class BTKbService(dbus.service.Object):
    def __init__(self, device):
        # set up as a dbus service
        dbus_conn = dbus.service.BusName(DBUS_OBJ_BTK_NAME, bus=dbus.SystemBus())
        dbus.service.Object.__init__(self, dbus_conn, DBUS_OBJ_BTK_PATH)
        # setup our device
        self.device = device

    @dbus.service.method(DBUS_OBJ_BTK_NAME, in_signature="yay")
    def send_keys(self, modifier_byte, keys):
        state = [0xA1, 1, 0, 0, 0, 0, 0, 0, 0, 0]
        state[2] = int(modifier_byte)
        count = 4
        for key_code in keys:
            if count < 10:
                state[count] = int(key_code)
            count += 1
        self.device.send_string(state)

    @dbus.service.method(DBUS_OBJ_BTK_NAME, in_signature="yay")
    def send_mouse(self, modifier_byte, keys):
        state = [0xA1, 2, 0, 0, 0, 0]
        count = 2
        for key_code in keys:
            if count < 6:
                state[count] = int(key_code)
            count += 1
        self.device.send_string(state)
