from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import hashlib
import secrets
import json
import base64
import hmac
from fastapi import HTTPException, status
from app.core.config import settings

PEPPER = "library_system_pepper_2025"


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64url_decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def _build_signature(signature_input: str) -> str:
    digest = hmac.new(
        settings.secret_key.encode(),
        signature_input.encode(),
        hashlib.sha256,
    ).digest()
    return _b64url_encode(digest)


def _build_legacy_signature(signature_input: str) -> str:
    legacy_signature = hashlib.sha256(
        f"{signature_input}{settings.secret_key}".encode()
    ).hexdigest()[:43]
    return _b64url_encode(legacy_signature.encode())

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет пароль"""
    if not plain_password or not hashed_password:
        return False
    
    try:
        parts = hashed_password.split('$')
        if len(parts) != 3:
            return False
        
        algorithm, salt, stored_hash = parts
        
        if algorithm == "sha256":
            password_with_salt = f"{PEPPER}{plain_password}{salt}"
            expected_hash = hashlib.sha256(password_with_salt.encode()).hexdigest()
            return secrets.compare_digest(expected_hash, stored_hash)
        
        return False
        
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """Создает хеш пароля"""
    if not password:
        raise ValueError("Password cannot be empty")
    
    safe_password = password[:50]
    salt = secrets.token_hex(8)
    password_with_salt = f"{PEPPER}{safe_password}{salt}"
    password_hash = hashlib.sha256(password_with_salt.encode()).hexdigest()
    
    return f"sha256${salt}${password_hash}"

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Создает простой JWT-подобный токен"""
    to_encode = data.copy()

    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=30)

    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp())
    })

    header = {"alg": settings.algorithm, "typ": "JWT"}
    header_encoded = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_encoded = _b64url_encode(json.dumps(to_encode, separators=(",", ":")).encode())
    signature_input = f"{header_encoded}.{payload_encoded}"
    signature_encoded = _build_signature(signature_input)

    return f"{header_encoded}.{payload_encoded}.{signature_encoded}"


def verify_token(token: str) -> Dict[str, Any]:
    """Проверяет токен"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is empty"
        )

    parts = token.split('.')
    if len(parts) != 3:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format"
        )
    
    try:
        header = json.loads(_b64url_decode(parts[0]))
        payload = json.loads(_b64url_decode(parts[1]))

        if header.get("alg") and header["alg"] != settings.algorithm:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unsupported token algorithm"
            )

        signature_input = f"{parts[0]}.{parts[1]}"
        expected_signature = _build_signature(signature_input)
        legacy_signature = _build_legacy_signature(signature_input)

        if not (
            secrets.compare_digest(parts[2], expected_signature)
            or secrets.compare_digest(parts[2], legacy_signature)
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token signature"
            )

        if 'exp' in payload:
            exp_time = datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
            if exp_time < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired"
                )

        return payload

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}"
        )
