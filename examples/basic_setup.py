import PhyweControl

import time

# look up the port of your function generator and adjust it accordingly. On Windows, the port is displayed in the
# device manager and has the format "COMx". On Linux, it shows up in /dev in the format "ttyUSBx". Use the complete
# path (/dev/ttyUSBx) here.
fg = PhyweControl.FunctionGenerator("COM10")

fg.set_configuration(440, 5, 0)
fg.set_shape(PhyweControl.SignalShape.TRIANGLE)

fg.set_output_state(True)
time.sleep(0.5)
fg.set_output_state(False)
