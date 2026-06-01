from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
from app.config import get_settings


def encrypt(plaintext: str) -> str:
    settings = get_settings()
    key = bytes.fromhex(settings.ENCRYPTION_KEY)
    cipher = AES.new(key, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(plaintext.encode("utf-8"), AES.block_size))
    return base64.b64encode(cipher.iv + ct_bytes).decode("utf-8")


def decrypt(ciphertext: str) -> str:
    settings = get_settings()
    key = bytes.fromhex(settings.ENCRYPTION_KEY)
    raw = base64.b64decode(ciphertext)
    iv = raw[:16]
    ct = raw[16:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    pt = unpad(cipher.decrypt(ct), AES.block_size)
    return pt.decode("utf-8")
