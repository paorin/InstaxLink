# InstaxLink
Python utility to print a JPG image to an Instax Link printer.

Uses GATT on BLE, so it works with the (IOS) device name.

Requires bleak.

Should work on Mac, Linux and Windows, though it's tested only on Mac.

Usage:
    InstaxLink.py [-h] [-n DEVICE_NAME] [-i IMAGE_PATH] [-d]

    options:
    -h, --help              Show help message
    -n DEVICE_NAME, --device-name DEVICE_NAME
                            Device name, format INSTAX-xxxxxxxx(IOS)
    -i IMAGE_PATH, --image-path IMAGE_PATH
                            Path to the image file
    -d, --debug

Credit to InstaxBLE for suggesting how to sniff the BLE packets and how to reverse engineer the communication of the Android app.
