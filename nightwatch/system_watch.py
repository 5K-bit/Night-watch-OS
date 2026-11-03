from __future__ import annotations

import socket
from datetime import datetime, timezone
from pathlib import Path

import psutil


def _read_pi_temp_c() -> float | None:
    # Common on Raspberry Pi OS
    p = Path("/sys/class/thermal/thermal_zone0/temp")
    try:
        raw = p.read_text(encoding="utf-8").strip()
        milli = int(raw)
        return milli / 1000.0
    except Exception:
        return None


def _read_any_temp_c() -> float | None:
    try:
        temps = psutil.sensors_temperatures(fahrenheit=False)
        for _, entries in temps.items():
            for e in entries:
                if e.current is not None:
                    return float(e.current)
    except Exception:
        pass
    return _read_pi_temp_c()


def _network_up() -> bool:
    """Report local network availability without requiring internet access.

    Nightwatch is local-first, so a LAN-only or Tailscale-only node must still be
    considered online. We therefore inspect non-loopback interfaces instead of
    probing a public DNS server.
    """
    try:
        if_stats = psutil.net_if_stats()
        if_addrs = psutil.net_if_addrs()
    except Exception:
        return False

    for name, stats in if_stats.items():
        if not stats.isup or name.lower() in {"lo", "lo0", "loopback"}:
            continue
        for address in if_addrs.get(name, []):
            if address.family not in {socket.AF_INET, socket.AF_INET6}:
                continue
            value = (address.address or "").split("%", 1)[0]
            if value and value not in {"127.0.0.1", "::1"}:
                return True
    return False


def read_system_snapshot() -> dict:
    cpu = float(psutil.cpu_percent(interval=0.15))
    vm = psutil.virtual_memory()
    du = psutil.disk_usage("/")

    return {
        "at": datetime.now(timezone.utc),
        "cpu_percent": cpu,
        "ram_percent": float(vm.percent),
        "ram_used_mb": int(vm.used / (1024 * 1024)),
        "ram_total_mb": int(vm.total / (1024 * 1024)),
        "disk_percent": float(du.percent),
        "disk_used_gb": round(du.used / (1024 * 1024 * 1024), 2),
        "disk_total_gb": round(du.total / (1024 * 1024 * 1024), 2),
        "temp_c": _read_any_temp_c(),
        "network_up": _network_up(),
    }
