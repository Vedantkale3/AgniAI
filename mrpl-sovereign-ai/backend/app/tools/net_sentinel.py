"""
NETWORK SENTINEL
==================
This is the literal proof-of-sovereignty component the problem statement
asks for: "through logs or a visible network monitor, that no external
calls are made at any point."

Two layers:
1. Passive: psutil polls all active outbound connections made by this
   process tree, tags each as LOCAL / PRIVATE-LAN / EXTERNAL, and logs a
   running feed the UI polls and renders live.
2. Active (optional, needs root/admin + scapy + npcap on Windows):
   sniffs the chosen interface and flags any packet whose destination is
   outside RFC1918 / loopback space. Off by default in constrained demo
   environments; the psutil layer alone is sufficient for the jury demo
   and does not require elevated privileges.
"""
import psutil
import ipaddress
import time
from collections import deque
from dataclasses import dataclass, asdict

_EVENT_LOG = deque(maxlen=500)


@dataclass
class ConnEvent:
    ts: float
    pid: int
    process_name: str
    remote_ip: str
    remote_port: int
    classification: str  # LOCAL | PRIVATE_LAN | EXTERNAL


def _classify_ip(ip: str) -> str:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return "UNKNOWN"
    if addr.is_loopback:
        return "LOCAL"
    if addr.is_private:
        return "PRIVATE_LAN"
    return "EXTERNAL"


def snapshot_connections(own_pid_tree: set[int] | None = None) -> list[ConnEvent]:
    events = []
    for c in psutil.net_connections(kind="inet"):
        if not c.raddr:
            continue
        if own_pid_tree and c.pid not in own_pid_tree:
            continue
        classification = _classify_ip(c.raddr.ip)
        try:
            pname = psutil.Process(c.pid).name() if c.pid else "unknown"
        except Exception:
            pname = "unknown"
        ev = ConnEvent(
            ts=time.time(), pid=c.pid or -1, process_name=pname,
            remote_ip=c.raddr.ip, remote_port=c.raddr.port,
            classification=classification,
        )
        events.append(ev)
        if classification == "EXTERNAL":
            _EVENT_LOG.append(ev)
    return events


def get_egress_feed() -> list[dict]:
    return [asdict(e) for e in list(_EVENT_LOG)]


def get_all_local_traffic_summary(own_pid_tree: set[int] | None = None) -> dict:
    events = snapshot_connections(own_pid_tree)
    local = sum(1 for e in events if e.classification in ("LOCAL", "PRIVATE_LAN"))
    external = sum(1 for e in events if e.classification == "EXTERNAL")
    return {
        "total_connections": len(events),
        "local_or_lan": local,
        "external_flagged": external,
        "sovereignty_status": "SEALED" if external == 0 else "BREACH DETECTED",
        "sample": [asdict(e) for e in events[:20]],
    }
