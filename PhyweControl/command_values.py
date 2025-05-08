"""
Enums with the command values for the function generator
DM - 05/2025
"""

from enum import Enum


class FrameType(Enum):
    """
    Communication frame types as defined on page 5 of the interface description
    """
    DATA_READ = 0x01
    DATA_RESPONSE_A = 0x0A
    DATA_RESPONSE_B = 0x0B
    WRITE_CONFIG = 0x11
    READ_CONFIG = 0x12
    CONFIG_OK = 0x18
    CONFIG_ERROR = 0x19
    CONFIG_RESPONSE = 0x1A
    COMMAND_OK = 0x1B
    MEAS_START = 0x13
    MEAS_STOP = 0x32
    PC_MODE_ON = 0x4D
    PC_MODE_OFF = 0x4E
    APPLY_VALUES = 0x4F
    COMM_ERROR = 0xFF
    RAMP_START = 0x51
    RAMP_STOP = 0x52


class Parameter:
    """
    Parameter class including parameter index and length
    """

    def __init__(self, index: int, num_bytes: int):
        self.index = index
        self.num_bytes = num_bytes


class BaseParameters(Enum):
    """
    Parameters of the base device (address 0x100)
    """
    HW_VERSION = Parameter(0x00, 1)
    FW_VERSION = Parameter(0x01, 2)
    DEVICE_CLASS = Parameter(0x02, 1)
    OUTPUT_MODE = Parameter(0x03, 1)
    SIGNAL_SHAPE = Parameter(0x04, 1)
    FREQUENCY = Parameter(0x05, 4)
    AMPLITUDE = Parameter(0x06, 2)
    OFFSET = Parameter(0x07, 2)
    F_RAMP_START = Parameter(0x08, 4)
    F_RAMP_STOP = Parameter(0x09, 4)
    F_RAMP_PAUSE = Parameter(0x0A, 4)
    F_RAMP_STEP = Parameter(0x0B, 4)
    F_RAMP_SHAPE = Parameter(0x0C, 1)
    V_RAMP_START = Parameter(0x0D, 2)
    V_RAMP_STOP = Parameter(0x0E, 2)
    V_RAMP_PAUSE = Parameter(0x0F, 4)
    V_RAMP_STEP = Parameter(0x10, 2)
    F_RAMP_DURATION = Parameter(0x11, 4)
    V_RAMP_DURATION = Parameter(0x12, 4)
    F_RAMP_REPEAT = Parameter(0x13, 1)
    V_RAMP_REPEAT = Parameter(0x14, 1)


class SensorParameters(Enum):
    """
    Parameters of the virtual sensor unit (address 0x101)
    """
    EEPROM_WRITTEN = Parameter(0x00, 1)
    SENSOR_ID = Parameter(0x01, 1)
    SERIAL_NUM = Parameter(0x02, 4)
    VENDOR_ID = Parameter(0x04, 1)
    DATA_RATE_MAX = Parameter(0x05, 4)
    DATA_RATE_TYP = Parameter(0x06, 4)
    SENSOR_CHANNEL_BITMASK = Parameter(0x07, 1)
    BURST_CHANNEL_BITMASK = Parameter(0x08, 1)
    CALIBRATION_ALLOWED = Parameter(0x09, 1)
    SAMPLE_UNIT = Parameter(0x0a, 1)
    REVISION = Parameter(0x0b, 1)
    WARM_UP_TIME = Parameter(0x0c, 1)
    EQUATION_TYPE = Parameter(0x0d, 1)
    CALIBRATION_PAGE_NUM = Parameter(0x0e, 1)
    CALIBRATION_PAGE_CURRENT = Parameter(0x0f, 1)


class SignalShape(Enum):
    """
    Signal shapes/modes
    """
    SINE = 0
    TRIANGLE = 1
    SQUARE = 2
    F_RAMP = 3
    V_RAMP = 4
