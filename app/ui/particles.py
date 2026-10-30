
import math
import random

from PySide6.QtCore import Qt, QTimer, QRect
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import QWidget

_PARTICLES = 400
_FADE_ALPHA = 26                                      
_FPS_MS = 16                       


class ParticleField(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._buffer = None
        self._parts = []
        self._t = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(_FPS_MS)

                                                                            
    def resizeEvent(self, event):
        w, h = max(self.width(), 2), max(self.height(), 2)
        self._buffer = QImage(w, h, QImage.Format_ARGB32)
        self._buffer.fill(QColor(13, 13, 13))
        self._seed()
        super().resizeEvent(event)

    def _seed(self):
        w, h = self.width(), self.height()
        while len(self._parts) < _PARTICLES:
            self._parts.append([
                random.uniform(0, max(w, 1)),          
                random.uniform(0, max(h, 1)),          
                random.uniform(0.4, 1.6),                           
                random.uniform(0.9, 1.9),                   
                random.uniform(60, 200),                         
            ])
        del self._parts[_PARTICLES:]

                                                                             
    def _tick(self):
        if self._buffer is None or not self.isVisible():
            return
        self._t += _FPS_MS / 1000.0
        t = self._t
        w, h = self.width(), self.height()

        painter = QPainter(self._buffer)
        painter.setRenderHint(QPainter.Antialiasing, False)
                                                                      
        painter.fillRect(QRect(0, 0, w, h), QColor(13, 13, 13, _FADE_ALPHA))

        for p in self._parts:
            x, y, speed, size, bright = p
                                                  
            angle = (math.sin(x * 0.0019 + t * 0.45)
                     + math.cos(y * 0.0016 - t * 0.35)
                     + math.sin((x + y) * 0.0007 + t * 0.2)) * math.pi * 0.66
            nx = x + math.cos(angle) * speed * 2.4
            ny = y + math.sin(angle) * speed * 2.4

                                           
            if nx < 0 or nx >= w or ny < 0 or ny >= h:
                nx, ny = random.uniform(0, w - 1), random.uniform(0, h - 1)
                p[0], p[1] = nx, ny
                continue

            alpha = int((0.55 + 0.45 * math.sin(t * 1.7 + x * 0.02))
                        * min(bright, 255))
            pen = QPen(QColor(0, 255, 0, alpha))
            pen.setWidthF(size)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.drawLine(int(x), int(y), int(nx), int(ny))
            p[0], p[1] = nx, ny

        painter.end()
        self.update()

    def paintEvent(self, event):
        if self._buffer is not None:
            QPainter(self).drawImage(0, 0, self._buffer)
