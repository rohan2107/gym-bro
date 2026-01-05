from fastapi import Header, HTTPException, status


def get_user_id(x_user_id: int = Header(..., alias="X-User-Id")) -> int:
    """Lightweight user scoping via required X-User-Id header."""
    if x_user_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid X-User-Id")
    return x_user_id
