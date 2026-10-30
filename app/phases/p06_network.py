import re

from app.core.proc import run_cmd, ps_json, run_ps
from app.phases.base import Phase

_DNS_PRIMARY = "1.1.1.1"
_DNS_SECONDARY = "1.0.0.1"


class NetworkPhase(Phase):
    id = 6
    icon = "\U0001F310"
    name = "Red e Internet"
    description = "DNS rapidos, limpieza de cache y ajuste TCP"

    def _ping_ms(self, host):
        rc, out = run_cmd(["ping", "-n", "6", host], timeout=30)
        vals = [int(v) for v in re.findall(r"(\d+)\s*ms", out)]
        return round(sum(vals) / len(vals), 1) if vals else None

    def _dns_rollback_data(self):
        rows = ps_json(
            "Get-DnsClientServerAddress -AddressFamily IPv4 | "
            "Where-Object { $_.ServerAddresses.Count -gt 0 } | "
            "Select-Object InterfaceAlias, ServerAddresses")
        return {r["InterfaceAlias"]: r.get("ServerAddresses") or []
                for r in rows or []}

    def run(self):
        ctx = self.ctx

        before = self._ping_ms(_DNS_PRIMARY)
        if before is not None:
            ctx.info(f"Latencia actual a {_DNS_PRIMARY}: {before} ms")

        if not ctx.dry_run:
            run_cmd(["ipconfig", "/flushdns"], timeout=30)
            run_cmd(["ipconfig", "/registerdns"], timeout=60)
            ctx.changed("Cache DNS limpiada y renovada")

        backups = self._dns_rollback_data()
        adapters = [a for a in ps_json(
            "Get-NetAdapter | Where-Object Status -eq 'Up' | "
            "Select-Object -ExpandProperty Name") or []]

        if not adapters:
            ctx.info("No se detectaron adaptadores de red activos")
        for iface in adapters:
            old = backups.get(iface, [])
            if _DNS_PRIMARY in old:
                ctx.info(f"{iface}: ya usa DNS rapidos")
                continue
            ctx.info(f"{iface}: DNS actual {old or 'DHCP'}")
            if ctx.dry_run:
                continue
            ctx.backup.record("dns", iface=iface, servers=old)
            rc, out = run_ps(
                f"Set-DnsClientServerAddress -InterfaceAlias '{iface}' "
                f"-ServerAddresses '{_DNS_PRIMARY}','{_DNS_SECONDARY}'")
            if rc == 0:
                ctx.changed(f"{iface}: DNS -> {_DNS_PRIMARY}, {_DNS_SECONDARY}")
            else:
                ctx.warn(f"{iface}: no se pudo cambiar el DNS")

                                                               
        rc, out = run_ps("(Get-NetTCPSetting -SettingName Internet)"
                         ".AutoTuningLevelLocal", timeout=60)
        current = out.strip().splitlines()[-1].strip()\
            if rc == 0 and out.strip() else None
        if current:
            ctx.info(f"Auto-tuning TCP actual: {current}")
            if not ctx.dry_run and str(current).lower() != "normal":
                ctx.backup.record("tcp", field="autotuning", value=current)
                rc, _ = run_ps("Set-NetTCPSetting -SettingName Internet "
                               "-AutoTuningLevelLocal Normal", timeout=60)
                if rc == 0:
                    ctx.changed("Auto-tuning TCP ajustado a 'Normal'")
                else:
                    ctx.warn("No se pudo ajustar el auto-tuning TCP")

        if not ctx.dry_run:
            after = self._ping_ms(_DNS_PRIMARY)
            if before and after:
                ctx.ok(f"Latencia antes/despues: {before} ms -> {after} ms")
