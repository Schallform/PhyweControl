import time
from abc import ABC, abstractmethod
from collections.abc import Iterable


class FunctionGenerator_abc(ABC):
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
    def _set_frequency(self, frequency: float, channel: int = 1):
        """
        Set the frequency of the output
        :param frequency: frequency in Hz
        :param channel: output channel, if applicable
        """
        pass

    def set_frequency(self, frequency: float | Iterable[float], channel: int = 1):
        """
        Set the frequency of the output
        :param frequency: frequency in Hz
        :param channel: output channel. This parameter is ignored if frequency is an iterable
        """
        try:
            for i in range(len(frequency)):
                self._set_frequency(frequency[i], channel=i + 1)
        except TypeError:
            self._set_frequency(frequency, channel=channel)

    @abstractmethod
    def _set_amplitude(self, amplitude: float, channel: int = 1):
        """
        Set the amplitude of the output
        :param amplitude: amplitude in V
        :param channel: output channel, if applicable
        """
        pass

    def set_amplitude(self, amplitude: float | Iterable[float], channel: int = 1):
        """
        Set the amplitude of the output
        :param amplitude: amplitude in V
        :param channel: output channel. This parameter is ignored if amplitude is an iterable
        """
        try:
            for i in range(len(amplitude)):
                self._set_amplitude(amplitude[i], i + 1)
        except TypeError:
            self._set_amplitude(amplitude, channel)

    @abstractmethod
    def _set_offset(self, offset: float, channel: int = 1):
        """
        Set the offset of the output
        :param offset: offset in V
        :param channel: output channel, if applicable
        """
        pass

    def set_offset(self, offset: float | Iterable[float], channel: int = 1):
        """
        Set the offset of the output
        :param offset: offset in V
        :param channel: output channel. This parameter is ignored if offset is an iterable
        """
        try:
            for i in range(len(offset)):
                self._set_offset(offset[i], i + 1)
        except TypeError:
            self._set_offset(offset, channel)

    def set_configuration(self, frequency: float | Iterable[float], amplitude: float | Iterable[float],
                          offset: float | Iterable[float] = 0):
        """
        Set the output frequency and amplitude at once
        :param frequency: frequency in Hz
        :param amplitude: amplitude in V
        :param offset: offset in V
        """
        self.set_frequency(frequency)
        self.set_amplitude(amplitude)
        self.set_offset(offset)

    @abstractmethod
    def _set_output_state(self, state: bool, channel: int = 1):
        """
        Set the output state of the function generator
        :param state: whether the output is on
        :param channel: output channel, if applicable
        """
        pass

    def set_output_state(self, state: bool | Iterable[bool], channel: int = 1):
        """
        Set the output state of the function generator
        :param state: whether the output is on
        :param channel: output channel. This parameter is ignored if state is an iterable
        """
        try:
            for i in range(len(state)):
                self._set_output_state(state[i], i + 1)
        except TypeError:
            self._set_output_state(state, channel)

    @abstractmethod
    def ramp_setup_f(self, start_freq: float, end_freq: float, step_time: float, step: float, repeat: bool = False):
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

    def pulse(self, frequency: float | Iterable[float], amplitude: float | Iterable[float], duration: float):
        """
        Set the function generator to a specific configuration for a given duration
        :param frequency: frequency(ies) to set the function generator to
        :param amplitude: amplitude(s) to set the function generator to
        :param duration: duration of the pulse
        """
        try:
            channels = [True] * max(len(frequency), len(amplitude))
        except TypeError:
            channels = [True]
        self.set_configuration(frequency, amplitude)
        self.set_output_state(channels)
        time.sleep(duration)
        self.set_output_state([not c for c in channels])

    def pulse_channel(self, channel: int, duration: float):
        """
        Enable the specified channel for a given time without changing its configuration
        :param channel: the channel to enable
        :param duration: the duration of the pulse
        """
        self.set_output_state(True, channel)
        time.sleep(duration)
        self.set_output_state(False, channel)
