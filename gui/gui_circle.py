import sys

from PyQt6 import QtWidgets, QtCore, QtGui

from processor.eeg_processor import EEGProcessor


class EEGGui(QtWidgets.QWidget):
    blink_signal = QtCore.pyqtSignal()
    clench_signal = QtCore.pyqtSignal()
    rhythm_signal = QtCore.pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("EEG GUI — Circle Visualizer")
        self.setGeometry(300, 300, 600, 500)

        self.blink_count = 0
        self.clench_count = 0
        self.circle_ratio = 1.0

        self.init_ui()

        self.eeg_processor = None
        self.thread = None
        self.worker = None

        self.blink_signal.connect(self.update_blink)
        self.clench_signal.connect(self.update_clench)
        self.rhythm_signal.connect(self.update_circle)

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Top counters
        top_layout = QtWidgets.QHBoxLayout()
        self.blink_label = QtWidgets.QLabel("🔴 Blink Count: 0")
        self.clench_label = QtWidgets.QLabel("🔵 Clench Count: 0")
        top_layout.addWidget(self.clench_label)
        top_layout.addStretch()
        top_layout.addWidget(self.blink_label)

        # Central visual indicator
        self.circle = CircleWidget()
        self.circle.setMinimumSize(200, 200)

        # Buttons
        self.btn_start = QtWidgets.QPushButton("Start")
        self.btn_stop = QtWidgets.QPushButton("Stop")
        self.btn_stop.setEnabled(False)

        self.btn_start.clicked.connect(self.start_eeg)
        self.btn_stop.clicked.connect(self.stop_eeg)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.btn_start)
        button_layout.addWidget(self.btn_stop)

        layout.addLayout(top_layout)
        layout.addStretch()
        layout.addWidget(self.circle, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        layout.addLayout(button_layout)

    def update_blink(self):
        self.blink_count += 1
        self.blink_label.setText(f"🔴 Blink Count: {self.blink_count}")
        self.circle.flash("red")

    def update_clench(self):
        self.clench_count += 1
        self.clench_label.setText(f"🔵 Clench Count: {self.clench_count}")
        self.circle.flash("blue")

    def update_circle(self, ratio: float):
        self.circle.set_ratio(ratio)

    def on_blink(self, timestamp: float) -> None:
        self.blink_signal.emit()

    def on_clench(self, timestamp: float) -> None:
        self.clench_signal.emit()

    def on_rhythm(self, alpha_power: float, beta_power: float, alpha_beta_ratio: float) -> None:
        self.rhythm_signal.emit(alpha_beta_ratio)

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
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.finished.connect(self.worker.deleteLater)

        self.thread.start()

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

    def stop_eeg(self):
        if self.worker:
            self.worker.stop()

        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)


class CircleWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.radius_ratio = 1.0
        self.color = QtGui.QColor("gray")
        self.flash_timer = QtCore.QTimer()
        self.flash_timer.setInterval(300)
        self.flash_timer.timeout.connect(self.clear_flash)

    def set_ratio(self, ratio: float):
        self.radius_ratio = max(0.1, min(ratio, 3.0))
        self.update()

    def flash(self, color_name: str):
        self.color = QtGui.QColor(color_name)
        self.update()
        self.flash_timer.start()

    def clear_flash(self):
        self.color = QtGui.QColor("gray")
        self.update()
        self.flash_timer.stop()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        center = self.rect().center()

        base_radius = 50
        radius = base_radius * self.radius_ratio

        circle_rect = QtCore.QRectF(
            center.x() - radius,
            center.y() - radius,
            2 * radius,
            2 * radius
        )

        painter.setBrush(self.color)
        painter.setPen(QtGui.QPen(QtCore.Qt.GlobalColor.black, 2))
        painter.drawEllipse(circle_rect)


class EEGWorker(QtCore.QObject):
    finished = QtCore.pyqtSignal()

    def __init__(self, processor: EEGProcessor):
        super().__init__()
        self.processor = processor
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.step)
        self.running = False

    def start(self):
        if self.processor.initialize_stream():
            self.running = True
            self.timer.start()
        else:
            self.finished.emit()

    def step(self):
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
    gui = EEGGui()
    gui.show()
    sys.exit(app.exec())
