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

# MongoDB connection (fallback)
mongo_url = os.environ['MONGO_URL']
mongo_client = AsyncIOMotorClient(mongo_url)
mongo_db = mongo_client[os.environ['DB_NAME']]

# MySQL connection configuration
MYSQL_CONFIG = {
    'host': os.environ.get('MYSQL_HOST', 'madoverai.cdam6io6a2o3.eu-north-1.rds.amazonaws.com'),
    'port': int(os.environ.get('MYSQL_PORT', 13306)),
    'user': os.environ.get('MYSQL_USER', 'admin'),
    'password': os.environ.get('MYSQL_PASSWORD', 'm94IHMwmhb1SHItnl3zP'),
    'database': os.environ.get('MYSQL_DATABASE', 'madoverai'),
    'charset': 'utf8mb4',
    'cursorclass': DictCursor,
    'connect_timeout': 5,
    'read_timeout': 30,
    'write_timeout': 30,
    'autocommit': True
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def try_mysql_connection():
    """Try to get MySQL connection, returns None if fails"""
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        return conn
    except pymysql.Error as e:
        logger.warning(f"MySQL connection failed, using MongoDB fallback: {e}")
        return None

def init_mysql_tables(connection):
    """Initialize MySQL tables"""
    try:
        with connection.cursor() as cursor:
            # Create users table
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
            
            # Create leads table
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
            
            # Create default admin user if not exists
            cursor.execute("SELECT id FROM brandsxai_users WHERE username = 'admin'")
            if not cursor.fetchone():
                password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')
                cursor.execute(
                    "INSERT INTO brandsxai_users (username, email, password_hash) VALUES (%s, %s, %s)",
                    ('admin', 'admin@madoverai.com', password_hash)
                )
            
            connection.commit()
            logger.info("MySQL tables initialized successfully")
            return True
    except pymysql.Error as e:
        logger.error(f"MySQL table initialization error: {e}")
        return False

async def init_mongodb_collections():
    """Initialize MongoDB collections with default data"""
    try:
        # Check if admin user exists in MongoDB
        admin = await mongo_db.brandsxai_users.find_one({"username": "admin"})
        if not admin:
            password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')
            await mongo_db.brandsxai_users.insert_one({
                "id": 1,
                "username": "admin",
                "email": "admin@madoverai.com",
                "password_hash": password_hash,
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            logger.info("MongoDB: Created default admin user")
        
        # Create indexes
        await mongo_db.brandsxai_users.create_index("username", unique=True)
        await mongo_db.brandsxai_leads.create_index("email")
        logger.info("MongoDB collections initialized successfully")
    except Exception as e:
        logger.error(f"MongoDB initialization error: {e}")

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

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict
    db_source: str = "mysql"  # Indicates which DB was used

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    is_active: bool

class LeadCreate(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    message: Optional[str] = None

class LeadResponse(BaseModel):
    id: int
    name: str
    email: str
    company: Optional[str] = None
    message: Optional[str] = None
    created_at: datetime
    db_source: str = "mysql"

# JWT Helper Functions
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[dict]:
    if not credentials:
        return None
    payload = verify_token(credentials.credentials)
    return payload

# ==================== AUTH ENDPOINTS ====================

@api_router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate user - tries MySQL first, falls back to MongoDB"""
    
    # Try MySQL first
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, username, email, password_hash, is_active FROM brandsxai_users WHERE username = %s",
                    (request.username,)
                )
                user = cursor.fetchone()
                
                if user:
                    if not user['is_active']:
                        raise HTTPException(status_code=401, detail="Account is disabled")
                    
                    if bcrypt.checkpw(request.password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                        # Update last login
                        cursor.execute("UPDATE brandsxai_users SET last_login = NOW() WHERE id = %s", (user['id'],))
                        mysql_conn.commit()
                        
                        token_data = {"sub": str(user['id']), "username": user['username'], "email": user['email']}
                        access_token = create_access_token(token_data)
                        
                        logger.info(f"User {request.username} logged in via MySQL")
                        return LoginResponse(
                            access_token=access_token,
                            user={"id": user['id'], "username": user['username'], "email": user['email']},
                            db_source="mysql"
                        )
                    else:
                        raise HTTPException(status_code=401, detail="Invalid username or password")
                # User not found in MySQL, will try MongoDB
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"MySQL login error, trying MongoDB: {e}")
        finally:
            mysql_conn.close()
    
    # MongoDB fallback
    logger.info(f"Trying MongoDB fallback for user: {request.username}")
    user = await mongo_db.brandsxai_users.find_one({"username": request.username})
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    if not user.get('is_active', True):
        raise HTTPException(status_code=401, detail="Account is disabled")
    
    if not bcrypt.checkpw(request.password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Update last login
    await mongo_db.brandsxai_users.update_one(
        {"username": request.username},
        {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}}
    )
    
    token_data = {"sub": str(user.get('id', 1)), "username": user['username'], "email": user.get('email', '')}
    access_token = create_access_token(token_data)
    
    logger.info(f"User {request.username} logged in via MongoDB (fallback)")
    return LoginResponse(
        access_token=access_token,
        user={"id": user.get('id', 1), "username": user['username'], "email": user.get('email', '')},
        db_source="mongodb"
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user - tries MySQL first, falls back to MongoDB"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Try MySQL first
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, username, email, is_active FROM brandsxai_users WHERE id = %s",
                    (current_user['sub'],)
                )
                user = cursor.fetchone()
                if user:
                    return UserResponse(**user)
        except Exception as e:
            logger.warning(f"MySQL get_me error, trying MongoDB: {e}")
        finally:
            mysql_conn.close()
    
    # MongoDB fallback
    user = await mongo_db.brandsxai_users.find_one({"username": current_user['username']})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user.get('id', 1),
        username=user['username'],
        email=user.get('email', ''),
        is_active=user.get('is_active', True)
    )

# ==================== LEAD ENDPOINTS ====================

@api_router.post("/leads")
async def create_lead(lead: LeadCreate):
    """Create lead - tries MySQL first, falls back to MongoDB"""
    
    # Try MySQL first
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO brandsxai_leads (name, email, company, message) VALUES (%s, %s, %s, %s)",
                    (lead.name, lead.email, lead.company, lead.message)
                )
                mysql_conn.commit()
                
                lead_id = cursor.lastrowid
                cursor.execute("SELECT * FROM brandsxai_leads WHERE id = %s", (lead_id,))
                result = cursor.fetchone()
                
                logger.info(f"Lead created in MySQL: {lead.email}")
                return {**result, "db_source": "mysql"}
        except Exception as e:
            logger.warning(f"MySQL create_lead error, trying MongoDB: {e}")
        finally:
            mysql_conn.close()
    
    # MongoDB fallback
    # Get next ID
    last_lead = await mongo_db.brandsxai_leads.find_one(sort=[("id", -1)])
    next_id = (last_lead.get('id', 0) + 1) if last_lead else 1
    
    lead_doc = {
        "id": next_id,
        "name": lead.name,
        "email": lead.email,
        "company": lead.company,
        "message": lead.message,
        "created_at": datetime.now(timezone.utc)
    }
    await mongo_db.brandsxai_leads.insert_one(lead_doc)
    
    logger.info(f"Lead created in MongoDB (fallback): {lead.email}")
    return {
        "id": next_id,
        "name": lead.name,
        "email": lead.email,
        "company": lead.company,
        "message": lead.message,
        "created_at": lead_doc['created_at'],
        "db_source": "mongodb"
    }

@api_router.get("/leads")
async def get_leads(current_user: dict = Depends(get_current_user)):
    """Get all leads - tries MySQL first, falls back to MongoDB"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Try MySQL first
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                cursor.execute("SELECT * FROM brandsxai_leads ORDER BY created_at DESC")
                results = cursor.fetchall()
                logger.info(f"Fetched {len(results)} leads from MySQL")
                return {"leads": results, "db_source": "mysql", "count": len(results)}
        except Exception as e:
            logger.warning(f"MySQL get_leads error, trying MongoDB: {e}")
        finally:
            mysql_conn.close()
    
    # MongoDB fallback
    leads = await mongo_db.brandsxai_leads.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    logger.info(f"Fetched {len(leads)} leads from MongoDB (fallback)")
    return {"leads": leads, "db_source": "mongodb", "count": len(leads)}

# ==================== UTILITY ENDPOINTS ====================

@api_router.get("/")
async def root():
    return {"message": "MadOver AI API", "version": "1.0.0"}

@api_router.get("/db-status")
async def db_status():
    """Check database connection status"""
    mysql_status = False
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        mysql_status = True
        mysql_conn.close()
    
    return {
        "mysql_available": mysql_status,
        "mongodb_available": True,
        "primary_db": "mysql" if mysql_status else "mongodb",
        "mysql_config": {
            "host": MYSQL_CONFIG['host'],
            "port": MYSQL_CONFIG['port']
        }
    }

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await mongo_db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await mongo_db.status_checks.find({}, {"_id": 0}).to_list(1000)
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    return status_checks

# Include router
app.include_router(api_router)

# CORS
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
    # Try MySQL first
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        init_mysql_tables(mysql_conn)
        mysql_conn.close()
        logger.info("Primary database: MySQL")
    else:
        logger.info("MySQL unavailable, using MongoDB as primary")
    
    # Always initialize MongoDB as fallback
    await init_mongodb_collections()
    logger.info("MongoDB fallback ready")
