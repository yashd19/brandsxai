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
    'connect_timeout': 2,
    'read_timeout': 10,
    'write_timeout': 10,
    'autocommit': True
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def try_mysql_connection():
    """Try to get MySQL connection, returns None if fails"""
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        return conn
    except pymysql.Error as e:
        logger.warning(f"MySQL connection failed: {e}")
        return None

def init_mysql_tables(connection):
    """Initialize all MySQL tables"""
    try:
        with connection.cursor() as cursor:
            # Admins table (MadOver AI employees)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS brandsxai_admins (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) NOT NULL UNIQUE,
                    email VARCHAR(255),
                    password_hash VARCHAR(255) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_admin_username (username)
                )
            """)
            
            # Brands table (Customers)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS brandsxai_brands (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Features table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS brandsxai_features (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    icon VARCHAR(50),
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Feature Pages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS brandsxai_feature_pages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    feature_id INT NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    icon VARCHAR(50),
                    route VARCHAR(100) NOT NULL,
                    display_order INT DEFAULT 0,
                    FOREIGN KEY (feature_id) REFERENCES brandsxai_features(id) ON DELETE CASCADE
                )
            """)
            
            # Users table (Brand users)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS brandsxai_users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) NOT NULL UNIQUE,
                    email VARCHAR(255),
                    password_hash VARCHAR(255) NOT NULL,
                    brand_id INT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP NULL,
                    FOREIGN KEY (brand_id) REFERENCES brandsxai_brands(id) ON DELETE SET NULL,
                    INDEX idx_user_username (username),
                    INDEX idx_user_brand (brand_id)
                )
            """)
            
            # User Features mapping
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS brandsxai_user_features (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    feature_id INT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES brandsxai_users(id) ON DELETE CASCADE,
                    FOREIGN KEY (feature_id) REFERENCES brandsxai_features(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_user_feature (user_id, feature_id)
                )
            """)
            
            # Campaigns table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS brandsxai_campaigns (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    brand_id INT NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    start_date DATE,
                    end_date DATE,
                    target_audience VARCHAR(255),
                    call_script TEXT,
                    status ENUM('draft', 'active', 'paused', 'completed') DEFAULT 'draft',
                    created_by INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (brand_id) REFERENCES brandsxai_brands(id) ON DELETE CASCADE,
                    INDEX idx_campaign_brand (brand_id),
                    INDEX idx_campaign_status (status)
                )
            """)
            
            # Opportunities/Leads table for campaigns
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS brandsxai_opportunities (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    campaign_id INT NOT NULL,
                    brand_id INT NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    phone VARCHAR(50),
                    email VARCHAR(255),
                    business_name VARCHAR(255),
                    opportunity_value DECIMAL(10, 2) DEFAULT 0.00,
                    stage ENUM('dialing', 'interested', 'not_interested', 'callback', 'store_visit', 'invalid_number') DEFAULT 'dialing',
                    notes TEXT,
                    last_called_at TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (campaign_id) REFERENCES brandsxai_campaigns(id) ON DELETE CASCADE,
                    FOREIGN KEY (brand_id) REFERENCES brandsxai_brands(id) ON DELETE CASCADE,
                    INDEX idx_opp_campaign (campaign_id),
                    INDEX idx_opp_stage (stage)
                )
            """)
            
            # Leads table (for contact form)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS brandsxai_leads (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    company VARCHAR(255),
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_lead_email (email)
                )
            """)
            
            # Insert default admin if not exists
            cursor.execute("SELECT id FROM brandsxai_admins WHERE username = 'madoveradmin'")
            if not cursor.fetchone():
                password_hash = bcrypt.hashpw('admin@123'.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')
                cursor.execute(
                    "INSERT INTO brandsxai_admins (username, email, password_hash) VALUES (%s, %s, %s)",
                    ('madoveradmin', 'admin@madoverai.com', password_hash)
                )
                logger.info("Created default MadOver AI admin")
            
            # Insert default features if not exists
            cursor.execute("SELECT id FROM brandsxai_features WHERE name = 'Voice AI'")
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO brandsxai_features (name, icon, description) VALUES (%s, %s, %s)",
                    ('Voice AI', 'Phone', 'Voice AI solutions for customer interactions')
                )
                voice_ai_id = cursor.lastrowid
                
                # Insert Voice AI pages
                cursor.execute(
                    "INSERT INTO brandsxai_feature_pages (feature_id, name, icon, route, display_order) VALUES (%s, %s, %s, %s, %s)",
                    (voice_ai_id, 'Contacts', 'Users', '/dashboard/voice-ai/contacts', 1)
                )
                cursor.execute(
                    "INSERT INTO brandsxai_feature_pages (feature_id, name, icon, route, display_order) VALUES (%s, %s, %s, %s, %s)",
                    (voice_ai_id, 'Dashboards', 'LayoutDashboard', '/dashboard/voice-ai/dashboards', 2)
                )
                cursor.execute(
                    "INSERT INTO brandsxai_feature_pages (feature_id, name, icon, route, display_order) VALUES (%s, %s, %s, %s, %s)",
                    (voice_ai_id, 'Session', 'Clock', '/dashboard/voice-ai/session', 3)
                )
                cursor.execute(
                    "INSERT INTO brandsxai_feature_pages (feature_id, name, icon, route, display_order) VALUES (%s, %s, %s, %s, %s)",
                    (voice_ai_id, 'Campaign', 'Megaphone', '/dashboard/voice-ai/campaign', 4)
                )
                logger.info("Created Voice AI feature with pages")
            
            cursor.execute("SELECT id FROM brandsxai_features WHERE name = 'Claim Processing'")
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO brandsxai_features (name, icon, description) VALUES (%s, %s, %s)",
                    ('Claim Processing', 'FileCheck', 'AI-powered claim processing automation')
                )
                logger.info("Created Claim Processing feature")
            
            # Insert sample brands if not exists
            cursor.execute("SELECT id FROM brandsxai_brands WHERE name = 'Brand X'")
            if not cursor.fetchone():
                cursor.execute("INSERT INTO brandsxai_brands (name) VALUES (%s)", ('Brand X',))
                cursor.execute("INSERT INTO brandsxai_brands (name) VALUES (%s)", ('Brand Y',))
                logger.info("Created sample brands")
            
            connection.commit()
            logger.info("MySQL tables initialized successfully")
            return True
    except pymysql.Error as e:
        logger.error(f"MySQL table initialization error: {e}")
        return False

async def init_mongodb_collections():
    """Initialize MongoDB collections with default data"""
    try:
        # Create indexes
        await mongo_db.brandsxai_admins.create_index("username", unique=True)
        await mongo_db.brandsxai_users.create_index("username", unique=True)
        await mongo_db.brandsxai_brands.create_index("name", unique=True)
        await mongo_db.brandsxai_features.create_index("name", unique=True)
        
        # Default admin
        admin = await mongo_db.brandsxai_admins.find_one({"username": "madoveradmin"})
        if not admin:
            password_hash = bcrypt.hashpw('admin@123'.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')
            await mongo_db.brandsxai_admins.insert_one({
                "id": 1, "username": "madoveradmin", "email": "admin@madoverai.com",
                "password_hash": password_hash, "is_active": True, "created_at": datetime.now(timezone.utc).isoformat()
            })
        
        # Default features
        voice_ai = await mongo_db.brandsxai_features.find_one({"name": "Voice AI"})
        if not voice_ai:
            await mongo_db.brandsxai_features.insert_one({
                "id": 1, "name": "Voice AI", "icon": "Phone", "description": "Voice AI solutions",
                "pages": [
                    {"id": 1, "name": "Contacts", "icon": "Users", "route": "/dashboard/voice-ai/contacts", "display_order": 1},
                    {"id": 2, "name": "Dashboards", "icon": "LayoutDashboard", "route": "/dashboard/voice-ai/dashboards", "display_order": 2},
                    {"id": 3, "name": "Session", "icon": "Clock", "route": "/dashboard/voice-ai/session", "display_order": 3},
                    {"id": 4, "name": "Campaign", "icon": "Megaphone", "route": "/dashboard/voice-ai/campaign", "display_order": 4}
                ]
            })
        else:
            # Update existing Voice AI to add Campaign page if missing
            if not any(p.get('name') == 'Campaign' for p in voice_ai.get('pages', [])):
                pages = voice_ai.get('pages', [])
                pages.append({"id": 4, "name": "Campaign", "icon": "Megaphone", "route": "/dashboard/voice-ai/campaign", "display_order": 4})
                await mongo_db.brandsxai_features.update_one(
                    {"name": "Voice AI"},
                    {"$set": {"pages": pages}}
                )
        
        claim = await mongo_db.brandsxai_features.find_one({"name": "Claim Processing"})
        if not claim:
            await mongo_db.brandsxai_features.insert_one({
                "id": 2, "name": "Claim Processing", "icon": "FileCheck", "description": "AI claim processing", "pages": []
            })
        
        # Default brands
        brand_x = await mongo_db.brandsxai_brands.find_one({"name": "Brand X"})
        if not brand_x:
            await mongo_db.brandsxai_brands.insert_one({"id": 1, "name": "Brand X", "created_at": datetime.now(timezone.utc).isoformat()})
            await mongo_db.brandsxai_brands.insert_one({"id": 2, "name": "Brand Y", "created_at": datetime.now(timezone.utc).isoformat()})
        
        logger.info("MongoDB collections initialized")
    except Exception as e:
        logger.error(f"MongoDB initialization error: {e}")

# Create the main app
app = FastAPI(title="MadOver AI API", version="1.0.0")
api_router = APIRouter(prefix="/api")
security = HTTPBearer(auto_error=False)

# ==================== PYDANTIC MODELS ====================

class LoginRequest(BaseModel):
    username: str
    password: str

class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin: dict
    is_admin: bool = True

class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict
    brand: dict
    features: List[dict]
    is_admin: bool = False

class CreateUserRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    brand_id: int
    feature_ids: List[int]

class UpdateUserFeaturesRequest(BaseModel):
    feature_ids: List[int]

class CreateBrandRequest(BaseModel):
    name: str

class LeadCreate(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    message: Optional[str] = None

# ==================== JWT HELPERS ====================

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except:
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[dict]:
    if not credentials:
        return None
    return verify_token(credentials.credentials)

# ==================== ADMIN AUTH ====================

@api_router.post("/admin/login")
async def admin_login(request: LoginRequest):
    """MadOver AI Admin login"""
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                cursor.execute("SELECT * FROM brandsxai_admins WHERE username = %s AND is_active = TRUE", (request.username,))
                admin = cursor.fetchone()
                if admin and bcrypt.checkpw(request.password.encode('utf-8'), admin['password_hash'].encode('utf-8')):
                    token = create_access_token({"sub": str(admin['id']), "username": admin['username'], "type": "admin"})
                    return {"access_token": token, "token_type": "bearer", "admin": {"id": admin['id'], "username": admin['username']}, "is_admin": True, "db_source": "mysql"}
        except Exception as e:
            logger.warning(f"MySQL admin login error: {e}")
        finally:
            mysql_conn.close()
    
    # MongoDB fallback
    admin = await mongo_db.brandsxai_admins.find_one({"username": request.username, "is_active": True})
    if admin and bcrypt.checkpw(request.password.encode('utf-8'), admin['password_hash'].encode('utf-8')):
        token = create_access_token({"sub": str(admin.get('id', 1)), "username": admin['username'], "type": "admin"})
        return {"access_token": token, "token_type": "bearer", "admin": {"id": admin.get('id', 1), "username": admin['username']}, "is_admin": True, "db_source": "mongodb"}
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

# ==================== USER AUTH ====================

@api_router.post("/auth/login")
async def user_login(request: LoginRequest):
    """Brand user login"""
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                # Get user with brand
                cursor.execute("""
                    SELECT u.*, b.name as brand_name 
                    FROM brandsxai_users u 
                    LEFT JOIN brandsxai_brands b ON u.brand_id = b.id 
                    WHERE u.username = %s AND u.is_active = TRUE
                """, (request.username,))
                user = cursor.fetchone()
                
                if user and bcrypt.checkpw(request.password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                    # Get user features with pages
                    cursor.execute("""
                        SELECT f.*, GROUP_CONCAT(
                            CONCAT(fp.id, ':', fp.name, ':', fp.icon, ':', fp.route, ':', fp.display_order) 
                            ORDER BY fp.display_order
                        ) as pages
                        FROM brandsxai_user_features uf
                        JOIN brandsxai_features f ON uf.feature_id = f.id
                        LEFT JOIN brandsxai_feature_pages fp ON f.id = fp.feature_id
                        WHERE uf.user_id = %s
                        GROUP BY f.id
                    """, (user['id'],))
                    features_raw = cursor.fetchall()
                    
                    features = []
                    for f in features_raw:
                        feature = {"id": f['id'], "name": f['name'], "icon": f['icon'], "description": f['description'], "pages": []}
                        if f['pages']:
                            for p in f['pages'].split(','):
                                parts = p.split(':')
                                if len(parts) >= 5:
                                    feature['pages'].append({"id": int(parts[0]), "name": parts[1], "icon": parts[2], "route": parts[3], "display_order": int(parts[4])})
                        features.append(feature)
                    
                    # Update last login
                    cursor.execute("UPDATE brandsxai_users SET last_login = NOW() WHERE id = %s", (user['id'],))
                    mysql_conn.commit()
                    
                    token = create_access_token({
                        "sub": str(user['id']), "username": user['username'], "type": "user",
                        "brand_id": user['brand_id'], "brand_name": user['brand_name']
                    })
                    
                    return {
                        "access_token": token, "token_type": "bearer",
                        "user": {"id": user['id'], "username": user['username'], "email": user['email']},
                        "brand": {"id": user['brand_id'], "name": user['brand_name']},
                        "features": features, "is_admin": False, "db_source": "mysql"
                    }
        except Exception as e:
            logger.warning(f"MySQL user login error: {e}")
        finally:
            mysql_conn.close()
    
    # MongoDB fallback
    user = await mongo_db.brandsxai_users.find_one({"username": request.username, "is_active": True})
    if user and bcrypt.checkpw(request.password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        brand = await mongo_db.brandsxai_brands.find_one({"id": user.get('brand_id')})
        
        # Get features
        feature_ids = user.get('feature_ids', [])
        features = []
        async for f in mongo_db.brandsxai_features.find({"id": {"$in": feature_ids}}):
            features.append({"id": f['id'], "name": f['name'], "icon": f['icon'], "description": f.get('description', ''), "pages": f.get('pages', [])})
        
        await mongo_db.brandsxai_users.update_one({"_id": user['_id']}, {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}})
        
        token = create_access_token({
            "sub": str(user.get('id', 1)), "username": user['username'], "type": "user",
            "brand_id": user.get('brand_id'), "brand_name": brand['name'] if brand else None
        })
        
        return {
            "access_token": token, "token_type": "bearer",
            "user": {"id": user.get('id', 1), "username": user['username'], "email": user.get('email', '')},
            "brand": {"id": brand['id'], "name": brand['name']} if brand else None,
            "features": features, "is_admin": False, "db_source": "mongodb"
        }
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

# ==================== ADMIN: USER MANAGEMENT ====================

@api_router.post("/admin/users")
async def create_user(request: CreateUserRequest, current_user: dict = Depends(get_current_user)):
    """Create a new brand user (Admin only)"""
    if not current_user or current_user.get('type') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    password_hash = bcrypt.hashpw(request.password.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')
    
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                # Create user
                cursor.execute(
                    "INSERT INTO brandsxai_users (username, email, password_hash, brand_id) VALUES (%s, %s, %s, %s)",
                    (request.username, request.email, password_hash, request.brand_id)
                )
                user_id = cursor.lastrowid
                
                # Add feature access
                for feature_id in request.feature_ids:
                    cursor.execute(
                        "INSERT INTO brandsxai_user_features (user_id, feature_id) VALUES (%s, %s)",
                        (user_id, feature_id)
                    )
                
                mysql_conn.commit()
                return {"message": "User created", "user_id": user_id, "db_source": "mysql"}
        except pymysql.IntegrityError:
            raise HTTPException(status_code=400, detail="Username already exists")
        except Exception as e:
            logger.error(f"MySQL create user error: {e}")
        finally:
            mysql_conn.close()
    
    # MongoDB fallback
    existing = await mongo_db.brandsxai_users.find_one({"username": request.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    last_user = await mongo_db.brandsxai_users.find_one(sort=[("id", -1)])
    new_id = (last_user.get('id', 0) + 1) if last_user else 1
    
    await mongo_db.brandsxai_users.insert_one({
        "id": new_id, "username": request.username, "email": request.email,
        "password_hash": password_hash, "brand_id": request.brand_id,
        "feature_ids": request.feature_ids, "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "User created", "user_id": new_id, "db_source": "mongodb"}

@api_router.get("/admin/users")
async def get_all_users(current_user: dict = Depends(get_current_user)):
    """Get all users (Admin only)"""
    if not current_user or current_user.get('type') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                cursor.execute("""
                    SELECT u.id, u.username, u.email, u.is_active, u.created_at, u.last_login,
                           b.id as brand_id, b.name as brand_name,
                           GROUP_CONCAT(f.id) as feature_ids, GROUP_CONCAT(f.name) as feature_names
                    FROM brandsxai_users u
                    LEFT JOIN brandsxai_brands b ON u.brand_id = b.id
                    LEFT JOIN brandsxai_user_features uf ON u.id = uf.user_id
                    LEFT JOIN brandsxai_features f ON uf.feature_id = f.id
                    GROUP BY u.id
                    ORDER BY u.created_at DESC
                """)
                users = cursor.fetchall()
                
                result = []
                for u in users:
                    result.append({
                        "id": u['id'], "username": u['username'], "email": u['email'],
                        "is_active": u['is_active'], "created_at": u['created_at'], "last_login": u['last_login'],
                        "brand": {"id": u['brand_id'], "name": u['brand_name']} if u['brand_id'] else None,
                        "features": [{"id": int(fid), "name": fn} for fid, fn in zip(
                            (u['feature_ids'] or '').split(','), (u['feature_names'] or '').split(',')
                        ) if fid and fn]
                    })
                
                return {"users": result, "db_source": "mysql"}
        except Exception as e:
            logger.error(f"MySQL get users error: {e}")
        finally:
            mysql_conn.close()
    
    # MongoDB fallback
    users = []
    async for u in mongo_db.brandsxai_users.find({}, {"_id": 0, "password_hash": 0}):
        brand = None
        if u.get('brand_id'):
            brand = await mongo_db.brandsxai_brands.find_one({"id": u.get('brand_id')}, {"_id": 0})
        features = []
        for fid in u.get('feature_ids', []):
            f = await mongo_db.brandsxai_features.find_one({"id": fid}, {"_id": 0})
            if f:
                features.append({"id": f['id'], "name": f['name']})
        users.append({
            "id": u.get('id'),
            "username": u.get('username'),
            "email": u.get('email'),
            "is_active": u.get('is_active', True),
            "created_at": u.get('created_at'),
            "last_login": u.get('last_login'),
            "brand": {"id": brand['id'], "name": brand['name']} if brand else None,
            "features": features
        })
    
    logger.info(f"MongoDB: Found {len(users)} users")
    return {"users": users, "db_source": "mongodb"}

@api_router.put("/admin/users/{user_id}/features")
async def update_user_features(user_id: int, request: UpdateUserFeaturesRequest, current_user: dict = Depends(get_current_user)):
    """Update user's feature access (Admin only)"""
    if not current_user or current_user.get('type') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                # Remove existing features
                cursor.execute("DELETE FROM brandsxai_user_features WHERE user_id = %s", (user_id,))
                
                # Add new features
                for feature_id in request.feature_ids:
                    cursor.execute(
                        "INSERT INTO brandsxai_user_features (user_id, feature_id) VALUES (%s, %s)",
                        (user_id, feature_id)
                    )
                
                mysql_conn.commit()
                return {"message": "Features updated", "db_source": "mysql"}
        except Exception as e:
            logger.error(f"MySQL update features error: {e}")
        finally:
            mysql_conn.close()
    
    # MongoDB fallback
    await mongo_db.brandsxai_users.update_one(
        {"id": user_id},
        {"$set": {"feature_ids": request.feature_ids}}
    )
    return {"message": "Features updated", "db_source": "mongodb"}

