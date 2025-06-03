# PhyweControl
Python package for controlling the "Digital Function Generator" produced by PHYWE Systeme GmbH & Co. KG.

## Installation 
The package is included in the python packaging index and can be installed via ```pip```:

    pip install phywecontrol


## Driver Installation
### Windows
The function generator should show up as "Digital Function Generator" in the device manager. Select "Update Driver" 
and point the installation wizard to the [driver](https://github.com/Schallform/PhyweControl/tree/main/driver) folder.

Open the device properties and enable "Load VCP" in the "Advanced" Tab. After unplugging and re-plugging, the function 
generator shows up as COM Port in the device manager.

### Linux
The device driver is included in the Linux kernel as ```ftdi_sio```. However, the vendor and product id of the 
function generator are not registered in the driver and must be added manually.

Load the module:

    modprobe ftio

Register the Device IDs for the module (if this doesn't work, the module location might be different on your system):

    echo 0403 a303 > /sys/bus/usb-serial/drivers/ftdi_sio/new_id

After plugging in the function generator, it should show up as ``/dev/ttyUSBx``.

To make this change permanent:

Add the file ``/etc/udev/rules.d/99-phywe.rules``:

    ACTION=="add", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="a303", RUN+="/sbin/modprobe ftdi_sio" RUN+="/bin/sh -c 'echo 0403 a303 > /sys/bus/usb-serial/drivers/ftdi_sio/new_id'"

## Third-Party Content
The device drivers and interface docs in this repository are authored by PHYWE Systeme GmbH & Co. KG 
and are used with permission. All rights remain with the original authors.
