import logging
import socket
from typing import Optional
from zeroconf import IPVersion, ServiceInfo, Zeroconf
from ..config import settings

logger = logging.getLogger(__name__)

class ServiceDiscoveryBroadcaster:
    def __init__(self):
        self.zc: Optional[Zeroconf] = None
        self.info: Optional[ServiceInfo] = None
        self.active_host: Optional[str] = None
        self.active_port: Optional[int] = None

    def start(self, host: str, port: int) -> bool:
        """
        Starts or restarts the mDNS broadcaster using the configured host and port.
        """
        self.stop()  # Ensure previously running instance is stopped

        if not host or not host.strip():
            logger.warning("mDNS: No host IP configured. Skipping broadcast.")
            return False

        self.active_host = host.strip()
        self.active_port = int(port)

        try:
            self.zc = Zeroconf(ip_version=IPVersion.V4Only)
            
            try:
                ip_bytes = socket.inet_aton(self.active_host)
            except OSError:
                logger.error(f"mDNS: Invalid IP address format: {self.active_host}")
                return False

            service_type = settings.service_discovery_type.strip()
            if not service_type.endswith("."):
                service_type = f"{service_type}."
            if not service_type.endswith(".local."):
                if service_type.endswith(".local"):
                    service_type = f"{service_type}."
                else:
                    service_type = f"{service_type.rstrip('.')}local."

            instance_name = f"{settings.service_discovery_name}.{service_type}"

            properties = {
                b"host": self.active_host.encode("utf-8"),
                b"mappedPort": str(self.active_port).encode("utf-8"),
                b"url": f"http://{self.active_host}:{self.active_port}".encode("utf-8"),
                b"version": b"1.0",
                b"path": b"/api",
            }

            self.info = ServiceInfo(
                type_=service_type,
                name=instance_name,
                addresses=[ip_bytes],
                port=self.active_port,
                properties=properties,
                server=f"{settings.service_discovery_name.lower()}.local."
            )

            logger.info(f"mDNS: Registering service {instance_name} at {self.active_host}:{self.active_port}")
            self.zc.register_service(self.info, allow_name_change=True)
            return True

        except Exception as e:
            logger.exception(f"mDNS: Failed to start service discovery: {e}")
            self.stop()
            return False

    def stop(self):
        """
        Unregisters the service and closes Zeroconf.
        """
        if self.zc:
            try:
                if self.info:
                    logger.info("mDNS: Unregistering service discovery...")
                    self.zc.unregister_service(self.info)
            except Exception as e:
                logger.error(f"mDNS: Error unregistering service: {e}")
            finally:
                try:
                    self.zc.close()
                except Exception as e:
                    logger.error(f"mDNS: Error closing Zeroconf: {e}")
                self.zc = None
                self.info = None
                self.active_host = None
                self.active_port = None
                logger.info("mDNS: Service discovery stopped.")