@api_router.delete("/admin/users/{user_id}")
async def delete_user(user_id: int, current_user: dict = Depends(get_current_user)):
    """Delete/deactivate a user (Admin only)"""
    if not current_user or current_user.get('type') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                cursor.execute("UPDATE brandsxai_users SET is_active = FALSE WHERE id = %s", (user_id,))
                mysql_conn.commit()
                return {"message": "User deactivated", "db_source": "mysql"}
        except Exception as e:
            logger.error(f"MySQL delete user error: {e}")
        finally:
            mysql_conn.close()
    
    await mongo_db.brandsxai_users.update_one({"id": user_id}, {"$set": {"is_active": False}})
    return {"message": "User deactivated", "db_source": "mongodb"}

# ==================== ADMIN: BRAND MANAGEMENT ====================

@api_router.get("/admin/brands")
async def get_brands(current_user: dict = Depends(get_current_user)):
    """Get all brands (Admin only)"""
    if not current_user or current_user.get('type') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                cursor.execute("SELECT * FROM brandsxai_brands ORDER BY name")
                return {"brands": cursor.fetchall(), "db_source": "mysql"}
        except Exception as e:
            logger.error(f"MySQL get brands error: {e}")
        finally:
            mysql_conn.close()
    
    brands = await mongo_db.brandsxai_brands.find({}, {"_id": 0}).to_list(100)
    return {"brands": brands, "db_source": "mongodb"}

