import re

from app.core.proc import run_cmd
from app.phases.base import Phase


def _query_behavior(key):
    rc, out = run_cmd(["fsutil", "behavior", "query", key])
    if rc != 0:
        return None
                                                                        
    m = re.search(r"=\s*(\d+)", out)
    return m.group(1) if m else None


class FileSystemPhase(Phase):
    id = 10
    icon = "\U0001F4C2"
    name = "Sistema de archivos"
    description = "Ajustes NTFS: ultimo acceso desactivado, estado de 8.3"

    def run(self):
        ctx = self.ctx

        current = _query_behavior("disablelastaccess")
        ctx.info(f"DisableLastAccess actual: {current}")
        if current not in ("1", "3"):                                       
            ctx.backup.record("fsutil", key="disablelastaccess",
                              value=current or "0")
            if not ctx.dry_run:
                rc, _ = run_cmd(["fsutil", "behavior", "set",
                                 "disablelastaccess", "1"])
                if rc == 0:
                    ctx.changed("Actualizacion de ultimo acceso desactivada")
        else:
            ctx.ok("Ultimo acceso ya desactivado")

        dot3 = _query_behavior("disable8dot3")
        ctx.info(f"Nombres 8.3 (disable8dot3): {dot3} "
                 "(se conserva por compatibilidad)")
        ctx.ok("Fase de sistema de archivos completada")
