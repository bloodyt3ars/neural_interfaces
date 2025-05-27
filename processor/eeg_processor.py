import time
from typing import Optional

from pylsl import resolve_streams, StreamInlet
from blink.blink_detector import BlinkDetector, BlinkDetectorListener
from jaws.jaw_clench_detector import JawClenchDetector, JawClenchDetectorListener
from rhytm.rhytm_analyzer import RhythmAnalyzer, RhythmAnalyzerListener


class EEGProcessor:
    """
    Главный управляющий класс, получающий данные LSL и выполняющий обработку сигналов.

    :param duration: Время выполнения в секундах. Если None — работает до Ctrl+C
    """

    def __init__(self, duration: Optional[float] = None,
             blink_listener: BlinkDetectorListener = None,
             clench_listener: JawClenchDetectorListener = None,
             rhythm_listener: RhythmAnalyzerListener = None):
        self.__duration = duration
        self.__blink_detector = BlinkDetector()
        self.__jaw_detector = JawClenchDetector()
        self.__rhythm_analyzer = RhythmAnalyzer()
        self.__stream = None

        self.__blink_listener = blink_listener
        self.__jaw_listener = clench_listener
        self.__rhythm_listener = rhythm_listener

    def start(self):
        """
        Запускает основной цикл обработки EEG-сигнала: подключение к LSL-потоку,
        детекция событий и анализ ритмов.
        """
        print("Поиск потока LSL...")
        streams = resolve_streams(wait_time=5)

        if not streams:
            print("Потоков не найдено.")
            return

        self.__stream = StreamInlet(streams[0])
        print("Обработка EEG...")

        start_time = time.time()
        try:
            while True:
                samples, timestamps = self.__stream.pull_chunk()
                if not samples:
                    continue

                self.__blink_detector.detect(samples, timestamps, self.__blink_listener)
                self.__jaw_detector.detect(samples, timestamps, self.__jaw_listener)
                self.__rhythm_analyzer.analyze(samples, self.__rhythm_listener)

                if self.__duration and (time.time() - start_time >= self.__duration):
                    print("Обработка завершена.")
                    break

                time.sleep(0.1)

        except KeyboardInterrupt:
            print("Остановка пользователем.")