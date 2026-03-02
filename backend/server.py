from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import pymysql
from pymysql.cursors import DictCursor
import bcrypt
import jwt

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'madoverai-secret-key-2024-secure')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# MySQL connection configuration with connection pooling settings
MYSQL_CONFIG = {
    'host': os.environ.get('MYSQL_HOST', 'madoverai.cdam6io6a2o3.eu-north-1.rds.amazonaws.com'),
    'port': int(os.environ.get('MYSQL_PORT', 13306)),
    'user': os.environ.get('MYSQL_USER', 'admin'),
    'password': os.environ.get('MYSQL_PASSWORD', 'm94IHMwmhb1SHItnl3zP'),
    'database': os.environ.get('MYSQL_DATABASE', 'madoverai'),
    'charset': 'utf8mb4',
    'cursorclass': DictCursor,
    'connect_timeout': 10,
    'read_timeout': 30,
    'write_timeout': 30,
    'autocommit': True
}

# MySQL connection status
mysql_available = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_mysql_connection():
    """Get MySQL database connection"""
    global mysql_available
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        mysql_available = True
        return conn
    except pymysql.Error as e:
        mysql_available = False
        logger.error(f"MySQL connection error: {e}")
        raise e

def init_mysql_database():
    """Initialize MySQL database with required tables"""
    global mysql_available
    try:
        connection = get_mysql_connection()
        try:
            with connection.cursor() as cursor:
                # Create users table with brandsxai prefix
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS brandsxai_users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        username VARCHAR(100) NOT NULL UNIQUE,
                        email VARCHAR(255),
                        password_hash VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        INDEX idx_username (username)
                    )
                """)
                
                # Create leads table with brandsxai prefix
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS brandsxai_leads (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        email VARCHAR(255) NOT NULL,
                        company VARCHAR(255),
                        message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_email (email)
                    )
                """)
                
                # Create dummy admin user if not exists
                cursor.execute("SELECT id FROM brandsxai_users WHERE username = 'admin'")
                if not cursor.fetchone():
                    # Hash password with bcrypt (cost factor 12 for security + performance)
                    password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')
                    cursor.execute(
                        "INSERT INTO brandsxai_users (username, email, password_hash) VALUES (%s, %s, %s)",
                        ('admin', 'admin@madoverai.com', password_hash)
                    )
                    logger.info("Created default admin user")
                
                connection.commit()
            mysql_available = True
            logger.info("MySQL tables initialized successfully")
        finally:
            connection.close()
    except pymysql.Error as e:
        mysql_available = False
        logger.error(f"MySQL initialization error: {e}")
        raise e

# Create the main app
app = FastAPI(title="MadOver AI API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer(auto_error=False)

# Pydantic Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

# Auth Models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    is_active: bool

# Lead Models
class LeadCreate(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    message: Optional[str] = None

class Lead(BaseModel):
    id: int
    name: str
    email: str
    company: Optional[str] = None
    message: Optional[str] = None
    created_at: datetime

# JWT Helper Functions
def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[dict]:
    """Get current user from JWT token"""
    if not credentials:
        return None
    
    payload = verify_token(credentials.credentials)
    if not payload:
        return None
    
    return payload

# Auth Endpoints
@api_router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate user and return JWT token"""
    if not mysql_available:
        try:
            init_mysql_database()
        except Exception:
            raise HTTPException(status_code=503, detail="Database temporarily unavailable")
    
    try:
        connection = get_mysql_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, username, email, password_hash, is_active FROM brandsxai_users WHERE username = %s",
                    (request.username,)
                )
                user = cursor.fetchone()
                
                if not user:
                    raise HTTPException(status_code=401, detail="Invalid username or password")
                
                if not user['is_active']:
                    raise HTTPException(status_code=401, detail="Account is disabled")
                
                # Verify password
                if not bcrypt.checkpw(request.password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                    raise HTTPException(status_code=401, detail="Invalid username or password")
                
                # Update last login
                cursor.execute(
                    "UPDATE brandsxai_users SET last_login = NOW() WHERE id = %s",
                    (user['id'],)
                )
                connection.commit()
                
                # Create JWT token
                token_data = {
                    "sub": str(user['id']),
                    "username": user['username'],
                    "email": user['email']
                }
                access_token = create_access_token(token_data)
                
                return LoginResponse(
                    access_token=access_token,
                    user={
                        "id": user['id'],
                        "username": user['username'],
                        "email": user['email']
                    }
                )
        finally:
            connection.close()
    except pymysql.Error as e:
        logger.error(f"MySQL error during login: {e}")
        raise HTTPException(status_code=500, detail="Authentication service error")

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        connection = get_mysql_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, username, email, is_active FROM brandsxai_users WHERE id = %s",
                    (current_user['sub'],)
                )
                user = cursor.fetchone()
                if not user:
                    raise HTTPException(status_code=404, detail="User not found")
                return UserResponse(**user)
        finally:
            connection.close()
    except pymysql.Error as e:
        logger.error(f"MySQL error fetching user: {e}")
        raise HTTPException(status_code=500, detail="Database error")

# Basic Routes
@api_router.get("/")
async def root():
    return {"message": "MadOver AI API", "version": "1.0.0"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    return status_checks

# Lead Endpoints (MySQL with brandsxai prefix)
@api_router.post("/leads", response_model=Lead)
async def create_lead(lead: LeadCreate):
    """Create a new lead from contact form submission"""
    if not mysql_available:
        try:
            init_mysql_database()
        except Exception:
            raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again later.")
    
    try:
        connection = get_mysql_connection()
        try:
            with connection.cursor() as cursor:
                sql = """
                    INSERT INTO brandsxai_leads (name, email, company, message)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (lead.name, lead.email, lead.company, lead.message))
                connection.commit()
                
                lead_id = cursor.lastrowid
                cursor.execute("SELECT * FROM brandsxai_leads WHERE id = %s", (lead_id,))
                result = cursor.fetchone()
                
                return Lead(**result)
        finally:
            connection.close()
    except pymysql.Error as e:
        logger.error(f"MySQL error creating lead: {e}")
        raise HTTPException(status_code=500, detail="Failed to create lead. Database connection error.")

@api_router.get("/leads", response_model=List[Lead])
async def get_leads(current_user: dict = Depends(get_current_user)):
    """Get all leads (requires authentication)"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    if not mysql_available:
        try:
            init_mysql_database()
        except Exception:
            raise HTTPException(status_code=503, detail="Database temporarily unavailable.")
    
    try:
        connection = get_mysql_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM brandsxai_leads ORDER BY created_at DESC")
                results = cursor.fetchall()
                return [Lead(**row) for row in results]
        finally:
            connection.close()
    except pymysql.Error as e:
        logger.error(f"MySQL error fetching leads: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch leads")

@api_router.get("/mysql-status")
async def mysql_status():
    """Check MySQL connection status"""
    return {
        "mysql_available": mysql_available,
        "config_host": MYSQL_CONFIG['host'],
        "config_port": MYSQL_CONFIG['port']
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize databases on startup"""
    try:
        init_mysql_database()
        logger.info("MySQL database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize MySQL database: {str(e)}")
