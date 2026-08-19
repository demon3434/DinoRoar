import logging
import socket
from ..config import settings
from ..database import SessionLocal
from .mdns import ServiceDiscoveryBroadcaster

logger = logging.getLogger("DinoRoar.mdns_discovery")

# mDNS Broadcaster Instance
broadcaster = ServiceDiscoveryBroadcaster()

def _detect_local_ip() -> str:
    """
    Attempts to detect the machine's primary local LAN IP address.
    """
    try:
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.connect(("8.8.8.8", 80))
        detected = udp.getsockname()[0]
        udp.close()
        if detected and not detected.startswith("127.") and not detected.startswith("172."):
            return detected
    except Exception:
        pass

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        detected_ip = s.getsockname()[0]
        s.close()
        if detected_ip and not detected_ip.startswith("127.") and not detected_ip.startswith("172."):
            return detected_ip
    except Exception:
        pass

    try:
        ip = socket.gethostbyname(socket.gethostname())
        if ip and not ip.startswith("127.") and not ip.startswith("172."):
            return ip
    except Exception:
        pass

    return ""


def get_mdns_settings_and_start():
    """
    Reads mDNS settings from environment or auto-detected local IP on startup and starts the mDNS broadcast.
    """
    try:
        host = ""
        if settings.service_advertise_host and settings.service_advertise_host.strip():
            host = settings.service_advertise_host.strip()
        else:
            host = _detect_local_ip()

        port = settings.service_advertise_port or getattr(settings, "web_port", 8080) or 8080

        if host:
            logger.info(f"Startup: Starting mDNS broadcast for {host}:{port}")
            broadcaster.start(host, port)
        else:
            logger.info("Startup: No host IP configured or detected. Zero-configuration service discovery is idle.")
    except Exception as e:
        logger.error(f"Startup: Failed to initialize mDNS: {e}")