@api_router.post("/admin/brands")
async def create_brand(request: CreateBrandRequest, current_user: dict = Depends(get_current_user)):
    """Create a new brand (Admin only)"""
    if not current_user or current_user.get('type') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                cursor.execute("INSERT INTO brandsxai_brands (name) VALUES (%s)", (request.name,))
                mysql_conn.commit()
                return {"message": "Brand created", "brand_id": cursor.lastrowid, "db_source": "mysql"}
        except pymysql.IntegrityError:
            raise HTTPException(status_code=400, detail="Brand already exists")
        except Exception as e:
            logger.error(f"MySQL create brand error: {e}")
        finally:
            mysql_conn.close()
    
    existing = await mongo_db.brandsxai_brands.find_one({"name": request.name})
    if existing:
        raise HTTPException(status_code=400, detail="Brand already exists")
    
    last_brand = await mongo_db.brandsxai_brands.find_one(sort=[("id", -1)])
    new_id = (last_brand.get('id', 0) + 1) if last_brand else 1
    
    await mongo_db.brandsxai_brands.insert_one({
        "id": new_id, "name": request.name, "created_at": datetime.now(timezone.utc).isoformat()
    })
    return {"message": "Brand created", "brand_id": new_id, "db_source": "mongodb"}

# ==================== ADMIN: FEATURE MANAGEMENT ====================

