import ctypes

import psutil

from app.core.proc import run_ps
from app.phases.base import Phase

_PROCESS_QUERY = 0x0400
_PROCESS_SET_QUOTA = 0x0100
_DENYLIST = {"system", "idle", "registry", "memory compression", "smss.exe",
             "csrss.exe", "wininit.exe", "services.exe", "lsass.exe"}


def _working_set_mb():
    return psutil.virtual_memory().available / (1024 * 1024)


class MemoryPhase(Phase):
    id = 3
    icon = "🧠"
    name = "Memoria RAM"
    description = "Recorta working sets y libera memoria inactiva"

    def _trim_processes(self):
        ctx = self.ctx
        trimmed = skipped = 0
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                name = (proc.info["name"] or "").lower()
                if name in _DENYLIST or ctx.dry_run:
                    continue
                handle = ctypes.windll.kernel32.OpenProcess(
                    _PROCESS_SET_QUOTA | _PROCESS_QUERY, False, proc.info["pid"])
                if handle:
                    ctypes.windll.psapi.EmptyWorkingSet(handle)
                    ctypes.windll.kernel32.CloseHandle(handle)
                    trimmed += 1
            except (psutil.Error, OSError):
                skipped += 1
        return trimmed, skipped

    def run(self):
        ctx = self.ctx
        before = _working_set_mb()
        ctx.info(f"Memoria disponible antes: {before:.0f} MB")

        trimmed, _ = self._trim_processes()
        if not ctx.dry_run:
            ctx.changed(f"Working sets recortados en {trimmed} procesos")
            after = _working_set_mb()
            ctx.ok(f"Memoria disponible despues: {after:.0f} MB "
                   f"({after - before:+.0f} MB)")
        else:
            ctx.ok(f"Simulacion: {len(psutil.pids())} procesos activos "
                   "analizados (sin cambios)")

                                                               
        rc, out = run_ps("(Get-MMAgent).MemoryCompression", timeout=60)
        if rc == 0 and out.strip():
            estado = "activada" if out.strip() == "True" else "desactivada"
            ctx.info(f"Compresion de memoria: {estado} (gestionada por Windows)")
