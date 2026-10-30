import glob
import json
import os
import winreg
from datetime import datetime

from app.config import BACKUP_DIR
from app.core.proc import run_cmd, run_ps

_HIVES = {"HKLM": winreg.HKEY_LOCAL_MACHINE, "HKCU": winreg.HKEY_CURRENT_USER}
_REG_TYPES = {"REG_SZ": winreg.REG_SZ, "REG_DWORD": winreg.REG_DWORD,
              "REG_EXPAND_SZ": winreg.REG_EXPAND_SZ,
              "REG_MULTI_SZ": winreg.REG_MULTI_SZ}

_SC_START = {"auto": "auto", "demand": "demand", "disabled": "disabled",
             "Auto": "auto", "Manual": "demand", "Disabled": "disabled"}


class BackupManager:
    def __init__(self):
        os.makedirs(BACKUP_DIR, exist_ok=True)
        self.entries = []
        self.path = os.path.join(
            BACKUP_DIR, f"backup_{datetime.now():%Y%m%d_%H%M%S}.json")

    def record(self, kind, **data):
        entry = {"kind": kind}
        entry.update(data)
        self.entries.append(entry)

    def save(self):
        if not self.entries:
            return None
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump({"created": datetime.now().isoformat(),
                       "entries": self.entries}, fh, indent=2, ensure_ascii=False)
        return self.path


def latest_backup():
    files = sorted(glob.glob(os.path.join(BACKUP_DIR, "backup_*.json")))
    return files[-1] if files else None


def apply_rollback(path, log):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            entries = json.load(fh).get("entries", [])
    except (OSError, json.JSONDecodeError) as exc:
        log(f"No se pudo leer el backup: {exc}", "err")
        return 0, 1

    ok = err = 0
    for e in reversed(entries):
        try:
            _rollback_entry(e, log)
            ok += 1
        except Exception as exc:                                     
            err += 1
            log(f"Error revirtiendo {e.get('kind')}: {exc}", "err")
    return ok, err


def _rollback_entry(e, log):
    kind = e["kind"]

    if kind == "service":
        sc = _SC_START.get(e.get("start_mode"), "demand")
        run_cmd(["sc.exe", "config", e["name"], "start=", sc])
        log(f"Servicio {e['name']} restaurado a {e.get('start_mode')}", "ok")

    elif kind == "reg":
        hive = _HIVES[e["hive"]]
        with winreg.CreateKey(hive, e["path"]) as key:
            winreg.SetValueEx(key, e["name"], 0, _REG_TYPES[e["type"]], e["value"])
        log(f"Registro restaurado: {e['hive']}\\{e['path']}\\{e['name']}", "ok")

    elif kind == "reg_delete":
        run_cmd(["reg", "add", f"{e['hive']}\\{e['path']}",
                 "/v", e["name"], "/t", e["type"], "/d", str(e["value"]), "/f"])
        log(f"Valor de registro recreado: {e['path']}\\{e['name']}", "ok")

    elif kind == "regfile":
        run_cmd(["reg", "import", e["file"]])
        log(f"Clave de registro restaurada desde {os.path.basename(e['file'])}", "ok")

    elif kind == "dns":
        if e.get("servers"):
            servers = ",".join(f'"{s}"' for s in e["servers"])
            run_ps(f"Set-DnsClientServerAddress -InterfaceAlias '{e['iface']}' "
                   f"-ServerAddresses @({servers})")
        else:
            run_ps(f"Set-DnsClientServerAddress -InterfaceAlias '{e['iface']}' "
                   "-ResetServerAddresses")
        log(f"DNS de '{e['iface']}' restaurado", "ok")

    elif kind == "powerplan":
        run_cmd(["powercfg", "/setactive", e["guid"]])
        log(f"Plan de energia restaurado ({e['guid'][:8]}...)", "ok")

    elif kind == "fsutil":
        run_cmd(["fsutil", "behavior", "set", e["key"], str(e["value"])])
        log(f"fsutil {e['key']} = {e['value']}", "ok")

    elif kind == "tcp":
        run_ps(f"Set-NetTCPSetting -SettingName Internet "
               f"-AutoTuningLevelLocal '{e['value']}'", timeout=60)
        log(f"Auto-tuning TCP restaurado a {e['value']}", "ok")

    elif kind == "startup":
        hive = _HIVES[e["hive"]]
        with winreg.CreateKey(hive, e["path"]) as key:
            winreg.SetValueEx(key, e["name"], 0, _REG_TYPES[e["type"]], e["value"])
        log(f"Entrada de inicio restaurada: {e['name']}", "ok")

    else:
        log(f"Tipo de backup desconocido: {kind}", "warn")
