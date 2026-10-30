from app.core.proc import ps_json, run_cmd, run_ps
from app.phases.base import Phase

                                            
SERVICES = [
    ("DiagTrack", "Telemetria y experiencias de Microsoft", True),
    ("dmwappushservice", "Enrutamiento de mensajes WAP", True),
    ("RetailDemo", "Modo demostracion de tienda", True),
    ("RemoteRegistry", "Registro remoto (mejora seguridad)", True),
    ("Fax", "Servicio de fax", True),
    ("XblAuthManager", "Xbox Live - autenticacion", True),
    ("XblGameSave", "Xbox Live - partidas guardadas", True),
    ("XboxNetApiSvc", "Xbox Live - red", True),
    ("XboxGipSvc", "Xbox - accesorios", True),
    ("NvTelemetryContainer", "Telemetria de NVIDIA", True),
    ("WSearch", "Indexado de busqueda de Windows", False),
    ("SysMain", "Superfetch (solo recomendable en SSD)", False),
    ("Spooler", "Cola de impresion (solo si no imprimes)", False),
    ("bthserv", "Soporte Bluetooth (solo si no lo usas)", False),
]


class ServicesPhase(Phase):
    id = 2
    icon = "⚙️"
    name = "Servicios de Windows"
    description = "Deshabilita servicios prescindibles (telemetria, Xbox...)"

    def run(self):
        ctx = self.ctx
        applied = 0
        for name, desc, default_on in SERVICES:
            info = ps_json(
                f"Get-CimInstance Win32_Service -Filter \"Name='{name}'\" "
                "| Select-Object Name, StartMode, State")
            if not info:
                continue                                     
            svc = info[0]
            start, state = svc.get("StartMode"), svc.get("State")
            if start == "Disabled":
                continue

            tag = "" if default_on else " (OPCIONAL)"
            ctx.info(f"{name}: {desc} [actual: {start}/{state}]{tag}")
            if ctx.dry_run or not default_on:
                continue

            ctx.backup.record("service", name=name, start_mode=start)
            rc, out = run_cmd(["sc.exe", "config", name, "start=", "disabled"])
            if rc == 0:
                if state == "Running":
                    run_ps(f"Stop-Service -Name '{name}' -Force "
                           "-ErrorAction SilentlyContinue", timeout=60)
                ctx.changed(f"Servicio {name} deshabilitado")
                applied += 1
            else:
                ctx.warn(f"No se pudo deshabilitar {name}: {out.strip()[:120]}")

        if ctx.dry_run:
            ctx.ok("Simulacion completada: no se modifico ningun servicio")
        else:
            ctx.ok(f"{applied} servicios optimizados")
