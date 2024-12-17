import time
from abc import ABC, abstractmethod


class FunctionGenerator(ABC):
    """
    Abstract function generator class
    """
    @abstractmethod
    def release(self):
        """
        Release all communication to the function generator
        """
        pass

    @abstractmethod
    def set_frequency(self, frequency: float, channel: int = 1):
        """
        Set the frequency of the output
        :param frequency: frequency in Hz
        :param channel: output channel, if applicable
        """
        pass

    @abstractmethod
    def set_amplitude(self, amplitude: float, channel: int = 1):
        """
        Set the amplitude of the output
        :param amplitude: amplitude in V
        :param channel: output channel, if applicable
        """
        pass

    @abstractmethod
    def set_offset(self, offset: float, channel: int = 1):
        """
        Set the offset of the output
        :param offset: offset in V
        :param channel: output channel, if applicable
        """
        pass

    def set_configuration(self, frequency: float, amplitude: float, offset: float = 0, **kwargs):
        """
        Set the output frequency and amplitude at once
        :param frequency: frequency in Hz
        :param amplitude: amplitude in V
        :param offset: offset in V
        """
        self.set_frequency(frequency, **kwargs)
        self.set_amplitude(amplitude, **kwargs)
        self.set_offset(offset, **kwargs)

    @abstractmethod
    def set_output_state(self, state: bool, channel: int = 1):
        """
        Set the output state of the function generator
        :param state: whether the output is on
        :param channel: output channel, if applicable
        """
        pass

    @abstractmethod
    def ramp_setup(self, start_freq: float, end_freq: float, step_time: float, step: float, repeat: bool = False):
        """
        Set up the function generator for a frequency ramp
        :param start_freq: start frequency in Hz
        :param end_freq: end frequency in Hz
        :param step_time: time in seconds between steps
        :param step: step size in Hz
        :param repeat: whether to repeat the ramp
        """
        pass

    @abstractmethod
    def ramp_start(self):
        """
        Start the frequency ramp
        """
        pass

    @abstractmethod
    def ramp_stop(self):
        """
        Stop the frequency ramp
        """
        pass

    @abstractmethod
    def ramp_duration(self):
        """
        Get the duration of the frequency ramp
        """
        pass

    def pulse(self, frequency1: float, amplitude1: float, duration: float, frequency2: float = None, amplitude2: float = None):
        """
        Set the function generator to a specific configuration for a given duration
        :param frequency1: frequency to set channel 1 of the function generator to
        :param amplitude1: amplitude to set channel 2 of the function generator to
        :param duration: duration of the pulse
        """
        secondChannel = frequency2 is not None and amplitude2 is not None
        self.set_configuration(frequency1, amplitude1, channel=1)
        if secondChannel:
            self.set_configuration(frequency2, amplitude2, channel=2)
        self.set_output_state(True, channel=1)
        if secondChannel:
            self.set_output_state(True, channel=2)
        time.sleep(duration)
        self.set_output_state(False, channel=1)
        if secondChannel:
            self.set_output_state(False, channel=2)
