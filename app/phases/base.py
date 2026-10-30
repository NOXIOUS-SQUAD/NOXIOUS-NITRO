

class PhaseContext:

    def __init__(self, log, backup, dry_run=False):
        self._log = log                                            
        self.backup = backup                      
        self.dry_run = dry_run

    def log(self, msg, level="info"):
        self._log(msg, level)

    def info(self, msg):
        self._log(msg, "info")

    def ok(self, msg):
        self._log(msg, "ok")

    def warn(self, msg):
        self._log(msg, "warn")

    def err(self, msg):
        self._log(msg, "err")

    def changed(self, msg):
        prefix = "[SIMULADO] " if self.dry_run else ""
        self._log(f"{prefix}{msg}", "ok")


class Phase:
    id = 0
    name = ""
    icon = ""
    description = ""

    def __init__(self, ctx: PhaseContext):
        self.ctx = ctx

    def run(self):                                                 
        raise NotImplementedError
