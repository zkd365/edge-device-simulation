# Edge System Simulation

## Instructions

### Running the Files

First, you want to dowload this repo as a zip file. Then, open separate terminals. Type `python3` into the terminal and add a space. Then...

Run the python files in this order:

1. urb-OFDMA
2. server-OFDMA
3. the device files

Go to the __How to Add a New Device__ section to add more devices.

But first thing's first...

### Updating Values

When adding new devices, you will want to change the current IP address to your device's IP address (follow the instructions in the __IP Address__ section).

You'll notice how each device has a unique ID. You will want to add an ID for any new device you add, so follow the instructions in the section below (titled __Device IDs__) to generate a new ID.

Once you've generated a device ID, add it to the following places:

- Device Files: line 34
- Server File: line 38 (after the four devices)

### IP Addresses

You will want to change the IP address to your device's IPv4 address on the following lines in the according files:

- Device Files: 55
- Server File: 204

## How to Add a New Device

In order to add a new device, follow these steps:

1. Duplicate a device file and rename it to the new device number (i.e. 1, 2, 3, etc.).
2. You will need to change the IP address from the current value to your device's IPv4 address. Follow the instructions in the section titled __IP Addresses__ to change those values in the correct places.
3. In `urb-OFDMA`, copy and paste a new dictionary from line 38 (`self.initial_cfg`). Make sure the device ID is the same as the device ID within the file. See the section below titled __Device IDs__ to generate a new ID.

## Device IDs

Each device has a unique alphanumeric ID. Use the `device_id.py` file to generate a random device ID and add this value to line 34 in the device file, and to the new dictionary you add in the URB.

## Got Questions?

Reach out to me if you have any further questions about updating files.
