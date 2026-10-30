import psutil

from app.core.proc import run_cmd, run_ps, ps_json
from app.core.sysinfo import physical_disks
from app.phases.base import Phase


_STORAGE_NS = r"root\Microsoft\Windows\Storage"
_MEDIA = {"3": "HDD", "4": "SSD", "5": "SCM"}


def _media_type(letter):
    part = ps_json(
        f"Get-CimInstance MSFT_Partition -Namespace {_STORAGE_NS} "
        f"-Filter \"DriveLetter='{letter}'\" | "
        "Select-Object -First 1 -ExpandProperty DiskNumber", timeout=60)
    if part:
        disk = ps_json(
            f"Get-CimInstance MSFT_PhysicalDisk -Namespace {_STORAGE_NS} "
            f"-Filter \"DeviceId='{part[0]}'\" | "
            "Select-Object -ExpandProperty MediaType", timeout=60)
        if disk:
            return _MEDIA.get(str(disk[0]), f"Tipo {disk[0]}")
                                                
    rows = ps_json(
        f"Get-Partition -DriveLetter {letter} | Get-Disk | Get-PhysicalDisk "
        "| Select-Object -First 1 -ExpandProperty MediaType", timeout=60)
    return (rows[0] if rows else None) or "Unknown"


class DiskPhase(Phase):
    id = 4
    icon = "💾"
    name = "Velocidad de disco"
    description = "TRIM en SSD, desfragmentacion en HDD e informe SMART"

    def _report_smart(self):
        for d in physical_disks():
            self.ctx.info(f"Disco: {d['name']} | {d['media']} | "
                          f"{d['size_gb']} GB | Salud: {d['health']}")

    def _enable_trim(self):
        ctx = self.ctx
        rc, out = run_cmd(["fsutil", "behavior", "query",
                           "DisableDeleteNotify"])
        if "0" in out:
            ctx.ok("TRIM ya estaba activado")
            return
        ctx.backup.record("fsutil", key="DisableDeleteNotify", value=1)
        if not ctx.dry_run:
            rc, _ = run_cmd(["fsutil", "behavior", "set",
                             "DisableDeleteNotify", "0"])
            if rc == 0:
                ctx.changed("TRIM activado globalmente")
            else:
                ctx.warn("No se pudo activar TRIM")

    def _optimize_volume(self, letter, media):
        ctx = self.ctx
        if ctx.dry_run:
            ctx.info(f"Unidad {letter}: {media} (sin cambios en simulacion)")
            return
        if media == "HDD":
            ctx.info(f"Desfragmentando {letter}: (puede tardar)...")
            rc, _ = run_ps(f"Optimize-Volume -DriveLetter {letter} -Defrag "
                           "-ErrorAction SilentlyContinue", timeout=5400)
            (ctx.changed if rc == 0 else ctx.warn)(
                f"Desfragmentacion de {letter}: "
                + ("completada" if rc == 0 else "no completada"))
        else:
            rc, _ = run_ps(f"Optimize-Volume -DriveLetter {letter} -ReTrim "
                           "-Verbose -ErrorAction SilentlyContinue", timeout=300)
            if rc == 0:
                ctx.changed(f"ReTrim aplicado en {letter}: (SSD)")

    def run(self):
        self._report_smart()
        self._enable_trim()
        letters = []
        for part in psutil.disk_partitions(all=False):
            if "fixed" in part.opts.lower() or part.fstype.upper() == "NTFS":
                letters.append(part.device.rstrip(":\\"))
        for letter in letters:
            self._optimize_volume(letter, _media_type(letter))
        self.ctx.ok("Fase de disco completada")
