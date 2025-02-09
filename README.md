# InstaxLink
Python utility to print a JPG image to an Instax Link printer.

It should work with Instax Link WIDE, Instax SQUARE Link and Instax mini Link (the new generation of printers that use Bluetooth instead of WiFi), though it's tested only with Instax Link WIDE.

The main motivation of this program is to send to the printer an unaltered version of a JPG image produced with a proper image editing software, avoiding the automatic conversion, cropping and compression that occurs if you use the app on a phone or the recently released computer driver. Therefore the image you supply should already meet the requirements of the printer in ters of size in pixels and maximum size in KB, InstaxLink doesn't deliberately take care of format conversion, resizing and recompression.

InstaxLink checks that the file you supply in IMAGE_PATH complies with what the printer supports, which is determined with a command at runtime. If it doesn't, it prints a message telling what the printer expects. So if you want to know what are the specifications of the file that work with your printer, send any file and you'll know from the output message.

For example Instax Link WIDE wants a JPG file with height 840 pixels, width 1260 pixels and maximum size 337920 KB (despite Fujifilm telling that the maximum resolution is 800x1260). Note however that the visible part of the image will be approximately 775 by 1235 pixels, so if you really care about not having it cropped when exposed to the film, provide a JPG with a white border of 32 pixels at each long side and of 12 pixels on each short side.

The second motivation of this program is to use the printer with computers and operating systems not supported by the official apps and drivers released by Fujifilm, even legacy computers that don't support recent versions of Bluetooth and legacy operating systems.

The Instax Link exposes two Bluetooth devices, one with IOS in the name, which uses GATT on Bluetooth Low Energy (BLE), and one with ANDROID in the name, which uses an RFCOMM socket on Bluetooth Classic (SDR/EDR). InstaxLink supports both (using bleak for BLE and pybluez for SDR/EDR), and chooses the applicable one based on the DEVICE_NAME provided.

It should therefore work on Mac, Linux and Windows with a pretty wide range of operating systems, though it's only tested on a Mid 2010 iMac running High Sierra and an M2 MacBook Air running Sequoia.

    Usage:
    InstaxLink.py [-h] [-n DEVICE_NAME] [-i IMAGE_PATH] [-d]

    Options:
    -h, --help              Show help message
    -n DEVICE_NAME, --device-name DEVICE_NAME
                            Device name, format INSTAX-xxxxxxxx(IOS) or INSTAX-xxxxxxxx(ANDROID)
    -i IMAGE_PATH, --image-path IMAGE_PATH
                            Path to the image file
    -d, --debug

Credit to InstaxBLE for suggesting how to sniff the Bluetooth packets and how to reverse engineer the communication of the Android app.
