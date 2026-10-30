import os
import re
import winreg
from datetime import datetime

from app.config import BACKUP_DIR
from app.core.proc import run_cmd
from app.phases.base import Phase

_UNINSTALL_PATHS = [
    (winreg.HKEY_CURRENT_USER, "HKCU",
     r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
     winreg.KEY_READ),
    (winreg.HKEY_LOCAL_MACHINE, "HKLM",
     r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
     winreg.KEY_READ | winreg.KEY_WOW64_64KEY),
    (winreg.HKEY_LOCAL_MACHINE, "HKLM",
     r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
     winreg.KEY_READ | winreg.KEY_WOW64_32KEY),
]


def _find_orphans(ctx):
    orphans = []
    for hive, hive_name, path, access in _UNINSTALL_PATHS:
        try:
            with winreg.OpenKey(hive, path, 0, access) as root:
                i = 0
                while True:
                    try:
                        sub = winreg.EnumKey(root, i)
                        i += 1
                    except OSError:
                        break
                    try:
                        with winreg.OpenKey(root, sub, 0, access) as key:
                            vals = {}
                            j = 0
                            while True:
                                try:
                                    n, v, _ = winreg.EnumValue(key, j)
                                    vals[n.lower()] = v
                                    j += 1
                                except OSError:
                                    break
                    except OSError:
                        continue
                    loc = str(vals.get("installlocation", "")).strip().strip('"')
                    name = vals.get("displayname", sub)
                                                                               
                    if loc and re.match(r"^[a-zA-Z]:\\", loc)\
                            and not os.path.isdir(loc):
                        orphans.append((hive_name, f"{path}\\{sub}", str(name)))
        except OSError:
            continue
                                                         
    seen, unique = set(), []
    for o in orphans:
        if o[1] not in seen:
            seen.add(o[1])
            unique.append(o)
    return unique


class RegistryPhase(Phase):
    id = 7
    icon = "\U0001F527"
    name = "Registro de Windows"
    description = "Elimina restos de programas desinstalados (conservador)"

    def run(self):
        ctx = self.ctx
        orphans = _find_orphans(ctx)
        ctx.info(f"Entradas huerfanas detectadas: {len(orphans)}")
        for hive, key_path, name in orphans:
            ctx.info(f"  - {name}")

        if ctx.dry_run or not orphans:
            if ctx.dry_run:
                ctx.ok("Simulacion: no se borro ninguna clave")
            return

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        reg_dir = os.path.join(BACKUP_DIR, f"reg_{stamp}")
        os.makedirs(reg_dir, exist_ok=True)

        removed = 0
        for idx, (hive, key_path, name) in enumerate(orphans):
            full = f"{hive}\\{key_path}"
            backup_file = os.path.join(reg_dir, f"clave_{idx:03d}.reg")
            rc, _ = run_cmd(["reg", "export", full, backup_file, "/y"],
                            timeout=60)
            if rc != 0:
                ctx.warn(f"Sin backup, no se toca: {name}")
                continue
            rc, _ = run_cmd(["reg", "delete", full, "/f"], timeout=60)
            if rc == 0:
                ctx.backup.record("regfile", file=backup_file)
                ctx.changed(f"Entrada huerfana eliminada: {name}")
                removed += 1
        ctx.ok(f"{removed} entradas de registro limpiadas "
               f"(backups en {reg_dir})")