@api_router.get("/admin/features")
async def get_features(current_user: dict = Depends(get_current_user)):
    """Get all features (Admin only)"""
    if not current_user or current_user.get('type') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                cursor.execute("SELECT * FROM brandsxai_features ORDER BY name")
                features = cursor.fetchall()
                
                for f in features:
                    cursor.execute("SELECT * FROM brandsxai_feature_pages WHERE feature_id = %s ORDER BY display_order", (f['id'],))
                    f['pages'] = cursor.fetchall()
                
                return {"features": features, "db_source": "mysql"}
        except Exception as e:
            logger.error(f"MySQL get features error: {e}")
        finally:
            mysql_conn.close()
    
    features = await mongo_db.brandsxai_features.find({}, {"_id": 0}).to_list(100)
    return {"features": features, "db_source": "mongodb"}

# ==================== LEADS ====================

@api_router.post("/leads")
async def create_lead(lead: LeadCreate):
    """Create lead from contact form"""
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO brandsxai_leads (name, email, company, message) VALUES (%s, %s, %s, %s)",
                    (lead.name, lead.email, lead.company, lead.message)
                )
                mysql_conn.commit()
                return {"message": "Lead created", "id": cursor.lastrowid, "db_source": "mysql"}
        except Exception as e:
            logger.error(f"MySQL create lead error: {e}")
        finally:
            mysql_conn.close()
    
    last_lead = await mongo_db.brandsxai_leads.find_one(sort=[("id", -1)])
    new_id = (last_lead.get('id', 0) + 1) if last_lead else 1
    
    await mongo_db.brandsxai_leads.insert_one({
        "id": new_id, "name": lead.name, "email": lead.email, "company": lead.company,
        "message": lead.message, "created_at": datetime.now(timezone.utc)
    })
    return {"message": "Lead created", "id": new_id, "db_source": "mongodb"}

