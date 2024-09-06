import time
import logging
from tabnanny import verbose

import serial
from serial.serialutil import SerialException

START_BYTE = bytearray([0x7D])
STOP_BYTE = bytearray([0x7E])

BAUD_RATE = 921600

RETRIES = 2

logging.basicConfig(
    filename="function_generator.log",
    encoding="utf-8",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
)


class FunctionGenerator:
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

    def __del__(self):
        self.interface.close()

    def _send(self, frame_index, address, data, num_bytes):
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

    def get_measurement(self):
        self.interface.flushInput()
        self._send(0x01, 0x100, 0, 0)
        response = self._receive()[5:]
        return int.from_bytes(response, "little")

    def set_frequency(self, frequency: float):
        """
        Set the frequency of the output
        :param frequency: frequency in Hz
        """
        self.set_parameter(0x100, 0x05, round(frequency * 10), 4)
        time.sleep(0.05)
        self.confirm()

    def set_amplitude(self, amplitude: float):
        """
        Set the amplitude of the output
        :param amplitude: amplitude in V for power output, 100 mV for Headphones
        """
        self.set_parameter(0x100, 0x06, round(amplitude * 1000), 4)
        time.sleep(0.05)
        self.confirm()

    def set_configuration(self, frequency: float, amplitude: float):
        """
        Set the output frequency and amplitude at once
        :param frequency: frequency in Hz
        :param amplitude: amplitude in V for power output, mV for Headphones
        """
        self.interface.flushInput()
        self.set_parameter(0x100, 0x05, round(frequency * 10), 4)
        # print(self._receive().hex())
        time.sleep(0.2)
        self.set_parameter(0x100, 0x06, round(amplitude * 1000), 4)
        # print(self._receive().hex())
        time.sleep(0.2)
        self.confirm()
        # print(self._receive().hex())

    def set_mode(self, mode: int):
        """
        Set the output mode of the function generator
        :param mode: output mode: 0 - power output, 1 - headphones
        """
        self.set_parameter(0x100, 0x03, mode, 1)

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


if __name__ == "__main__":
    fg = FunctionGenerator("COM7")  # initialize serial interface
    fg.set_configuration(440, 3.5)  # change to an example setup
    fg.set_mode(0)  # turn power output on
    time.sleep(2)
    fg.set_mode(1)  # turn power output off
