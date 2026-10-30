import os
import re

import psutil

from app.config import DATA_DIR
from app.core.proc import run_cmd
from app.phases.base import Phase


class PowerPhase(Phase):
    id = 11
    icon = "\U0001F50B"
    name = "Energia y bateria"
    description = "Informe de salud de la bateria y ahorro inteligente"

    def run(self):
        ctx = self.ctx
        bat = psutil.sensors_battery()
        if bat is None:
            ctx.info("Equipo de sobremesa (sin bateria): nada que optimizar "
                     "en esta fase")
            ctx.ok("Fase de energia completada")
            return

        ctx.info(f"Bateria actual: {bat.percent:.0f}% "
                 f"({'cargando' if bat.power_plugged else 'en uso'})")

        report = os.path.join(DATA_DIR, "battery_report.html")
        rc, _ = run_cmd(["powercfg", "/batteryreport", "/output", report],
                        timeout=120)
        if rc == 0 and os.path.isfile(report):
            try:
                with open(report, "r", encoding="utf-8", errors="replace") as fh:
                    html = fh.read()
                caps = re.findall(r"([\d.,]+)\s*mWh", html)
                if len(caps) >= 2:
                    design = float(caps[0].replace(".", "").replace(",", "."))
                    full = float(caps[1].replace(".", "").replace(",", "."))
                    if design:
                        ctx.ok(f"Salud de la bateria: {full / design * 100:.1f}% "
                               f"({full:.0f} de {design:.0f} mWh)")
            except (OSError, ValueError):
                pass
            ctx.info(f"Informe completo: {report}")

        if not ctx.dry_run:
            run_cmd(["powercfg", "/setdcvalueindex", "SCHEME_CURRENT",
                     "SUB_VIDEO", "VIDEOIDLE", "300"])                     
            run_cmd(["powercfg", "/setdcvalueindex", "SCHEME_CURRENT",
                     "SUB_DISK", "DISKIDLE", "600"])                     
            run_cmd(["powercfg", "/setactive", "SCHEME_CURRENT"])
            ctx.changed("Ahorro con bateria: pantalla 5 min, disco 10 min")
        ctx.ok("Fase de energia completada")
