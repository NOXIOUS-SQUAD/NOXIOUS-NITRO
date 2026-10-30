import platform
import time

import psutil

from app.core.proc import ps_json

_last_disk = None
_last_disk_t = 0.0


def snapshot():
    global _last_disk, _last_disk_t
    io = psutil.disk_io_counters()
    now = time.time()
    rate = 0.0
    if _last_disk is not None and io is not None:
        dt = max(now - _last_disk_t, 1e-6)
        rate = ((io.read_bytes + io.write_bytes)
                - (_last_disk.read_bytes + _last_disk.write_bytes)) / dt / 1024
    _last_disk, _last_disk_t = io, now
    return {
        "cpu": psutil.cpu_percent(interval=None),
        "ram": psutil.virtual_memory().percent,
        "disk_kbs": max(rate, 0.0),
        "uptime": time.time() - psutil.boot_time(),
    }


def static_info():
    try:
        build = int(platform.version().split(".")[2])
    except (IndexError, ValueError):
        build = 0
    return {
        "os": f"Windows {platform.release()} (build {build})",
        "machine": platform.machine(),
        "cpu": platform.processor() or "CPU",
        "cores": psutil.cpu_count(logical=True),
        "ram_gb": round(psutil.virtual_memory().total / (1024 ** 3), 1),
        "supported": build >= 19041,
    }


def physical_disks():
    rows = ps_json(
        "Get-PhysicalDisk | Select-Object FriendlyName, MediaType, "
        "HealthStatus, Size")
    disks = []
    for r in rows or []:
        disks.append({
            "name": r.get("FriendlyName", "Disco"),
            "media": r.get("MediaType") or "Unknown",
            "health": r.get("HealthStatus") or "Unknown",
            "size_gb": round((r.get("Size") or 0) / (1024 ** 3), 1),
        })
    return disks


def fmt_uptime(seconds):
    d, rem = divmod(int(seconds), 86400)
    h, rem = divmod(rem, 3600)
    m, _ = divmod(rem, 60)
    return f"{d}d {h:02d}h {m:02d}m" if d else f"{h:02d}h {m:02d}m"
