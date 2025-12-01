from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import hashlib
import secrets
import json
import base64
from fastapi import HTTPException, status
from app.core.config import settings

PEPPER = "library_system_pepper_2025"

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
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=30)
    
    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(datetime.utcnow().timestamp())
    })
    
    # Создаем части JWT
    header = {"alg": "HS256", "typ": "JWT"}
    header_encoded = base64.urlsafe_b64encode(
        json.dumps(header).encode()
    ).decode().rstrip('=')
    
    payload_encoded = base64.urlsafe_b64encode(
        json.dumps(to_encode).encode()
    ).decode().rstrip('=')
    
    # Подпись
    signature_input = f"{header_encoded}.{payload_encoded}"
    signature = hashlib.sha256(
        f"{signature_input}{settings.secret_key}".encode()
    ).hexdigest()[:43]
    
    signature_encoded = base64.urlsafe_b64encode(
        signature.encode()
    ).decode().rstrip('=')
    
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
        # Декодируем payload
        payload_json = base64.urlsafe_b64decode(parts[1] + '=' * (4 - len(parts[1]) % 4))
        payload = json.loads(payload_json)
        
        # Проверяем срок действия
        if 'exp' in payload:
            exp_time = datetime.fromtimestamp(payload['exp'])
            if exp_time < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired"
                )
        
        return payload
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}"
        )