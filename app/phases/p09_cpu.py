import re

from app.core.proc import run_cmd
from app.phases.base import Phase

_ULTIMATE = "e9a42b02-d5df-448d-aa00-03f14749eb61"                      
_HIGH = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"                        
_GUID_RE = re.compile(r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
                      r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12})")


def _active_scheme():
    rc, out = run_cmd(["powercfg", "/getactivescheme"])
    m = _GUID_RE.search(out) if rc == 0 else None
    return m.group(1) if m else None


class CpuPhase(Phase):
    id = 9
    icon = "\U0001F4AA"
    name = "CPU y procesador"
    description = "Plan de maximo rendimiento y CPU sin estrangulamiento"

    def run(self):
        ctx = self.ctx
        previous = _active_scheme()
        ctx.info(f"Plan de energia actual: {previous}")

        if ctx.dry_run:
            ctx.ok("Simulacion: se activaria el plan de maximo rendimiento "
                   "y el estado minimo del procesador al 100%")
            return

        if previous:
            ctx.backup.record("powerplan", guid=previous)

        new_guid = None
        for scheme in (_ULTIMATE, _HIGH):
            rc, out = run_cmd(["powercfg", "/duplicatescheme", scheme])
            if rc == 0:
                m = _GUID_RE.search(out)
                if m:
                    new_guid = m.group(1)
                    break
        if not new_guid:
                                                                       
            new_guid = _HIGH
            rc, out = run_cmd(["powercfg", "/list"])
            if _ULTIMATE.lower() in out.lower():
                new_guid = _ULTIMATE

        run_cmd(["powercfg", "/setactive", new_guid])
                                                              
        run_cmd(["powercfg", "/setacvalueindex", new_guid, "SUB_PROCESSOR",
                 "PROCTHROTTLEMIN", "100"])
        run_cmd(["powercfg", "/setdcvalueindex", new_guid, "SUB_PROCESSOR",
                 "PROCTHROTTLEMIN", "100"])
        run_cmd(["powercfg", "/setactive", new_guid])
        ctx.changed("Plan de maximo rendimiento activo, estado minimo de "
                    "CPU al 100%")
