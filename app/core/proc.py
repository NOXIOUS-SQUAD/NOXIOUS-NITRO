import base64
import json
import subprocess

_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def run_cmd(args, timeout=120):
    try:
        p = subprocess.run(
            args, capture_output=True, timeout=timeout,
            creationflags=_NO_WINDOW,
        )
        out = (p.stdout or b"").decode("cp850", errors="replace")
        err = (p.stderr or b"").decode("cp850", errors="replace")
        return p.returncode, out + err
    except subprocess.TimeoutExpired:
        return -1, "TIMEOUT"
    except OSError as exc:
        return -1, str(exc)


def run_ps(script, timeout=300):
    full = "$ProgressPreference='SilentlyContinue';" + script
    encoded = base64.b64encode(full.encode("utf-16-le")).decode("ascii")
    return run_cmd(
        ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy",
         "Bypass", "-EncodedCommand", encoded], timeout=timeout)


def ps_json(script, timeout=120):
    rc, out = run_ps(f"@({script}) | ConvertTo-Json -Depth 4 -Compress", timeout)
    if rc != 0 or not out.strip():
        return None
                                                                      
    start = min([i for i in (out.find("["), out.find("{")) if i >= 0],
                default=-1)
    end = max(out.rfind("]"), out.rfind("}"))
    candidate = out[start:end + 1] if 0 <= start < end else out.strip()
    try:
        data = json.loads(candidate)
        if isinstance(data, list):
            return data
        return [data]                                        
    except (json.JSONDecodeError, ValueError):
        return None
