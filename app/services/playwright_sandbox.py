import ipaddress
import re
import socket
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from app.config import get_settings


class SandboxError(ValueError):
    pass


_PRIVATE_NETWORKS = (
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
)


def _is_private_ip(addr: str) -> bool:
    try:
        ip = ipaddress.ip_address(addr)
    except ValueError:
        return False
    return any(ip in net for net in _PRIVATE_NETWORKS)


def _resolve_host_ips(hostname: str) -> list[str]:
    if re.fullmatch(r"(\d{1,3}\.){3}\d{1,3}", hostname):
        return [hostname]
    if ":" in hostname and not hostname.startswith("["):
        return [hostname]
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise SandboxError(f"无法解析域名: {hostname}") from exc
    return list({info[4][0] for info in infos})


def validate_target_url(url: str) -> str:
    settings = get_settings()
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise SandboxError("仅允许 http/https 协议")
    if not parsed.hostname:
        raise SandboxError("URL 缺少主机名")

    hostname = parsed.hostname.lower()
    if hostname in {"localhost", "0.0.0.0"}:
        raise SandboxError("禁止访问 localhost")

    if settings.playwright_allowed_hosts:
        allowed = {h.strip().lower() for h in settings.playwright_allowed_hosts.split(",") if h.strip()}
        if hostname not in allowed and not any(hostname.endswith(f".{h}") for h in allowed):
            raise SandboxError(f"主机不在白名单: {hostname}")

    if settings.playwright_block_private_network:
        for ip in _resolve_host_ips(hostname):
            if _is_private_ip(ip):
                raise SandboxError(f"禁止访问内网地址: {ip}")

    return url.strip()


def create_sandbox_dir(user_id: str) -> Path:
    settings = get_settings()
    base = Path(settings.playwright_sandbox_dir) / user_id / str(uuid4())
    base.mkdir(parents=True, exist_ok=True)
    return base
