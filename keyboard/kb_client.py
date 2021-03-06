#!/usr/bin/python3
#
# Thanhle Bluetooth keyboard emulation service
# keyboard copy client.
# Reads local key events and forwards them to the btk_server DBUS service
#

import os  # used to all external commands
import sys  # used to exit the script
import dbus
import dbus.service
import dbus.mainloop.glib
import time
import evdev  # used to get input from the keyboard
from evdev import ecodes, InputDevice, list_devices
import keymap  # used to map evdev input to hid keodes
import select
import logging
from logging import error

logging.basicConfig(level=logging.DEBUG)

DBUS_OBJ_BTK_NAME = 'org.thanhle.btkbservice'
DBUS_OBJ_BTK_PATH = '/org/thanhle/btkbservice'

# Define a client to listen to local key events
class Keyboard():

    def __init__(self):
        # the structure for a bt keyboard input report (size is 10 bytes)

        self.state = [
            0xA1,  # this is an input report
            0x01,  # Usage report = Keyboard
            # Bit array for Modifier keys
            [0,  # Right GUI - Windows Key
             0,  # Right ALT
             0,  # Right Shift
             0,  # Right Control
             0,  # Left GUI
             0,  # Left ALT
             0,  # Left Shift
             0],  # Left Control
            0x00,  # Vendor reserved
            0x00,  # rest is space for 6 keys
            0x00,
            0x00,
            0x00,
            0x00,
            0x00]

        print("setting up DBus Client")

        self.bus = dbus.SystemBus()
        self.btkservice = self.bus.get_object(DBUS_OBJ_BTK_NAME, DBUS_OBJ_BTK_PATH)
        self.iface = dbus.Interface(self.btkservice, DBUS_OBJ_BTK_NAME)
        print("waiting for keyboard")
        self.wait_keyboards()

    def wait_keyboards(self, device_dir='/dev/input'):
        have_dev = False
        # keep trying to key a keyboard
        while have_dev == False:
            devices = [InputDevice(path) for path in list_devices(device_dir)]
            self.keyboards = [dev for dev in devices if "Keyboard" in dev.name]
            if self.keyboards:
                for keyboard in self.keyboards:
                    print("find keyboard: ", keyboard.name)
                break

            print("Keyboard not found, waiting 3 seconds and retrying")
            time.sleep(3)

    def change_state(self, event):
        evdev_code = ecodes.KEY[event.code]
        modkey_element = keymap.modkey(evdev_code)

        if modkey_element > 0:
            if self.state[2][modkey_element] == 0:
                self.state[2][modkey_element] = 1
            else:
                self.state[2][modkey_element] = 0
        else:
            # Get the keycode of the key
            hex_key = keymap.convert(ecodes.KEY[event.code])
            if hex_key == -1:
                return

            # Loop through elements 4 to 9 of the inport report structure
            for i in range(4, 10):
                if self.state[i] == hex_key and event.value == 0:
                    # Code 0 so we need to depress it
                    self.state[i] = 0x00
                elif self.state[i] == 0x00 and event.value == 1:
                    # if the current space if empty and the key is being pressed
                    self.state[i] = hex_key
                    break

    # poll for keyboard events
    def event_loop(self):
        fd_to_device = {dev.fd: dev for dev in self.keyboards}
        while True:
            read_list, _, _ = select.select(fd_to_device, [], [])
            for fd in read_list:
                for event in fd_to_device[fd].read():
                    # only bother if we hit a key and its an up or down event
                    if event.type == ecodes.EV_KEY and event.value < 2:
                        self.change_state(event)
                        print("sending key: %s, status: %s, key board code: %d, bluetooth code: %d" % (
                                ecodes.KEY[event.code],
                                ("UP" if event.value == 0 else "DOWN"),
                                event.code, 
                                self.state[4]
                        ))
                        self.send_input()

    # forward keyboard events to the dbus service
    def send_input(self):
        modifier_bin_str = ""
        element = self.state[2]
        for bit in element:
            modifier_bin_str += str(bit)
        try:
            self.iface.send_keys(int(modifier_bin_str, 2), self.state[4:10])
        except dbus.exceptions.DBusException as err:
            error(err)

if __name__ == "__main__":

    print("Setting up keyboard")

    kb = Keyboard()

    print("starting event loop")
    kb.event_loop()
