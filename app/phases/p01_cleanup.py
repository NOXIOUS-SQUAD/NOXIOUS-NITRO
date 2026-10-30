import os
import time

from app.core.proc import run_cmd, run_ps
from app.phases.base import Phase

_MB = 1024 * 1024


def _scan(path, pred=None):
    total, count = 0, 0
    for root, dirs, files in os.walk(path, onerror=lambda e: None):
        dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root, d))]
        for f in files:
            fp = os.path.join(root, f)
            try:
                if os.path.islink(fp) or (pred and not pred(fp)):
                    continue
                total += os.path.getsize(fp)
                count += 1
            except OSError:
                continue
    return total, count


def _purge(path, ctx, pred=None):
    freed = kept = 0
    for root, dirs, files in os.walk(path, onerror=lambda e: None):
        dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root, d))]
        for f in files:
            fp = os.path.join(root, f)
            try:
                if os.path.islink(fp) or (pred and not pred(fp)):
                    continue
                size = os.path.getsize(fp)
                os.remove(fp)
                freed += size
            except (OSError, PermissionError):
                kept += 1
                            
    for root, dirs, _files in os.walk(path, topdown=False, onerror=lambda e: None):
        for d in dirs:
            try:
                os.rmdir(os.path.join(root, d))
            except OSError:
                pass
    return freed, kept


class CleanupPhase(Phase):
    id = 1
    icon = "\U0001F9F9"
    name = "Limpieza profunda"
    description = "Temporales, caches, papelera, prefetch antiguo y volcados"

    def _targets(self):
        local = os.environ.get("LOCALAPPDATA", "")
        win = os.environ.get("SystemRoot", r"C:\Windows")
        thirty_days = time.time() - 30 * 86400
        return [
            ("Archivos temporales del usuario",
             os.environ.get("TEMP", os.path.join(local, "Temp")), None, False),
            ("Archivos temporales de Windows",
             os.path.join(win, "Temp"), None, True),
            ("Prefetch con mas de 30 dias",
             os.path.join(win, "Prefetch"),
             lambda p: p.lower().endswith(".pf")
             and os.path.getmtime(p) < thirty_days, True),
            ("Mini-volcados de errores (Minidump)",
             os.path.join(win, "Minidump"), None, True),
            ("Volcados de aplicaciones del usuario",
             os.path.join(local, "CrashDumps"), None, False),
            ("Cache de miniaturas (Explorer)",
             os.path.join(local, "Microsoft", "Windows", "Explorer"),
             lambda p: os.path.basename(p).lower().startswith("thumbcache_"),
             False),
        ]

    def _clean_update_cache(self):
        ctx = self.ctx
        path = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"),
                            "SoftwareDistribution", "Download")
        if not os.path.isdir(path):
            return
        size, _ = _scan(path)
        ctx.info(f"Cache de Windows Update: {size / _MB:.1f} MB")
        if ctx.dry_run or size == 0:
            return
        for svc in ("wuauserv", "bits"):
            run_cmd(["net", "stop", svc], timeout=60)
        freed, _ = _purge(path, ctx)
        for svc in ("bits", "wuauserv"):
            run_cmd(["net", "start", svc], timeout=60)
        ctx.changed(f"Cache de Windows Update limpiada: {freed / _MB:.1f} MB")

    def _empty_recycle_bin(self):
        ctx = self.ctx
        if ctx.dry_run:
            ctx.info("Papelera de reciclaje (simulacion: no se vacia)")
            return
        rc, _ = run_ps("Clear-RecycleBin -Force -ErrorAction SilentlyContinue",
                       timeout=180)
        if rc == 0:
            ctx.changed("Papelera de reciclaje vaciada")

    def _flush_dns_logs(self):
                                                                           
        if self.ctx.dry_run:
            return
        run_cmd(["wevtutil", "cl", "Microsoft-Windows-Diagnostic"], timeout=30)

    def run(self):
        ctx = self.ctx
        total = 0
        for label, path, pred, _admin in self._targets():
            if not os.path.isdir(path):
                continue
            size, count = _scan(path, pred)
            ctx.info(f"{label}: {size / _MB:.1f} MB en {count} archivos")
            if ctx.dry_run:
                continue
            freed, kept = _purge(path, ctx, pred)
            total += freed
            msg = f"{label}: liberados {freed / _MB:.1f} MB"
            if kept:
                msg += f" ({kept} en uso, omitidos)"
            ctx.changed(msg)

        self._clean_update_cache()
        self._empty_recycle_bin()
        self._flush_dns_logs()
        if not ctx.dry_run:
            ctx.ok(f"TOTAL liberado en disco: {total / _MB:.1f} MB")
