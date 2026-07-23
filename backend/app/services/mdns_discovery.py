import logging
from ..config import settings
from ..database import SessionLocal
from .mdns import ServiceDiscoveryBroadcaster

logger = logging.getLogger("DinoRoar.mdns_discovery")

# mDNS Broadcaster Instance
broadcaster = ServiceDiscoveryBroadcaster()

def get_mdns_settings_and_start():
    """
    Attempts to read mDNS settings from system_settings_manager on startup and starts the broadcast.
    """
    try:
        from ..system_settings_manager import load_system_settings
        sys_settings = load_system_settings()
        host = sys_settings.get("host_ip", "").strip()
        port = sys_settings.get("host_port", 8080)
        
        if host:
            logger.info(f"Startup: Starting mDNS broadcast for {host}:{port}")
            broadcaster.start(host, port)
        else:
            # 自动获取本机局域网 IP 作为默认的发布地址
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(('10.255.255.255', 1))
                detected_ip = s.getsockname()[0]
                if detected_ip and detected_ip != '127.0.0.1' and not detected_ip.startswith("172."):
                    host = detected_ip
            except Exception as e:
                logger.warning(f"Startup: Failed to auto-detect local IP: {e}")
            finally:
                s.close()
                
            if host:
                logger.info(f"Startup: Auto-detected IP. Starting mDNS broadcast for {host}:{port}")
                broadcaster.start(host, port)
            else:
                logger.info("Startup: No host IP configured. Zero-configuration service discovery is idle.")
    except Exception as e:
        logger.error(f"Startup: Failed to initialize mDNS: {e}")


def start_udp_discovery_responder():
    import socket
    import threading
    import json
    
    def responder():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.bind(("", 8090))
            logger.info("UDP Discovery Responder listening on port 8090")
        except Exception as e:
            logger.error(f"Failed to bind UDP socket on 8090: {e}")
            return
            
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                message = data.decode("utf-8", errors="ignore").strip()
                if message == "DISCOVER_DINOROAR_REQUEST":
                    from ..system_settings_manager import load_system_settings
                    sys_settings = load_system_settings()
                    host_ip = sys_settings.get("host_ip", "").strip()
                    port = sys_settings.get("host_port", 8080)
                        
                    response_data = {"port": port, "ip": host_ip}
                    response_bytes = json.dumps(response_data).encode("utf-8")
                    sock.sendto(response_bytes, addr)
            except Exception as e:
                logger.warning(f"Error in UDP discovery loop: {e}")

    t = threading.Thread(target=responder, daemon=True)
    t.start()
