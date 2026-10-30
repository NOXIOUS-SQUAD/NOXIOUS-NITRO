from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QGraphicsDropShadowEffect, QLabel, QProgressBar,
                               QPushButton, QVBoxLayout, QWidget)

from app.config import COLOR_ACCENT


class GlowButton(QPushButton):

    def __init__(self, text="", parent=None, pulse=False):
        super().__init__(text, parent)
        self._glow = QGraphicsDropShadowEffect(self)
        self._glow.setColor(QColor(COLOR_ACCENT))
        self._glow.setOffset(0, 0)
        self._glow.setBlurRadius(10)
        self.setGraphicsEffect(self._glow)
        self.setCursor(Qt.PointingHandCursor)

        self._anim = QPropertyAnimation(self._glow, b"blurRadius", self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

        self._pulse = None
        if pulse:
            self._pulse = QPropertyAnimation(self._glow, b"blurRadius", self)
            self._pulse.setKeyValues([(0.0, 16.0), (0.5, 40.0), (1.0, 16.0)])
            self._pulse.setDuration(1600)
            self._pulse.setEasingCurve(QEasingCurve.InOutSine)
            self._pulse.setLoopCount(-1)
            self._pulse.start()

    def enterEvent(self, event):
        if self._pulse is not None:
            self._pulse.stop()
        self._animate_to(46)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._pulse is not None:
            self._pulse.start()
        else:
            self._animate_to(10)
        super().leaveEvent(event)

    def _animate_to(self, radius):
        self._anim.stop()
        self._anim.setStartValue(self._glow.blurRadius())
        self._anim.setEndValue(radius)
        self._anim.start()


class StatCard(QWidget):

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(3)

        self.name = QLabel(title.upper())
        self.name.setObjectName("statName")
        self.value = QLabel("--")
        self.value.setObjectName("statValue")
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(6)

        layout.addWidget(self.name)
        layout.addWidget(self.value)
        layout.addWidget(self.bar)

    def set_value(self, text, percent=None):
        self.value.setText(text)
        if percent is None:
            self.bar.hide()
        else:
            self.bar.show()
            self.bar.setValue(max(0, min(100, int(percent))))

    def set_color(self, color):
        self.value.setStyleSheet(f"color: {color};")
