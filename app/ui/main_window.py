
import html
import os
import subprocess

from PySide6.QtCore import Qt, QThread, QTimer, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QCheckBox, QHBoxLayout, QLabel,
                               QListWidget, QListWidgetItem, QMessageBox,
                               QProgressBar, QPushButton, QStackedWidget,
                               QTextEdit, QVBoxLayout, QWidget, QApplication)

PAGE_HOME, PAGE_RUN = 0, 1

from app.config import (APP_NAME, APP_VERSION, COLOR_ACCENT, COLOR_ERROR,
                        COLOR_TEXT_DIM, COLOR_WARN, DISCORD_URL)
from app.core import admin, sysinfo
from app.core.backup import apply_rollback, latest_backup
from app.phases import PHASES
from app.ui.particles import ParticleField
from app.ui.widgets import GlowButton, StatCard
from app.ui.worker import OptimizeWorker

_LEVEL_COLOR = {"info": "#d6ffd6", "ok": COLOR_ACCENT,
                "warn": COLOR_WARN, "err": COLOR_ERROR}


class RollbackWorker(QThread):
    log = Signal(str, str)

    def run(self):
        path = latest_backup()
        if not path:
            self.log.emit("No hay ningun backup para revertir.", "warn")
            return
        self.log.emit(f"Revirtiendo desde {os.path.basename(path)}...", "info")
        ok, err = apply_rollback(path, lambda m, l="info": self.log.emit(m, l))
        self.log.emit(f"Rollback terminado: {ok} cambios revertidos, "
                      f"{err} errores", "ok" if err == 0 else "warn")


