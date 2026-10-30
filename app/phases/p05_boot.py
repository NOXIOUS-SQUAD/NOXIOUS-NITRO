import winreg

from app.phases.base import Phase

_RUN_KEYS = [
    ("HKCU", winreg.HKEY_CURRENT_USER,
     r"Software\Microsoft\Windows\CurrentVersion\Run"),
    ("HKLM", winreg.HKEY_LOCAL_MACHINE,
     r"Software\Microsoft\Windows\CurrentVersion\Run"),
]

                                                                  
_SAFE_DISABLE = ("adobearm", "adobe acrobat", "ccxprocess", "adobeipcbroker",
                 "adobegcclient", "adobecollabsync", "jusched", "quicktime",
                 "ituneshelper")


class BootPhase(Phase):
    id = 5
    icon = "\U0001F680"
    name = "Arranque del sistema"
    description = "Inicio rapido y limpieza de programas de arranque"

    def _enable_fast_startup(self):
        ctx = self.ctx
        path = r"SYSTEM\CurrentControlSet\Control\Session Manager\Power"
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0,
                                winreg.KEY_READ) as key:
                current, _ = winreg.QueryValueEx(key, "HiberbootEnabled")
        except OSError:
            current = None
        ctx.info(f"Inicio rapido actual: {current}")
        if current == 1:
            ctx.ok("El inicio rapido ya estaba activado")
            return
        ctx.backup.record("reg", hive="HKLM", path=path,
                          name="HiberbootEnabled", value=current or 0,
                          type="REG_DWORD")
        if not ctx.dry_run:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0,
                                    winreg.KEY_SET_VALUE) as key:
                    winreg.SetValueEx(key, "HiberbootEnabled", 0,
                                      winreg.REG_DWORD, 1)
                ctx.changed("Inicio rapido (Fast Startup) activado")
            except OSError as exc:
                ctx.warn(f"No se pudo activar el inicio rapido: {exc}")

    def _startup_items(self):
        items = []
        for hive_name, hive, path in _RUN_KEYS:
            try:
                with winreg.OpenKey(hive, path) as key:
                    i = 0
                    while True:
                        try:
                            name, value, vtype = winreg.EnumValue(key, i)
                            items.append((hive_name, path, name, value, vtype))
                            i += 1
                        except OSError:
                            break
            except OSError:
                continue
        return items

    def run(self):
        ctx = self.ctx
        self._enable_fast_startup()

        items = self._startup_items()
        ctx.info(f"Programas en el arranque: {len(items)}")
        disabled = 0
        for hive, path, name, value, vtype in items:
            ctx.info(f"  - {name}: {str(value)[:80]}")
            if not ctx.dry_run and any(k in name.lower() for k in _SAFE_DISABLE):
                vtype_name = {winreg.REG_SZ: "REG_SZ",
                              winreg.REG_EXPAND_SZ: "REG_EXPAND_SZ"}.get(
                                  vtype, "REG_SZ")
                ctx.backup.record("reg_delete", hive=hive, path=path, name=name,
                                  value=value, type=vtype_name)
                try:
                    with winreg.OpenKey(
                            {"HKCU": winreg.HKEY_CURRENT_USER,
                             "HKLM": winreg.HKEY_LOCAL_MACHINE}[hive],
                            path, 0, winreg.KEY_SET_VALUE) as key:
                        winreg.DeleteValue(key, name)
                    ctx.changed(f"Entrada de arranque deshabilitada: {name}")
                    disabled += 1
                except OSError as exc:
                    ctx.warn(f"No se pudo quitar {name}: {exc}")
        if not ctx.dry_run:
            ctx.ok(f"{disabled} entradas de arranque innecesarias quitadas "
                   "(las demas se conservan intactas)")
