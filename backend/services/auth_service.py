import jwt
import bcrypt
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, Header
import os
import uuid

SECRET_KEY = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

class AuthService:
    def __init__(self, db):
        self.db = db
    
    async def signup(self, email: str, password: str, name: str):
        # Check if user exists
        existing_user = await self.db.users.find_one({"email": email})
        if existing_user:
            raise ValueError("Email already registered")
        
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Create user
        user_id = str(uuid.uuid4())
        user_doc = {
            "id": user_id,
            "email": email,
            "password_hash": hashed_password.decode('utf-8'),
            "name": name,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await self.db.users.insert_one(user_doc)
        
        # Create initial credit balance (50 free credits)
        await self.db.credit_balances.insert_one({
            "user_id": user_id,
            "balance": 50,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Create ledger entry
        await self.db.credit_ledger.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "delta": 50,
            "reason": "signup_bonus",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Generate token
        token = self._create_access_token({"sub": user_id, "email": email})
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {"id": user_id, "email": email, "name": name}
        }
    
    async def login(self, email: str, password: str):
        # Find user
        user = await self.db.users.find_one({"email": email})
        if not user:
            raise ValueError("Invalid email or password")
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            raise ValueError("Invalid email or password")
        
        # Generate token
        token = self._create_access_token({"sub": user['id'], "email": email})
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {"id": user['id'], "email": email, "name": user['name']}
        }
    
    def _create_access_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    async def verify_token(self, token: str):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            user = await self.db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            
            return user
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")


# Dependency for protected routes
async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    
    # Get db from app state (we'll need to inject this)
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    auth_service = AuthService(db)
    user = await auth_service.verify_token(token)
    return user
