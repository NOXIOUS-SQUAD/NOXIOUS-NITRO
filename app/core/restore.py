import winreg

from app.config import APP_NAME
from app.core.proc import run_ps


def _allow_frequent_restore_points(log):
    try:
        key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\SystemRestore"
        with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            winreg.SetValueEx(key, "SystemRestorePointCreationFrequency", 0,
                              winreg.REG_DWORD, 0)
    except OSError as exc:
        log(f"No se pudo ajustar la frecuencia de puntos de restauracion: {exc}",
            "warn")


def create_restore_point(log):
    log("Habilitando Restaurar sistema en C:...", "info")
    run_ps('Enable-ComputerRestore -Drive "C:\\"', timeout=120)
    _allow_frequent_restore_points(log)

    desc = f"{APP_NAME} - Punto previo a optimizacion"
    log(f"Creando punto de restauracion: '{desc}' ...", "info")
    log("(puede tardar varios minutos)", "info")
    rc, out = run_ps(
        f'Checkpoint-Computer -Description "{desc}" '
        '-RestorePointType MODIFY_SETTINGS', timeout=900)

    if rc == 0:
        log("Punto de restauracion creado correctamente.", "ok")
        return True
    log(f"PowerShell devolvio codigo {rc}: {out.strip()[:400]}", "err")
    log("Verifica en 'Proteccion del sistema' que la restauracion este activada.",
        "warn")
    return False
