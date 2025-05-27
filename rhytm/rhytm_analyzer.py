from abc import ABC, abstractmethod
from collections import deque

import numpy as np
from scipy.fft import rfft, rfftfreq
from scipy.signal import windows


class RhythmAnalyzerListener(ABC):
    """Интерфейс для получения данных о ритмах."""

    @abstractmethod
    def on_rhythm(self, alpha_power: float, beta_power: float, alpha_beta_ratio: float) -> None:
        """
        Вызывается при каждом анализе спектра сигнала.

        :param alpha_power: Мощность в альфа-диапазоне (8–13 Гц)
        :param beta_power: Мощность в бета-диапазоне (14–30 Гц)
        :param alpha_beta_ratio: Отношение альфа/бета мощностей
        """
        pass


class _Rhythm:
    def __init__(self, name: str, start_freq: float, end_freq: float):
        self.name = name
        self.start = start_freq
        self.end = end_freq


class RhythmAnalyzer:
    """
    Класс для анализа спектра сигнала и извлечения мощности альфа и бета ритмов.
    """

    def __init__(self, fs: int = 125, fft_len: int = 4096):
        self.__fs = fs
        self.__fft_len = fft_len
        self.__buffer = deque(maxlen=fs * 2)
        self.__alpha = _Rhythm("alpha", 8, 13)
        self.__beta = _Rhythm("beta", 14, 30)

    def analyze(self, samples: list[list[float]], listener: RhythmAnalyzerListener):
        """
        Выполняет спектральный анализ и вызывает слушатель с результатами.

        :param samples: Список сэмплов (массив каналов)
        :param listener: Объект, реализующий интерфейс RhythmAnalyzerListener
        """
        for s in samples:
            self.__buffer.append(s[3])

        if len(self.__buffer) < self.__fs:
            return

        y = np.array(self.__buffer)
        y = y * windows.hamming(len(y))
        yf = np.abs(rfft(y, n=self.__fft_len))
        xf = rfftfreq(self.__fft_len, d=1 / self.__fs)

        alpha_power = self.__sum_power(xf, yf, self.__alpha)
        beta_power = self.__sum_power(xf, yf, self.__beta)
        ratio = alpha_power / (beta_power + 1e-8)

        listener.on_rhythm(alpha_power, beta_power, ratio)

    def __sum_power(self, x: np.ndarray, y: np.ndarray, rhythm: _Rhythm) -> float:
        """
        Суммирует мощность в заданном диапазоне частот.

        :param x: Частотный вектор
        :param y: Спектр сигнала
        :param rhythm: Объект ритма с диапазоном частот
        :return: Суммарная мощность в этом диапазоне
        """
        return float(np.sum([v for f, v in zip(x, y) if rhythm.start <= f <= rhythm.end]))
