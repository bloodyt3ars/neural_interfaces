from blink.blink_detector import BlinkDetectorListener
from jaws.jaw_clench_detector import JawClenchDetectorListener
from processor.eeg_processor import EEGProcessor
from rhytm.rhytm_analyzer import RhythmAnalyzerListener


class PrintBlinkListener(BlinkDetectorListener):
    def on_blink(self, timestamp: float) -> None:
        print(f"[BLINK] {timestamp:.2f} sec")


class PrintJawClenchListener(JawClenchDetectorListener):
    def on_clench(self, timestamp: float) -> None:
        print(f"[CLENCH] {timestamp:.2f} sec")


class PrintRhythmListener(RhythmAnalyzerListener):
    def on_rhythm(self, alpha_power: float, beta_power: float, alpha_beta_ratio: float) -> None:
        print(f"[RHYTHM] α: {alpha_power:.2f}, β: {beta_power:.2f}, α/β: {alpha_beta_ratio:.2f}")


def main():
    blink_listener = PrintBlinkListener()
    jaw_clench_listener = PrintJawClenchListener()
    rhythm_listener = PrintRhythmListener()
    eeg = EEGProcessor(blink_listener=blink_listener, clench_listener=jaw_clench_listener,
                       rhythm_listener=rhythm_listener)
    eeg.initialize_stream()
    try:
        while eeg.step():
            pass
    except KeyboardInterrupt:
        print("Остановка пользователем.")


if __name__ == '__main__':
    main()