class _TitleBar(QWidget):

    HEIGHT = 38

    def __init__(self, window):
        super().__init__(window)
        self.setObjectName("titleBar")
        self.setFixedHeight(self.HEIGHT)
        self._drag_pos = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(4)
        layout.addStretch()

        self.btn_min = QPushButton("–")
        self.btn_min.setObjectName("titleBtn")
        self.btn_min.setFixedSize(42, 26)
        self.btn_min.setCursor(Qt.PointingHandCursor)
        self.btn_min.setToolTip("Minimizar")
        self.btn_min.clicked.connect(window.showMinimized)
        layout.addWidget(self.btn_min)

        self.btn_close = QPushButton("✕")
        self.btn_close.setObjectName("titleBtn")
        self.btn_close.setFixedSize(42, 26)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setToolTip("Cerrar")
        self.btn_close.clicked.connect(window.close)
        layout.addWidget(self.btn_close)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = (event.globalPosition().toPoint()
                              - self.window().frameGeometry().topLeft())
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.LeftButton:
            self.window().move(event.globalPosition().toPoint()
                               - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint
                            | Qt.WindowMinimizeButtonHint)
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1024, 680)
        self.resize(1200, 780)

        self._particles = ParticleField(self)
        self._titlebar = _TitleBar(self)
        self._stack = QStackedWidget(self)
        self._worker = None
        self._rollback = None

        self._build_select_page()
        self._build_run_page()
        self._stack.setCurrentIndex(PAGE_HOME)
        self._center()

        self._stats_timer = QTimer(self)
        self._stats_timer.timeout.connect(self._refresh_stats)
        self._stats_timer.start(1000)
        sysinfo.snapshot()

    def _center(self):
        screen = QApplication.primaryScreen().availableGeometry()
        geo = self.geometry()
        geo.moveCenter(screen.center())
        self.move(geo.topLeft())

    def _build_select_page(self):
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(26, 20, 26, 14)

        header = QHBoxLayout()
        left = QVBoxLayout()
        title = QLabel("NOXIOUS NITRO")
        title.setObjectName("title")
        info = sysinfo.static_info()
        subtitle = QLabel(f"v{APP_VERSION}  ·  {info['os']}  ·  {info['cpu']}  ·  "
                          f"{info['ram_gb']} GB RAM")
        subtitle.setObjectName("subtitle")
        left.addWidget(title)
        left.addWidget(subtitle)
        header.addLayout(left)
        header.addStretch()

        badge = QLabel("DEV | NSCP12")
        badge.setObjectName("badgeOk")
        header.addWidget(badge)
        if not admin.is_admin():
            elevate = GlowButton("Elevar a administrador")
            elevate.clicked.connect(self._elevate)
            header.addWidget(elevate)
        root.addLayout(header)
        root.addSpacing(10)

        cards = QHBoxLayout()
        cards.setSpacing(10)
        self.card_cpu = StatCard("CPU")
        self.card_ram = StatCard("RAM")
        self.card_disk = StatCard("Disco")
        self.card_uptime = StatCard("Tiempo activo")
        for c in (self.card_cpu, self.card_ram, self.card_disk,
                  self.card_uptime):
            cards.addWidget(c)
        root.addLayout(cards)
        root.addSpacing(10)

        body = QHBoxLayout()
        body.setSpacing(12)

        self.phase_list = QListWidget()
        for cls in PHASES:
            item = QListWidgetItem(
                f"{cls.icon}  Fase {cls.id:02d}  ·  {cls.name}")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            item.setData(Qt.UserRole, cls.id)
            self.phase_list.addItem(item)
        body.addWidget(self.phase_list, stretch=3)

        actions = QWidget()
        actions.setObjectName("panel")
        panel = QVBoxLayout(actions)
        panel.setContentsMargins(18, 18, 18, 18)
        panel.setSpacing(12)

        lbl = QLabel("CONFIGURACION DE LA EJECUCION")
        lbl.setObjectName("phaseLabel")
        panel.addWidget(lbl)

        self.chk_restore = QCheckBox("ACTIVAR PUNTO DE RESTAURACION")
        self.chk_restore.setChecked(True)
        panel.addWidget(self.chk_restore)

        hint = QLabel(" En caso de tener una falla precione revertir cambios")
        hint.setObjectName("footer")
        hint.setWordWrap(True)
        panel.addWidget(hint)
        panel.addStretch()

        self.btn_start = GlowButton("INICIAR OPTIMIZACION", pulse=True)
        self.btn_start.setObjectName("startButton")
        self.btn_start.clicked.connect(self._start)
        panel.addWidget(self.btn_start)

        self.btn_rollback = GlowButton("Revertir ultimos cambios")
        self.btn_rollback.setEnabled(latest_backup() is not None)
        self.btn_rollback.clicked.connect(self._do_rollback)
        panel.addWidget(self.btn_rollback)

        self.btn_discord = GlowButton("Discord")
        self.btn_discord.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(DISCORD_URL)))
        panel.addWidget(self.btn_discord)

        body.addWidget(actions, stretch=1)
        root.addLayout(body, stretch=1)

        footer = QLabel("NOXIOUS SQUAD | @ COPYRIGHT 2026")
        footer.setObjectName("footer")
        root.addWidget(footer)

        self._stack.addWidget(page)

    def _build_run_page(self):
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(26, 22, 26, 20)
        root.setSpacing(12)

        self.lbl_phase = QLabel("Preparando...")
        self.lbl_phase.setObjectName("phaseLabel")
        self.progress = QProgressBar()
        self.progress.setTextVisible(True)
        root.addWidget(self.lbl_phase)
        root.addWidget(self.progress)

        self.log_view = QTextEdit()
        self.log_view.setObjectName("logView")
        self.log_view.setReadOnly(True)
        root.addWidget(self.log_view, stretch=1)

        buttons = QHBoxLayout()
        self.btn_cancel = GlowButton("Cancelar")
        self.btn_cancel.clicked.connect(self._cancel)
        self.btn_back = GlowButton("Volver al inicio")
        self.btn_back.clicked.connect(
            lambda: self._stack.setCurrentIndex(PAGE_HOME))
        self.btn_back.hide()
        self.btn_logs = GlowButton("Abrir carpeta de logs")
        self.btn_logs.clicked.connect(self._open_logs)
        self.btn_logs.hide()
        self.btn_exit = GlowButton("Salir")
        self.btn_exit.clicked.connect(QApplication.instance().quit)
        self.btn_exit.hide()
        for b in (self.btn_cancel, self.btn_back, self.btn_logs, self.btn_exit):
            buttons.addWidget(b)
        root.addLayout(buttons)

        self._stack.addWidget(page)

    def resizeEvent(self, event):
        w, h = self.width(), self.height()
        self._particles.setGeometry(0, 0, w, h)
        self._titlebar.setGeometry(0, 0, w, _TitleBar.HEIGHT)
        self._stack.setGeometry(0, _TitleBar.HEIGHT, w, h - _TitleBar.HEIGHT)
        super().resizeEvent(event)

    def _refresh_stats(self):
        s = sysinfo.snapshot()
        self.card_cpu.set_value(f"{s['cpu']:.0f}%", s["cpu"])
        self.card_ram.set_value(f"{s['ram']:.0f}%", s["ram"])
        self.card_disk.set_value(f"{s['disk_kbs'] / 1024:.1f} MB/s",
                                 min(s["disk_kbs"] / 1024 / 20 * 100, 100))
        self.card_uptime.set_value(sysinfo.fmt_uptime(s["uptime"]))

    def _selected_phases(self):
        return [self.phase_list.item(i).data(Qt.UserRole)
                for i in range(self.phase_list.count())
                if self.phase_list.item(i).checkState() == Qt.Checked]

    def _elevate(self):
        if admin.relaunch_as_admin():
            QApplication.instance().quit()
        else:
            QMessageBox.warning(self, APP_NAME,
                                "No se pudo relanzar como administrador.")

    def _start(self):
        selected = self._selected_phases()
        restore = self.chk_restore.isChecked()
        if not selected:
            QMessageBox.information(self, APP_NAME,
                                    "Selecciona al menos una fase.")
            return
        if not admin.is_admin():
            box = QMessageBox(self)
            box.setWindowTitle(APP_NAME)
            box.setText("Para optimizar el sistema se necesitan privilegios "
                        "de administrador.\n\nPulsa 'Elevar' para reiniciar "
                        "la aplicacion con privilegios.")
            btn_elev = box.addButton("Elevar", QMessageBox.AcceptRole)
            box.addButton("Cancelar", QMessageBox.RejectRole)
            box.exec()
            if box.clickedButton() is btn_elev:
                self._elevate()
            return

        self._stack.setCurrentIndex(PAGE_RUN)
        self.log_view.clear()
        self.progress.setValue(0)
        self.btn_cancel.show()
        for b in (self.btn_back, self.btn_logs, self.btn_exit):
            b.hide()

        self._worker = OptimizeWorker(selected, make_restore=restore)
        self._worker.log.connect(self._append_log)
        self._worker.step.connect(self._on_step)
        self._worker.finished_all.connect(self._on_finished)
        self._worker.start()

    def _cancel(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self.btn_cancel.setEnabled(False)

    def _append_log(self, msg, level):
        color = _LEVEL_COLOR.get(level, "#d6ffd6")
        self.log_view.append(
            f'<span style="color:{color}">{html.escape(msg)}</span>')
        sb = self.log_view.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _on_step(self, idx, total, name):
        self.progress.setMaximum(total)
        self.progress.setValue(idx)
        self.lbl_phase.setText(name)

    def _on_finished(self, ok):
        self.progress.setValue(self.progress.maximum())
        self.lbl_phase.setText("PROCESO TERMINADO" if ok
                               else "TERMINADO CON ERRORES (revisa el log)")
        self.btn_cancel.hide()
        for b in (self.btn_back, self.btn_logs, self.btn_exit):
            b.show()
        self.btn_rollback.setEnabled(latest_backup() is not None)

    def _do_rollback(self):
        if self._rollback and self._rollback.isRunning():
            return
        if QMessageBox.question(
                self, APP_NAME,
                "Se revertiran los cambios del ultimo backup "
                "(servicios, registro, DNS, energia...).\n\nContinuar?"
        ) != QMessageBox.Yes:
            return
        self._stack.setCurrentIndex(PAGE_RUN)
        self.log_view.clear()
        self.lbl_phase.setText("REVERTIENDO CAMBIOS...")
        self.progress.setMaximum(1)
        self.progress.setValue(0)
        self._rollback = RollbackWorker(self)
        self._rollback.log.connect(self._append_log)
        self._rollback.finished.connect(lambda: self._on_finished(True))
        self.btn_cancel.hide()
        self._rollback.start()

    def _open_logs(self):
        if self._worker and self._worker.log_path:
            folder = os.path.dirname(self._worker.log_path)
            if os.path.isdir(folder):
                subprocess.Popen(["explorer", folder])

    def closeEvent(self, event):
        for w in (self._worker, self._rollback):
            if w and w.isRunning():
                if hasattr(w, "cancel"):
                    w.cancel()
                w.wait(2000)
        event.accept()
