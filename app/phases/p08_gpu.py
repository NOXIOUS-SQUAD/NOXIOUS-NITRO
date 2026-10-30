import winreg

from app.core.proc import ps_json
from app.phases.base import Phase

_HAGS_PATH = r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers"


class GpuPhase(Phase):
    id = 8
    icon = "\U0001F3AE"
    name = "GPU y graficos"
    description = "Informe de drivers y aceleracion por hardware (HAGS)"

    def _report_gpus(self):
        rows = ps_json(
            "Get-CimInstance Win32_VideoController | "
            "Select-Object Name, DriverVersion, DriverDate, "
            "AdapterRAM, CurrentRefreshRate")
        for r in rows or []:
            vram = (r.get("AdapterRAM") or 0) / (1024 ** 3)
            self.ctx.info(f"GPU: {r.get('Name')} | driver "
                          f"{r.get('DriverVersion')} | VRAM ~{vram:.1f} GB | "
                          f"{r.get('CurrentRefreshRate') or '?'} Hz")

    def _enable_hags(self):
        ctx = self.ctx
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, _HAGS_PATH, 0,
                                winreg.KEY_READ) as key:
                current, _ = winreg.QueryValueEx(key, "HwSchMode")
        except OSError:
            current = None
        ctx.info(f"Programacion de GPU por hardware (HAGS): {current}")
        if current == 2:
            ctx.ok("HAGS ya estaba activado")
            return
        ctx.backup.record("reg", hive="HKLM", path=_HAGS_PATH,
                          name="HwSchMode", value=current if current else 1,
                          type="REG_DWORD")
        if not ctx.dry_run:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, _HAGS_PATH, 0,
                                    winreg.KEY_SET_VALUE) as key:
                    winreg.SetValueEx(key, "HwSchMode", 0, winreg.REG_DWORD, 2)
                ctx.changed("HAGS activado (efectivo tras reiniciar)")
            except OSError as exc:
                ctx.warn(f"No se pudo activar HAGS: {exc}")

    def run(self):
        self._report_gpus()
        self._enable_hags()
        self.ctx.ok("Fase de GPU completada")