# ==================== CAMPAIGNS ====================

class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    target_audience: Optional[str] = None
    call_script: Optional[str] = None

class OpportunityCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    business_name: Optional[str] = None
    opportunity_value: float = 0.0
    notes: Optional[str] = None

class OpportunityStageUpdate(BaseModel):
    stage: str

@api_router.get("/campaigns")
async def get_campaigns(current_user: dict = Depends(get_current_user)):
    """Get all campaigns for the user's brand"""
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    
    brand_id = current_user.get('brand_id')
    if not brand_id:
        raise HTTPException(status_code=400, detail="User has no brand assigned")
    
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                cursor.execute("""
                    SELECT c.*, 
                           COUNT(o.id) as total_opportunities,
                           COALESCE(SUM(o.opportunity_value), 0) as total_value
                    FROM brandsxai_campaigns c
                    LEFT JOIN brandsxai_opportunities o ON c.id = o.campaign_id
                    WHERE c.brand_id = %s
                    GROUP BY c.id
                    ORDER BY c.created_at DESC
                """, (brand_id,))
                campaigns = cursor.fetchall()
                return {"campaigns": campaigns, "db_source": "mysql"}
        except Exception as e:
            logger.error(f"MySQL get campaigns error: {e}")
        finally:
            mysql_conn.close()
    
    # MongoDB fallback
    campaigns = await mongo_db.brandsxai_campaigns.find(
        {"brand_id": brand_id}, {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Add opportunity stats
    for c in campaigns:
        opps = await mongo_db.brandsxai_opportunities.find({"campaign_id": c['id']}, {"_id": 0}).to_list(1000)
        c['total_opportunities'] = len(opps)
        c['total_value'] = sum(o.get('opportunity_value', 0) for o in opps)
    
    return {"campaigns": campaigns, "db_source": "mongodb"}

@api_router.post("/campaigns")
async def create_campaign(campaign: CampaignCreate, current_user: dict = Depends(get_current_user)):
    """Create a new campaign"""
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    
    brand_id = current_user.get('brand_id')
    user_id = int(current_user.get('sub'))
    
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO brandsxai_campaigns 
                    (brand_id, name, description, start_date, end_date, target_audience, call_script, created_by, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'active')
                """, (brand_id, campaign.name, campaign.description, campaign.start_date, 
                      campaign.end_date, campaign.target_audience, campaign.call_script, user_id))
                mysql_conn.commit()
                campaign_id = cursor.lastrowid
                
                cursor.execute("SELECT * FROM brandsxai_campaigns WHERE id = %s", (campaign_id,))
                result = cursor.fetchone()
                return {"campaign": result, "db_source": "mysql"}
        except Exception as e:
            logger.error(f"MySQL create campaign error: {e}")
        finally:
            mysql_conn.close()
    
    # MongoDB fallback
    last_campaign = await mongo_db.brandsxai_campaigns.find_one(sort=[("id", -1)])
    new_id = (last_campaign.get('id', 0) + 1) if last_campaign else 1
    
    new_campaign = {
        "id": new_id,
        "brand_id": brand_id,
        "name": campaign.name,
        "description": campaign.description,
        "start_date": campaign.start_date,
        "end_date": campaign.end_date,
        "target_audience": campaign.target_audience,
        "call_script": campaign.call_script,
        "status": "active",
        "created_by": user_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await mongo_db.brandsxai_campaigns.insert_one(new_campaign)
    new_campaign.pop('_id', None)
    
    return {"campaign": new_campaign, "db_source": "mongodb"}

@api_router.get("/campaigns/{campaign_id}")
async def get_campaign(campaign_id: int, current_user: dict = Depends(get_current_user)):
    """Get campaign details with opportunities"""
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    
    brand_id = current_user.get('brand_id')
    
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                cursor.execute("SELECT * FROM brandsxai_campaigns WHERE id = %s AND brand_id = %s", (campaign_id, brand_id))
                campaign = cursor.fetchone()
                if not campaign:
                    raise HTTPException(status_code=404, detail="Campaign not found")
                
                cursor.execute("SELECT * FROM brandsxai_opportunities WHERE campaign_id = %s ORDER BY created_at DESC", (campaign_id,))
                opportunities = cursor.fetchall()
                
                # Group by stage
                stages = {}
                for stage in ['dialing', 'interested', 'not_interested', 'callback', 'store_visit', 'invalid_number']:
                    stage_opps = [o for o in opportunities if o['stage'] == stage]
                    stages[stage] = {
                        'opportunities': stage_opps,
                        'count': len(stage_opps),
                        'total_value': sum(float(o['opportunity_value'] or 0) for o in stage_opps)
                    }
                
                return {"campaign": campaign, "stages": stages, "db_source": "mysql"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"MySQL get campaign error: {e}")
        finally:
            mysql_conn.close()
    
    # MongoDB fallback
    campaign = await mongo_db.brandsxai_campaigns.find_one({"id": campaign_id, "brand_id": brand_id}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    opportunities = await mongo_db.brandsxai_opportunities.find({"campaign_id": campaign_id}, {"_id": 0}).to_list(1000)
    
    stages = {}
    for stage in ['dialing', 'interested', 'not_interested', 'callback', 'store_visit', 'invalid_number']:
        stage_opps = [o for o in opportunities if o.get('stage') == stage]
        stages[stage] = {
            'opportunities': stage_opps,
            'count': len(stage_opps),
            'total_value': sum(o.get('opportunity_value', 0) for o in stage_opps)
        }
    
    return {"campaign": campaign, "stages": stages, "db_source": "mongodb"}

@api_router.post("/campaigns/{campaign_id}/opportunities")
async def create_opportunity(campaign_id: int, opportunity: OpportunityCreate, current_user: dict = Depends(get_current_user)):
    """Add an opportunity to a campaign"""
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    
    brand_id = current_user.get('brand_id')
    
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                # Verify campaign belongs to user's brand
                cursor.execute("SELECT id FROM brandsxai_campaigns WHERE id = %s AND brand_id = %s", (campaign_id, brand_id))
                if not cursor.fetchone():
                    raise HTTPException(status_code=404, detail="Campaign not found")
                
                cursor.execute("""
                    INSERT INTO brandsxai_opportunities 
                    (campaign_id, brand_id, name, phone, email, business_name, opportunity_value, notes, stage)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'dialing')
                """, (campaign_id, brand_id, opportunity.name, opportunity.phone, opportunity.email,
                      opportunity.business_name, opportunity.opportunity_value, opportunity.notes))
                mysql_conn.commit()
                
                opp_id = cursor.lastrowid
                cursor.execute("SELECT * FROM brandsxai_opportunities WHERE id = %s", (opp_id,))
                result = cursor.fetchone()
                return {"opportunity": result, "db_source": "mysql"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"MySQL create opportunity error: {e}")
        finally:
            mysql_conn.close()
    
    # MongoDB fallback
    campaign = await mongo_db.brandsxai_campaigns.find_one({"id": campaign_id, "brand_id": brand_id})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    last_opp = await mongo_db.brandsxai_opportunities.find_one(sort=[("id", -1)])
    new_id = (last_opp.get('id', 0) + 1) if last_opp else 1
    
    new_opp = {
        "id": new_id,
        "campaign_id": campaign_id,
        "brand_id": brand_id,
        "name": opportunity.name,
        "phone": opportunity.phone,
        "email": opportunity.email,
        "business_name": opportunity.business_name,
        "opportunity_value": opportunity.opportunity_value,
        "notes": opportunity.notes,
        "stage": "dialing",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await mongo_db.brandsxai_opportunities.insert_one(new_opp)
    new_opp.pop('_id', None)
    
    return {"opportunity": new_opp, "db_source": "mongodb"}

@api_router.put("/opportunities/{opportunity_id}/stage")
async def update_opportunity_stage(opportunity_id: int, update: OpportunityStageUpdate, current_user: dict = Depends(get_current_user)):
    """Update opportunity stage (for drag-drop in Kanban)"""
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    
    brand_id = current_user.get('brand_id')
    valid_stages = ['dialing', 'interested', 'not_interested', 'callback', 'store_visit', 'invalid_number']
    
    if update.stage not in valid_stages:
        raise HTTPException(status_code=400, detail=f"Invalid stage. Must be one of: {valid_stages}")
    
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE brandsxai_opportunities SET stage = %s, updated_at = NOW() WHERE id = %s AND brand_id = %s",
                    (update.stage, opportunity_id, brand_id)
                )
                mysql_conn.commit()
                
                if cursor.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Opportunity not found")
                
                cursor.execute("SELECT * FROM brandsxai_opportunities WHERE id = %s", (opportunity_id,))
                result = cursor.fetchone()
                return {"opportunity": result, "db_source": "mysql"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"MySQL update stage error: {e}")
        finally:
            mysql_conn.close()
    
    # MongoDB fallback
    result = await mongo_db.brandsxai_opportunities.update_one(
        {"id": opportunity_id, "brand_id": brand_id},
        {"$set": {"stage": update.stage, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    opp = await mongo_db.brandsxai_opportunities.find_one({"id": opportunity_id}, {"_id": 0})
    return {"opportunity": opp, "db_source": "mongodb"}

# ==================== UTILITY ====================

@api_router.get("/")
async def root():
    return {"message": "MadOver AI API", "version": "2.0.0"}

@api_router.get("/db-status")
async def db_status():
    mysql_status = try_mysql_connection() is not None
    return {"mysql_available": mysql_status, "mongodb_available": True, "primary_db": "mysql" if mysql_status else "mongodb"}

# Include router & middleware
app.include_router(api_router)
app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
async def startup_event():
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        init_mysql_tables(mysql_conn)
        mysql_conn.close()
    await init_mongodb_collections()
    logger.info("Database initialization complete")
