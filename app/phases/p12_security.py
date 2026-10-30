import winreg

from app.core.proc import run_ps
from app.phases.base import Phase


class SecurityPhase(Phase):
    id = 12
    icon = "\U0001F6E1"
    name = "Seguridad"
    description = "Defender, firewall y UAC verificados y reforzados"

    def _defender(self):
        ctx = self.ctx
        rc, out = run_ps(
            "$s = Get-MpComputerStatus; "
            "Write-Output \"$($s.RealTimeProtectionEnabled)"
            "|$($s.AntivirusEnabled)\"", timeout=90)
        if rc != 0 or "|" not in out:
            ctx.warn("No se pudo consultar el estado de Windows Defender")
            return
        rtp, av = [v.strip() == "True" for v in out.strip().split("|")[:2]]
        ctx.info(f"Defender - antivirus: {av}, proteccion en tiempo real: {rtp}")
        if not rtp and not ctx.dry_run:
            rc, _ = run_ps("Set-MpPreference -DisableRealtimeMonitoring $false",
                           timeout=90)
            if rc == 0:
                ctx.changed("Proteccion en tiempo real de Defender reactivada")
        elif rtp:
            ctx.ok("Windows Defender activo y protegiendo")

    def _firewall(self):
        ctx = self.ctx
        rc, out = run_ps(
            "$f = Get-NetFirewallProfile; "
            "($f | ForEach-Object { $_.Enabled }) -join ','", timeout=60)
        if rc != 0:
            ctx.warn("No se pudo consultar el firewall")
            return
        states = [s.strip() == "True" for s in out.strip().split(",")]
        if all(states):
            ctx.ok("Firewall de Windows activo en todos los perfiles")
            return
        if not ctx.dry_run:
            rc, _ = run_ps("Set-NetFirewallProfile -All -Enabled True",
                           timeout=60)
            if rc == 0:
                ctx.changed("Firewall activado en todos los perfiles")
        else:
            ctx.warn("Hay perfiles de firewall desactivados")

    def _uac(self):
        ctx = self.ctx
        path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0,
                                winreg.KEY_READ) as key:
                enable_lua, _ = winreg.QueryValueEx(key, "EnableLUA")
        except OSError:
            return
        if enable_lua == 1:
            ctx.ok("Control de cuentas de usuario (UAC) activo")
        else:
            ctx.warn("UAC desactivado: no se modifica automaticamente, "
                     "activalo en Configuracion > Seguridad")

    def run(self):
        self._defender()
        self._firewall()
        self._uac()
        self.ctx.ok("Verificacion de seguridad completada")
