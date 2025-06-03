import PhyweControl

import time

# look up the port of your function generator and adjust it accordingly. On Windows, the port is displayed in the
# device manager and has the format "COMx". On Linux, it shows up in /dev in the format "ttyUSBx". Use the complete
# path (/dev/ttyUSBx) here.
fg = PhyweControl.FunctionGenerator("COM10")

# the ramp mode is selected as a signal shape
fg.set_shape(PhyweControl.SignalShape.F_RAMP)

# ramp setup: ramp from 100 Hz to 1000 hz in 2 Hz steps. Each step takes 0.1 s. The function shape is a
# sine wave and the ramp isn't repeated.
fg.ramp_setup_f(100, 1000, 0.1, 2, False, PhyweControl.SignalShape.SINE)

ramp_time = fg.ramp_duration()

print(f"The ramp will take {ramp_time} seconds.")
fg.set_output_state(True)
fg.ramp_start()

time.sleep(ramp_time)

fg.set_output_state(False)
