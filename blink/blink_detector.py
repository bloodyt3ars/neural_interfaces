from abc import ABC, abstractmethod
from collections import deque
from typing import List

from filter.signal_filter import SignalFilter


class BlinkDetectorListener(ABC):
    """Интерфейс обработчика события моргания."""

    @abstractmethod
    def on_blink(self, timestamp: float) -> None:
        """
        Обрабатывает момент моргания.

        :param timestamp: Время события в секундах
        """
        pass


class BlinkDetector:
    """
    Детектор одиночных морганий по каналам F3/F4.
    """

    def __init__(self, threshold_min=50, threshold_max=150, min_interval=0.3, fs=125):
        self.__threshold_min = threshold_min
        self.__threshold_max = threshold_max
        self.__min_interval = min_interval
        self.__fs = fs
        self.__last_blink_time = 0
        self.__f3_buffer = deque(maxlen=fs)
        self.__f4_buffer = deque(maxlen=fs)
        self.__filter = SignalFilter(fs=fs)

    def detect(self, samples: List[List[float]], timestamps: List[float], listener: BlinkDetectorListener):
        """
        Анализирует поток данных и сообщает о моргании при обнаружении.

        :param samples: Список сэмплов (массив каналов)
        :param timestamps: Список временных меток
        :param listener: Объект, реализующий интерфейс BlinkDetectorListener
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
                if current_time - self.__last_blink_time > self.__min_interval:
                    listener.on_blink(current_time)
                    self.__last_blink_time = current_time
