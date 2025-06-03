import time
import logging

import serial
from serial.serialutil import SerialException

from .function_generator import FunctionGenerator_abc
from .command_values import FrameType, BaseParameters, SensorParameters, SignalShape

START_BYTE = bytearray([0x7D])
STOP_BYTE = bytearray([0x7E])

BAUD_RATE = 921600

RETRIES = 2

SEND_PAUSE = 0.2
SERIAL_TIMEOUT = 1

BASE_ADDR = 0x100
SENSOR_ADDR = 0x101

FREQ_MAX = 999999
FREQ_MIN = 0.1

AMP_MAX = 20
AMP_MIN = 0

OFF_MAX = 10
OFF_MIN = -10

RAMP_PAUSE_MAX = 9.999
RAMP_PAUSE_MIN = 0.01

RAMP_VSTEP_MAX = 10
RAMP_VSTEP_MIN = 0.001


class FunctionGenerator_Phywe(FunctionGenerator_abc):
    def __init__(self, port: str, log: bool = False, verbose: bool = False):
        """
        Initialize the object for control of a Phywe function generator
        :param port: the COM port of the Phywe function generator
        :param log: whether to log the communication
        :param verbose: whether to print the raw communication to the terminal
        """
        self.port = port
        self.interface = serial.Serial(port, BAUD_RATE, timeout=SERIAL_TIMEOUT)
        self.interface.reset_input_buffer()
        self.verbose = verbose
        self.log = log
        self.send_timestamp = time.time()

        if log:
            logging.basicConfig(
                filename="function_generator.log",
                encoding="utf-8",
                filemode="a",
                format="%(asctime)s - %(levelname)s - %(message)s",
                level=logging.DEBUG,
            )

    def release(self):
        if self.interface.is_open:
            self.interface.close()

    def _send(self, frame_index: FrameType, address: int, data: bytes):
        # wait until at least 0.2 seconds have passed since the last send
        time.sleep(max(0.0, SEND_PAUSE - (time.time() - self.send_timestamp)))
        address_bytes = address.to_bytes(2, "little")
        frame_bytes = frame_index.value.to_bytes(1, "little")
        frame = frame_bytes + address_bytes + data
        length = len(frame)
        frame = bytearray([length]) + frame
        if self.log:
            logging.debug(f"Tx: {(START_BYTE + frame + STOP_BYTE).hex()}")
        if self.verbose:
            print(f"Tx: {(START_BYTE + frame + STOP_BYTE).hex()}")
        self.interface.write(START_BYTE + frame + STOP_BYTE)
        self.send_timestamp = time.time()

    def _send_with_ack(self, frame_index: FrameType, address: int, data: bytes, tries):
        failed_tries = 0
        while failed_tries < tries:
            try:
                self._send(frame_index, address, data)
                response = self._receive()
                if self.verbose:
                    print(response.hex())
                break
            except SerialException:
                self.interface.close()
                logging.error("Failed to send data to function generator")
                input("Restart the function generator, then press enter\a")
                self.interface = serial.Serial(self.port, BAUD_RATE, timeout=SERIAL_TIMEOUT)
                self.interface.reset_input_buffer()
                failed_tries += 1
        if failed_tries >= tries:
            raise SerialException

    def _receive(self):
        try:
            response_header = self.interface.read(2)
            length = response_header[1]
            response_data = self.interface.read(length + 1)[:-1]  # cutting off end byte
        except IndexError:
            raise SerialException
        if self.log:
            logging.debug(f"Rx: {response_header.hex() + response_data.hex()}")
        return response_data

    def set_parameter(self, address: int, parameter: BaseParameters | SensorParameters, value: int):
        """
        Set a single parameter - changes aren't applied until confirm() is called
        :param address: address of the device
        :param parameter: address of the parameter
        :param value: new value of the parameter
        """
        data = parameter.value.index.to_bytes(1) + value.to_bytes(parameter.value.num_bytes, "little", signed=True)
        self._send_with_ack(FrameType.WRITE_CONFIG, address, data, RETRIES)

    def confirm(self):
        """
        Apply previous changes to parameters
        """
        self._send_with_ack(FrameType.APPLY_VALUES, BASE_ADDR, b"", RETRIES)

    def get_parameter(self, address: int, parameter: BaseParameters | SensorParameters) -> int:
        """
        Returns the set value of a parameter
        :param address: address of the device
        :param parameter: address of the parameter
        :return: current value of the parameter
        """
        self.interface.reset_input_buffer()
        self._send(FrameType.READ_CONFIG, address, parameter.value.index.to_bytes())
        response = self._receive()[4:]
        return int.from_bytes(response, "little")

    def _set_frequency(self, frequency: float, channel=None, **kwargs):
        """
        Set the frequency of the output
        :param frequency: frequency in Hz
        :param channel: included for compatibility, should not be used
        """

        if channel is not None and channel != 1:
            raise NotImplementedError("This function generator does not have multiple channels")

        if frequency > FREQ_MAX or frequency < FREQ_MIN:
            raise ValueError(f"Frequency must be between {FREQ_MIN} Hz and {FREQ_MAX} Hz")

        self.set_parameter(BASE_ADDR, BaseParameters.FREQUENCY, round(frequency * 10))
        self.confirm()

    def _set_amplitude(self, amplitude: float, channel=None, **kwargs):
        """
        Set the amplitude of the output
        :param amplitude: amplitude in V for power output, 100 mV for Headphones
        :param channel: included for compatibility, should not be used
        """
        if channel is not None and channel != 1:
            raise NotImplementedError("This function generator does not have multiple channels")

        if amplitude < AMP_MIN or amplitude > AMP_MAX:
            raise ValueError(f"Amplitude must be between {AMP_MIN} V and {AMP_MAX} V")

        self.set_parameter(BASE_ADDR, BaseParameters.AMPLITUDE, round(amplitude * 1000))
        self.confirm()

    def _set_offset(self, offset: float, channel=None, **kwargs):
        """
        Set the offset of the output
        :param offset: offset in V
        :param channel: included for compatibility, should not be used
        """
        if channel is not None and channel != 1:
            raise NotImplementedError("This function generator does not have multiple channels")

        if offset < OFF_MIN or offset > OFF_MAX:
            raise ValueError(f"Offset must be between {OFF_MIN} V and {OFF_MAX} V")

        self.set_parameter(BASE_ADDR, BaseParameters.OFFSET, round(offset * 1000))
        self.confirm()

    def _set_output_state(self, state: bool, channel=None, **kwargs):
        """
        Set the output state of the function generator
        :param state: output state: True - on, False - off
        :param channel: included for compatibility, should not be used
        """
        if channel is not None and channel != 1:
            raise NotImplementedError("This function generator does not have multiple channels")

        self.set_parameter(BASE_ADDR, BaseParameters.OUTPUT_MODE, int(not state))

    def get_frequency(self):
        """
        Get the frequency of the output
        :return: frequency in Hz
        """
        return self.get_parameter(BASE_ADDR, BaseParameters.FREQUENCY) / 10

    def get_amplitude(self):
        """
        Get the amplitude of the output
        :return: amplitude in V for power output, 100 mV for Headphones
        """
        return self.get_parameter(BASE_ADDR, BaseParameters.AMPLITUDE) / 1000

    def set_shape(self, shape: SignalShape):
        """
        Set the output shape of the function generator
        :param shape: output shape
        """
        self.set_parameter(BASE_ADDR, BaseParameters.SIGNAL_SHAPE, shape.value)

    def ramp_setup_f(self, start_freq: float, end_freq: float, step_time: float, step: float, repeat: bool = False,
                     shape: SignalShape = SignalShape.SINE):
        """
        Set up the function generator for a frequency ramp
        :param start_freq: start frequency in Hz
        :param end_freq: end frequency in Hz
        :param step_time: time in seconds between steps
        :param step: step size in Hz
        :param repeat: whether to repeat the ramp
        :param shape: signal shape
        """
        if start_freq < FREQ_MIN or start_freq > FREQ_MAX:
            raise ValueError(f"Frequency must be between {FREQ_MIN} Hz and {FREQ_MAX} Hz")
        if end_freq < FREQ_MIN or end_freq > FREQ_MAX:
            raise ValueError(f"Frequency must be between {FREQ_MIN} Hz and {FREQ_MAX} Hz")
        if step < FREQ_MIN or step > FREQ_MAX:
            raise ValueError(f"Frequency must be between {FREQ_MIN} Hz and {FREQ_MAX} Hz")

        if step_time < RAMP_PAUSE_MIN or step_time > RAMP_PAUSE_MAX:
            raise ValueError(f"Step time must be between {RAMP_PAUSE_MIN} ms and {RAMP_PAUSE_MAX} ms")

        if shape == SignalShape.F_RAMP or shape == SignalShape.V_RAMP:
            raise ValueError("Signal shape can't be a ramp type")

        self.set_parameter(BASE_ADDR, BaseParameters.F_RAMP_START, round(start_freq * 10))
        self.set_parameter(BASE_ADDR, BaseParameters.F_RAMP_STOP, round(end_freq * 10))
        self.set_parameter(BASE_ADDR, BaseParameters.F_RAMP_PAUSE, round(step_time * 1000))
        self.set_parameter(BASE_ADDR, BaseParameters.F_RAMP_STEP, round(step * 10))
        self.set_parameter(BASE_ADDR, BaseParameters.F_RAMP_REPEAT, int(repeat))
        self.set_parameter(BASE_ADDR, BaseParameters.F_RAMP_SHAPE, shape.value)
        self.set_shape(SignalShape.F_RAMP)
        self.confirm()

    def ramp_setup_v(self, start_volt: float, end_volt: float, step_time: float, step: float, repeat: bool = False):
        """
        Set up the function generator for a voltage ramp
        :param start_volt: start voltage in V
        :param end_volt: end voltage in V
        :param step_time: time in seconds between steps
        :param step: step size in V
        :param repeat: whether to repeat the ramp
        """

        if start_volt < OFF_MIN or start_volt > OFF_MAX:
            raise ValueError(f"Offset must be between {OFF_MIN} V and {OFF_MAX} V")
        if end_volt < OFF_MIN or end_volt > OFF_MAX:
            raise ValueError(f"Offset must be between {OFF_MIN} V and {OFF_MAX} V")

        if step < RAMP_VSTEP_MIN or step > RAMP_VSTEP_MAX:
            raise ValueError(f"Voltage step must be between {RAMP_VSTEP_MIN} mV and {RAMP_VSTEP_MAX} mV")

        if step_time < RAMP_PAUSE_MIN or step_time > RAMP_PAUSE_MAX:
            raise ValueError(f"Step time must be between {RAMP_PAUSE_MIN} ms and {RAMP_PAUSE_MAX} ms")

        self.set_parameter(BASE_ADDR, BaseParameters.V_RAMP_START, round(start_volt * 1e3))
        self.set_parameter(BASE_ADDR, BaseParameters.V_RAMP_STOP, round(end_volt * 1e3))
        self.set_parameter(BASE_ADDR, BaseParameters.V_RAMP_PAUSE, round(step_time * 1000))
        self.set_parameter(BASE_ADDR, BaseParameters.V_RAMP_STEP, round(step * 1e3))
        self.set_parameter(BASE_ADDR, BaseParameters.V_RAMP_REPEAT, int(repeat))
        self.set_shape(SignalShape.V_RAMP)

    def ramp_start(self):
        """
        Start the frequency ramp
        """
        self._send_with_ack(FrameType.RAMP_START, BASE_ADDR, b"", RETRIES)

    def ramp_stop(self):
        """
        Stop the frequency ramp
        """
        self._send_with_ack(FrameType.RAMP_STOP, BASE_ADDR, b"", RETRIES)

    def ramp_duration(self):
        """
        Get the duration of the frequency ramp
        """
        return self.get_parameter(BASE_ADDR, BaseParameters.F_RAMP_DURATION) / 1000


if __name__ == "__main__":
    fg = FunctionGenerator_Phywe("/dev/functionGenerator")  # initialize serial interface
    fg.set_configuration(440, 3.5)  # change to an example setup
    fg._set_output_state(True)  # turn power output on
    time.sleep(2)
    fg._set_output_state(False)  # turn power output off
