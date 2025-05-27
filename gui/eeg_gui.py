import sys

import pyqtgraph as pg
from PyQt6 import QtWidgets, QtCore

from processor.eeg_processor import EEGProcessor


class EEGGui(QtWidgets.QWidget):
    """
    Графический интерфейс для отображения EEG активности, событий моргания и сжатия челюсти, а также альфа/бета ритмов.
    """
    blink_signal = QtCore.pyqtSignal()
    clench_signal = QtCore.pyqtSignal()
    rhythm_signal = QtCore.pyqtSignal(float, float, float)

    def __init__(self):
        super().__init__()
        self.blink_count = 0
        self.clench_count = 0
        self.setWindowTitle("EEG Monitor")
        self.setGeometry(200, 200, 800, 600)

        self.init_ui()
        self.eeg_processor = None
        self.worker = None
        self.thread = None

        self.blink_signal.connect(self.update_blink_ui)
        self.clench_signal.connect(self.update_clench_ui)
        self.rhythm_signal.connect(self.update_graphs)

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        self.plot_alpha = pg.PlotWidget(title="Alpha Power")
        self.plot_beta = pg.PlotWidget(title="Beta Power")
        self.plot_ratio = pg.PlotWidget(title="Alpha/Beta Ratio")

        self.alpha_curve = self.plot_alpha.plot(pen='g')
        self.beta_curve = self.plot_beta.plot(pen='b')
        self.ratio_curve = self.plot_ratio.plot(pen='r')

        self.alpha_data = []
        self.beta_data = []
        self.ratio_data = []
        self.x = []

        graph_layout = QtWidgets.QVBoxLayout()
        graph_layout.addWidget(self.plot_alpha)
        graph_layout.addWidget(self.plot_beta)
        graph_layout.addWidget(self.plot_ratio)

        left_layout = QtWidgets.QVBoxLayout()
        self.blink_label = QtWidgets.QLabel("🔴 Blink Count: 0")
        self.clench_label = QtWidgets.QLabel("🔵 Clench Count: 0")

        self.blink_indicator = QtWidgets.QLabel()
        self.clench_indicator = QtWidgets.QLabel()
        self.set_led(self.blink_indicator, "gray")
        self.set_led(self.clench_indicator, "gray")

        left_layout.addWidget(self.blink_label)
        left_layout.addWidget(self.blink_indicator)
        left_layout.addWidget(self.clench_label)
        left_layout.addWidget(self.clench_indicator)

        center_layout = QtWidgets.QHBoxLayout()
        center_layout.addLayout(left_layout)
        center_layout.addLayout(graph_layout)

        layout.addLayout(center_layout)

        self.btn_start = QtWidgets.QPushButton("Старт")
        self.btn_stop = QtWidgets.QPushButton("Стоп")
        self.btn_stop.setEnabled(False)

        self.btn_start.clicked.connect(self.start_eeg)
        self.btn_stop.clicked.connect(self.stop_eeg)

        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        layout.addLayout(btn_layout)

    def set_led(self, label: QtWidgets.QLabel, color: str):
        label.setFixedSize(20, 20)
        label.setStyleSheet(f"background-color: {color}; border-radius: 10px;")

    def update_blink_ui(self):
        self.blink_count += 1
        self.blink_label.setText(f"🔴 Blink Count: {self.blink_count}")
        self.set_led(self.blink_indicator, "red")
        QtCore.QTimer.singleShot(300, lambda: self.set_led(self.blink_indicator, "gray"))

    def update_clench_ui(self):
        self.clench_count += 1
        self.clench_label.setText(f"🔵 Clench Count: {self.clench_count}")
        self.set_led(self.clench_indicator, "blue")
        QtCore.QTimer.singleShot(300, lambda: self.set_led(self.clench_indicator, "gray"))

    def update_graphs(self, alpha: float, beta: float, ratio: float):
        self.alpha_data.append(alpha)
        self.beta_data.append(beta)
        self.ratio_data.append(ratio)
        self.x.append(len(self.x))

        self.alpha_curve.setData(self.x, self.alpha_data)
        self.beta_curve.setData(self.x, self.beta_data)
        self.ratio_curve.setData(self.x, self.ratio_data)

    def on_blink(self, timestamp: float) -> None:
        self.blink_signal.emit()

    def on_clench(self, timestamp: float) -> None:
        self.clench_signal.emit()

    def on_rhythm(self, alpha_power: float, beta_power: float, alpha_beta_ratio: float) -> None:
        self.rhythm_signal.emit(alpha_power, beta_power, alpha_beta_ratio)

    def start_eeg(self):
        self.eeg_processor = EEGProcessor(
            duration=None,
            blink_listener=self,
            clench_listener=self,
            rhythm_listener=self
        )

        self.thread = QtCore.QThread()
        self.worker = EEGWorker(self.eeg_processor)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.start)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

    def stop_eeg(self):
        if self.worker:
            self.worker.stop()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)


class EEGWorker(QtCore.QObject):
    """
    Запускает EEGProcessor в отдельном потоке. Работает до сигнала stop().
    """
    finished = QtCore.pyqtSignal()

    def __init__(self, processor: EEGProcessor):
        super().__init__()
        self.processor = processor
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.process_step)
        self.running = False

    def start(self):
        if self.processor.initialize_stream():
            self.running = True
            self.timer.start()
        else:
            self.finished.emit()

    def process_step(self):
        if not self.running:
            self.timer.stop()
            self.finished.emit()
            return

        if not self.processor.step():
            self.stop()

    def stop(self):
        self.running = False
        self.timer.stop()
        self.finished.emit()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = EEGGui()
    window.show()
    sys.exit(app.exec())
