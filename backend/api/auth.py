from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

# CONFIGURATION
# ---------------------------------------------------------
# 1. GO TO SUPABASE -> PROJECT SETTINGS -> API -> JWT SETTINGS
# 2. COPY "JWT SECRET" AND PASTE IT BELOW
SUPABASE_JWT_SECRET = "TLqIxl0ELre/W4sbm8yfsxIv7PGuWkpg3078dpJSbb8DNuqQPyEunasZjB+x/ZV2pRtV11PeJKeFLzDOEF0JoA=="
ALGORITHM = "HS256"
# ---------------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Validates the Supabase JWT token sent by the frontend.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the token using the Secret
        payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=[ALGORITHM], audience="authenticated")
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        
        if user_id is None:
            raise credentials_exception
            
        return {"user_id": user_id, "email": email}
        
    except JWTError:
        raise credentials_exception