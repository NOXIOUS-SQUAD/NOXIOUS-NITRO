
import traceback

from PySide6.QtCore import QThread, Signal

from app.core.backup import BackupManager
from app.core.logger import create_logger
from app.core.restore import create_restore_point
from app.phases import PHASES
from app.phases.base import PhaseContext


class OptimizeWorker(QThread):
    log = Signal(str, str)                           
    step = Signal(int, int, str)                                    
    finished_all = Signal(bool)                    

    def __init__(self, selected_ids, make_restore=True, dry_run=False,
                 parent=None):
        super().__init__(parent)
        self._selected = selected_ids
        self._make_restore = make_restore
        self._dry_run = dry_run
        self._cancel = False
        self.log_path = None

    def cancel(self):
        self._cancel = True

    def _log(self, msg, level="info"):
        self.log.emit(msg, level)

    def run(self):
        logger, path = create_logger()
        self.log_path = path
        ctx = PhaseContext(self._emit, BackupManager(), dry_run=self._dry_run)

        if self._dry_run:
            self._emit("=== MODO SIMULACION: ningun cambio se aplicara ===",
                       "warn")

                                                                          
        if self._make_restore and not self._dry_run:
            self.step.emit(0, len(self._selected) + 1,
                           "FASE 0 - Punto de restauracion")
            try:
                create_restore_point(self._emit)
            except Exception:
                self._emit("Fallo al crear el punto de restauracion:\n"
                           + traceback.format_exc(limit=2), "err")
                self._emit("Se DETIENE la optimizacion por seguridad.", "err")
                self.finished_all.emit(False)
                return
        elif not self._dry_run:
            self._emit("Punto de restauracion omitido a peticion del usuario",
                       "warn")

                                                                            
        phases = [p for p in PHASES if p.id in self._selected]
        total = len(phases) + (1 if self._make_restore and not self._dry_run
                               else 0)
        offset = total - len(phases)
        ok = True
        for i, cls in enumerate(phases, start=1):
            if self._cancel:
                self._emit("Operacion cancelada por el usuario.", "warn")
                break
            self.step.emit(offset + i - 1, total, f"FASE {cls.id} - {cls.name}")
            self._emit(f"\n{'=' * 22} FASE {cls.id}: {cls.name} {'=' * 22}")
            try:
                cls(ctx).run()
            except Exception:
                ok = False
                self._emit(f"Error inesperado en la fase {cls.id}:\n"
                           + traceback.format_exc(limit=3), "err")

        saved = ctx.backup.save()
        if saved:
            self._emit(f"Backup de cambios guardado en: {saved}", "info")
        self._emit("=== PROCESO TERMINADO ===", "ok" if ok else "warn")
        self.finished_all.emit(ok)

    def _emit(self, msg, level="info"):
        for line in str(msg).splitlines():
            self.log.emit(line, level)
