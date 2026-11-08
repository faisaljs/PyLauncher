"""Deterministic offline UUID generation (matches Mojang's scheme)."""

import hashlib


def offline_uuid(username: str) -> str:
    """Return the same UUID Mojang uses for offline players.

    Algorithm: MD5("OfflinePlayer:" + username), then stamp the
    bytes as a version-3 UUID with the IETF variant.
    """
    digest = bytearray(hashlib.md5(f"OfflinePlayer:{username}".encode("utf-8")).digest())
    digest[6] = (digest[6] & 0x0F) | 0x30
    digest[8] = (digest[8] & 0x3F) | 0x80
    h = digest.hex()
    return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"