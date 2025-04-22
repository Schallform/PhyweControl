import time
import logging

import serial
from serial.serialutil import SerialException
from enum import Enum

from .function_generator import FunctionGenerator

START_BYTE = bytearray([0x7D])
STOP_BYTE = bytearray([0x7E])

BAUD_RATE = 921600

RETRIES = 2


class FunctionGenerator_Phywe(FunctionGenerator):
    def __init__(self, port: str, log: bool = False, verbose: bool = False):
        """
        Initialize the object for control of a Phywe function generator
        :param port: the COM port of the Phywe function generator
        :param log: whether to log the communication
        """
        self.port = port
        self.interface = serial.Serial(port, BAUD_RATE, timeout=1)
        self.interface.flushInput()
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

    def __del__(self):
        self.release()

    def release(self):
        if self.interface.is_open:
            self.interface.close()

    def _send(self, frame_index, address, data, num_bytes):
        # wait until at least 0.2 seconds have passed since the last send
        time.sleep(max(0.0, 0.2 - (time.time() - self.send_timestamp)))
        data_bytes = data.to_bytes(num_bytes, "little")
        address_bytes = address.to_bytes(2, "little")
        frame_bytes = frame_index.to_bytes(1, "little")
        frame = frame_bytes + address_bytes + data_bytes
        length = len(frame)
        frame = bytearray([length]) + frame
        if self.log:
            logging.debug(f"Tx: {(START_BYTE + frame + STOP_BYTE).hex()}")
        if self.verbose:
            print(f"Tx: {(START_BYTE + frame + STOP_BYTE).hex()}")
        self.interface.write(START_BYTE + frame + STOP_BYTE)
        self.send_timestamp = time.time()

    def _send_with_ack(self, frame_index, address, data, num_bytes, tries):
        failed_tries = 0
        while failed_tries < tries:
            try:
                self._send(frame_index, address, data, num_bytes)
                response = self._receive()
                if self.verbose:
                    print(response.hex())
                break
            except SerialException:
                self.interface.close()
                logging.error("Failed to send data to function generator")
                input("Restart the function generator, then press enter\a")
                self.interface = serial.Serial(self.port, BAUD_RATE, timeout=1)
                self.interface.flushInput()
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

    def set_parameter(self, address: int, parameter: int, value: int, num_bytes: int):
        """
        Set a single parameter - changes aren't applied until confirm() is called
        :param address: address of the device
        :param parameter: address of the parameter
        :param value: new value of the parameter
        :param num_bytes: length of the parameter in bytes
        """
        data = parameter + value * (2 ** 8)
        self._send_with_ack(0x11, address, data, num_bytes + 1, RETRIES)

    def confirm(self):
        """
        Apply previous changes to parameters
        """
        self._send_with_ack(0x4f, 0x100, 0, 0, RETRIES)

    def get_parameter(self, address: int, parameter: int) -> int:
        """
        Returns the set value of a parameter
        :param address: address of the device
        :param parameter: address of the parameter
        :return: current value of the parameter
        """
        self.interface.flushInput()
        self._send(0x12, address, parameter, 1)
        response = self._receive()[4:]
        return int.from_bytes(response, "little")

    def _set_frequency(self, frequency: float):
        """
        Set the frequency of the output
        :param frequency: frequency in Hz
        """
        self.set_parameter(0x100, 0x05, round(frequency * 10), 4)
        time.sleep(0.05)
        self.confirm()

    def _set_amplitude(self, amplitude: float, **kwargs):
        """
        Set the amplitude of the output
        :param amplitude: amplitude in V for power output, 100 mV for Headphones
        """
        if "channel" in kwargs and kwargs["channel"] != 1:
            raise NotImplementedError("This function generator does not have multiple channels")

        self.set_parameter(0x100, 0x06, round(amplitude * 1000), 4)
        time.sleep(0.05)
        self.confirm()

    def _set_offset(self, offset: float, **kwargs):
        """
        Set the offset of the output
        :param offset: offset in V
        """
        if "channel" in kwargs and kwargs["channel"] != 1:
            raise NotImplementedError("This function generator does not have multiple channels")

        self.set_parameter(0x100, 0x07, round(offset * 1000), 2)
        time.sleep(0.05)
        self.confirm()

    def _set_output_state(self, state: bool, **kwargs):
        """
        Set the output state of the function generator
        :param state: output state: True - on, False - off
        """
        if "channel" in kwargs and kwargs["channel"] != 1:
            raise NotImplementedError("This function generator does not have multiple channels")

        self.set_parameter(0x100, 0x03, int(not state), 1)

    def get_frequency(self):
        """
        Get the frequency of the output
        :return: frequency in Hz
        """
        return self.get_parameter(0x100, 0x05) / 10

    def get_amplitude(self):
        """
        Get the amplitude of the output
        :return: amplitude in V for power output, 100 mV for Headphones
        """
        return self.get_parameter(0x100, 0x06) / 1000

    class Shape(Enum):
        SINE = 1
        TRIANGLE = 2
        SQUARE = 3
        F_RAMP = 4
        U_Ramp = 5

    def set_shape(self, shape: Shape):
        """
        Set the output shape of the function generator
        :param shape: output shape
        """
        self.set_parameter(0x100, 0x04, shape.value, 1)

    def ramp_setup_f(self, start_freq: float, end_freq: float, step_time: float, step: float, repeat: bool = False):
        """
        Set up the function generator for a frequency ramp
        :param start_freq: start frequency in Hz
        :param end_freq: end frequency in Hz
        :param step_time: time in seconds between steps
        :param step: step size in Hz
        :param repeat: whether to repeat the ramp
        """
        self.set_parameter(0x100, 0x08, round(start_freq * 10), 4)
        time.sleep(0.1)
        self.set_parameter(0x100, 0x09, round(end_freq * 10), 4)
        time.sleep(0.1)
        self.set_parameter(0x100, 0x0a, round(step_time * 1000), 4)
        time.sleep(0.1)
        self.set_parameter(0x100, 0x0b, round(step * 10), 4)
        time.sleep(0.1)
        self.set_parameter(0x100, 0x13, int(repeat), 1)
        time.sleep(0.1)
        self.set_shape(self.Shape.F_RAMP)

    def ramp_setup_v(self, start_volt: float, end_volt: float, step_time: float, step: float, repeat: bool = False):
        """
        Set up the function generator for a voltage ramp
        :param start_volt: start voltage in V
        :param end_volt: end voltage in V
        :param step_time: time in seconds between steps
        :param step: step size in V
        :param repeat: whether to repeat the ramp
        """
        self.set_parameter(0x100, 0x0d, round(start_volt * 1e3), 4)
        time.sleep(0.1)
        self.set_parameter(0x100, 0x0e, round(end_volt * 1e3), 4)
        time.sleep(0.1)
        self.set_parameter(0x100, 0x0f, round(step_time * 1000), 4)
        time.sleep(0.1)
        self.set_parameter(0x100, 0x10, round(step * 1e3), 4)
        time.sleep(0.1)
        self.set_parameter(0x100, 0x14, int(repeat), 1)
        time.sleep(0.1)
        self.set_parameter(0x100, 0x04, 3, 1)

    def ramp_start(self):
        """
        Start the frequency ramp
        """
        self._send_with_ack(0x51, 0x100, 0, 0, RETRIES)

    def ramp_stop(self):
        """
        Stop the frequency ramp
        """
        self._send_with_ack(0x52, 0x100, 0, 0, RETRIES)

    def ramp_duration(self):
        """
        Get the duration of the frequency ramp
        """
        return self.get_parameter(0x100, 0x11) / 1000


if __name__ == "__main__":
    fg = FunctionGenerator_Phywe("/dev/functionGenerator")  # initialize serial interface
    fg.set_configuration(440, 3.5)  # change to an example setup
    fg._set_output_state(True)  # turn power output on
    time.sleep(2)
    fg._set_output_state(False)  # turn power output off
