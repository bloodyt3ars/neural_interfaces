from abc import ABC, abstractmethod
from collections import deque
from typing import List

from filter.signal_filter import SignalFilter


class JawClenchDetectorListener(ABC):
    """Интерфейс обработчика события сжатия челюсти."""

    @abstractmethod
    def on_clench(self, timestamp: float) -> None:
        """
        Обрабатывает момент сжатия челюсти.

        :param timestamp: Время события в секундах
        """
        pass


class JawClenchDetector:
    """
    Детектор одиночных сжатий челюсти по каналам F3/F4.
    """

    def __init__(self, threshold_min=100, threshold_max=300, debounce_time=0.5, fs=125):
        self.__threshold_min = threshold_min
        self.__threshold_max = threshold_max
        self.__debounce_time = debounce_time
        self.__fs = fs
        self.__last_clench_time = 0
        self.__f3_buffer = deque(maxlen=fs)
        self.__f4_buffer = deque(maxlen=fs)
        self.__filter = SignalFilter(fs=fs)

    def detect(self, samples: List[List[float]], timestamps: List[float], listener: JawClenchDetectorListener):
        """
        Анализирует сигнал и сообщает о сжатии челюсти.

        :param samples: Список сэмплов (массив каналов)
        :param timestamps: Список временных меток
        :param listener: Объект, реализующий интерфейс JawClenchDetectorListener
        """
        for i in range(len(samples)):
            self.__f3_buffer.append(samples[i][3])
            self.__f4_buffer.append(samples[i][4])

            if len(self.__f3_buffer) < self.__fs:
                continue

            f3_val = abs(self.__filter.lowpass_filter(list(self.__f3_buffer))[-1])
            f4_val = abs(self.__filter.lowpass_filter(list(self.__f4_buffer))[-1])

            if self.__threshold_min < f3_val < self.__threshold_max or \
                    self.__threshold_min < f4_val < self.__threshold_max:
                current_time = timestamps[i]
                if current_time - self.__last_clench_time > self.__debounce_time:
                    listener.on_clench(current_time)
                    self.__last_clench_time = current_time
