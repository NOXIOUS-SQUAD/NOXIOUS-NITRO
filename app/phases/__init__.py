from app.phases.p01_cleanup import CleanupPhase
from app.phases.p02_services import ServicesPhase
from app.phases.p03_memory import MemoryPhase
from app.phases.p04_disk import DiskPhase
from app.phases.p05_boot import BootPhase
from app.phases.p06_network import NetworkPhase
from app.phases.p07_registry import RegistryPhase
from app.phases.p08_gpu import GpuPhase
from app.phases.p09_cpu import CpuPhase
from app.phases.p10_filesystem import FileSystemPhase
from app.phases.p11_power import PowerPhase
from app.phases.p12_security import SecurityPhase

PHASES = [
    CleanupPhase, ServicesPhase, MemoryPhase, DiskPhase, BootPhase,
    NetworkPhase, RegistryPhase, GpuPhase, CpuPhase, FileSystemPhase,
    PowerPhase, SecurityPhase,
]
