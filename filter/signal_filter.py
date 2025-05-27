from typing import List

import numpy as np
from scipy.signal import butter, filtfilt


class SignalFilter:
    """
    Низкочастотный фильтр для сглаживания EEG-сигнала.

    :param cutoff: Частота среза фильтра в Гц (по умолчанию 10)
    :param fs: Частота дискретизации в Гц (по умолчанию 125)
    :param order: Порядок фильтра (по умолчанию 4)
    """

    def __init__(self, cutoff=10, fs=125, order=4):
        self.__cutoff = cutoff
        self.__fs = fs
        self.__order = order

    def __butter_lowpass(self):
        """
        Создаёт параметры Butterworth-фильтра для заданных настроек.
        :return: коэффициенты (b, a)
        """
        nyquist = 0.5 * self.__fs
        normal_cutoff = self.__cutoff / nyquist
        b, a = butter(self.__order, normal_cutoff, btype='low', analog=False)
        return b, a

    def lowpass_filter(self, data: List[float]) -> np.ndarray:
        """
        Применяет низкочастотный фильтр к данным.

        :param data: Список отсчётов сигнала
        :return: Отфильтрованный сигнал как массив numpy
        """
        b, a = self.__butter_lowpass()
        return filtfilt(b, a, data)
