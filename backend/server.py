from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument
import os
import re
import asyncio
import logging
import json
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

# MySQL availability cache to avoid repeated connection attempts
_mysql_available = None
_mysql_check_time = None
MYSQL_RETRY_INTERVAL = 60  # Retry MySQL check every 60 seconds

def _probe_mysql():
    """Blocking MySQL reachability probe. Runs ONLY in a background thread — never on the event loop."""
    global _mysql_available, _mysql_check_time
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        conn.close()
        if _mysql_available is not True:
            logger.info("MySQL reachable — MySQL-first mode active")
        _mysql_available = True
    except Exception as e:
        if _mysql_available is not False:
            logger.warning(f"MySQL unreachable, using MongoDB: {e}")
        _mysql_available = False
    _mysql_check_time = datetime.now(timezone.utc)

def _mysql_prober_loop():
    import time as _time
    while True:
        _probe_mysql()
        _time.sleep(MYSQL_RETRY_INTERVAL)

def start_mysql_prober():
    import threading
    t = threading.Thread(target=_mysql_prober_loop, daemon=True, name="mysql-prober")
    t.start()

def try_mysql_connection():
    """Get a MySQL connection WITHOUT ever blocking the async event loop.
    MySQL remains first preference: we connect only when the background probe reports it reachable;
    otherwise return None immediately so callers fall back to MongoDB."""
    global _mysql_available
    if _mysql_available is not True:
        return None
    try:
        return pymysql.connect(**MYSQL_CONFIG)
    except pymysql.Error as e:
        _mysql_available = False
        logger.warning(f"MySQL connection failed: {e}")
        return None

def init_mysql_tables(connection):
    """Initialize all MySQL tables"""
    try:
        with connection.cursor() as cursor:
            # Admins table (BrandsXAI employees)
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
            
            # Claim Processing Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS brandsxai_claim_sessions (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id INT NOT NULL,
                    brand_id INT NOT NULL,
                    title VARCHAR(255) DEFAULT 'New Claim Session',
                    status ENUM('active', 'completed', 'archived') DEFAULT 'active',
                    extracted_codes JSON,
                    source_document LONGTEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_claim_user (user_id),
                    INDEX idx_claim_brand (brand_id),
                    INDEX idx_claim_status (status)
                )
            """)
            
            # Claim Processing Messages table (chat history)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS brandsxai_claim_messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id VARCHAR(36) NOT NULL,
                    role ENUM('user', 'assistant', 'system') NOT NULL,
                    content TEXT NOT NULL,
                    file_info JSON,
                    codes_extracted JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_msg_session (session_id)
                )
            """)

            # Migrate: existing sessions predate source_document. Isolated so a failed
            # ALTER (e.g. insufficient grants) cannot abort the rest of this function.
            try:
                cursor.execute("""
                    SELECT COUNT(*) AS c FROM information_schema.columns
                    WHERE table_schema = DATABASE()
                      AND table_name = 'brandsxai_claim_sessions'
                      AND column_name = 'source_document'
                """)
                if not (cursor.fetchone() or {}).get('c'):
                    cursor.execute("""
                        ALTER TABLE brandsxai_claim_sessions
                        ADD COLUMN source_document LONGTEXT AFTER extracted_codes
                    """)
                    logger.info("Migrated: added source_document to brandsxai_claim_sessions")
            except Exception as e:
                logger.error(f"source_document migration skipped: {e}")
            
            # Insert default admin if not exists
            cursor.execute("SELECT id FROM brandsxai_admins WHERE username = 'madoveradmin'")
            if not cursor.fetchone():
                password_hash = bcrypt.hashpw('admin@123'.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')
                cursor.execute(
                    "INSERT INTO brandsxai_admins (username, email, password_hash) VALUES (%s, %s, %s)",
                    ('madoveradmin', 'admin@madoverai.com', password_hash)
                )
                logger.info("Created default BrandsXAI admin")
            
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
            claim_feature = cursor.fetchone()
            if not claim_feature:
                cursor.execute(
                    "INSERT INTO brandsxai_features (name, icon, description) VALUES (%s, %s, %s)",
                    ('Claim Processing', 'FileCheck', 'AI-powered medical claim processing and ICD-10 code extraction')
                )
                claim_id = cursor.lastrowid
                cursor.execute(
                    "INSERT INTO brandsxai_feature_pages (feature_id, name, icon, route, display_order) VALUES (%s, %s, %s, %s, %s)",
                    (claim_id, 'Code Extractor', 'FileSearch', '/dashboard/claim-processing/extractor', 1)
                )
                logger.info("Created Claim Processing feature with pages")
            else:
                # Migrate: ensure Code Extractor page exists for existing Claim Processing feature
                claim_id = claim_feature['id']
                cursor.execute(
                    "SELECT id FROM brandsxai_feature_pages WHERE feature_id = %s AND name = 'Code Extractor'",
                    (claim_id,)
                )
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO brandsxai_feature_pages (feature_id, name, icon, route, display_order) VALUES (%s, %s, %s, %s, %s)",
                        (claim_id, 'Code Extractor', 'FileSearch', '/dashboard/claim-processing/extractor', 1)
                    )
                    logger.info("Migrated: added Code Extractor page to existing Claim Processing feature")

            cursor.execute("SELECT id FROM brandsxai_features WHERE name = 'WhatsApp AI'")
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO brandsxai_features (name, icon, description) VALUES (%s, %s, %s)",
                    ('WhatsApp AI', 'MessageCircle', 'AI-assisted WhatsApp Business conversations for lead conversion')
                )
                wa_id = cursor.lastrowid
                cursor.execute(
                    "INSERT INTO brandsxai_feature_pages (feature_id, name, icon, route, display_order) VALUES (%s, %s, %s, %s, %s)",
                    (wa_id, 'Conversations', 'MessageCircle', '/dashboard/whatsapp-ai/conversations', 1)
                )
                logger.info("Created WhatsApp AI feature with pages")
            
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
                "id": 2, "name": "Claim Processing", "icon": "FileCheck", 
                "description": "AI-powered medical claim processing and ICD-10 code extraction",
                "pages": [
                    {"id": 1, "name": "Code Extractor", "icon": "FileSearch", "route": "/dashboard/claim-processing/extractor", "display_order": 1}
                ]
            })
        else:
            # Update existing Claim Processing to add pages if missing
            if not claim.get('pages'):
                await mongo_db.brandsxai_features.update_one(
                    {"name": "Claim Processing"},
                    {"$set": {"pages": [
                        {"id": 1, "name": "Code Extractor", "icon": "FileSearch", "route": "/dashboard/claim-processing/extractor", "display_order": 1}
                    ]}}
                )
        
        # WhatsApp AI feature
        wa_feature = await mongo_db.brandsxai_features.find_one({"name": "WhatsApp AI"})
        if not wa_feature:
            await mongo_db.brandsxai_features.insert_one({
                "id": 3, "name": "WhatsApp AI", "icon": "MessageCircle",
                "description": "AI-assisted WhatsApp Business conversations for lead conversion",
                "pages": [
                    {"id": 1, "name": "Conversations", "icon": "MessageCircle", "route": "/dashboard/whatsapp-ai/conversations", "display_order": 1}
                ]
            })
        # Ensure user 'mukesh' exists in Mongo (MySQL is blocked) with WhatsApp AI access
        mukesh = await mongo_db.brandsxai_users.find_one({"username": "mukesh"})
        if not mukesh:
            m_hash = bcrypt.hashpw('mukesh123'.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')
            await mongo_db.brandsxai_users.insert_one({
                "id": 1, "username": "mukesh", "email": "mukesh@brandx.com",
                "password_hash": m_hash, "brand_id": 1, "feature_ids": [1, 2, 3],
                "is_active": True, "created_at": datetime.now(timezone.utc).isoformat()
            })
        else:
            fids = mukesh.get('feature_ids', []) or []
            if 3 not in fids:
                fids.append(3)
                await mongo_db.brandsxai_users.update_one({"_id": mukesh['_id']}, {"$set": {"feature_ids": fids}})

        # Dedicated test user (MongoDB fallback ensures login works even when MySQL is unavailable)
        test_user = await mongo_db.brandsxai_users.find_one({"username": "testuser"})
        if not test_user:
            t_hash = bcrypt.hashpw('test123'.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')
            await mongo_db.brandsxai_users.insert_one({
                "id": 99, "username": "testuser", "email": "testuser@brandx.com",
                "password_hash": t_hash, "brand_id": 1, "feature_ids": [1, 2, 3],
                "is_active": True, "created_at": datetime.now(timezone.utc).isoformat()
            })
        else:
            fids = test_user.get('feature_ids', []) or []
            if set([1, 2, 3]) - set(fids):
                await mongo_db.brandsxai_users.update_one({"_id": test_user['_id']}, {"$set": {"feature_ids": [1, 2, 3]}})

        # Seed default WhatsApp message templates (global, brand_id=None)
        wa_tpl_count = await mongo_db.brandsxai_wa_templates.count_documents({})
        if wa_tpl_count == 0:
            # Seeded only on a fresh install, and only used for simulation / as a fallback:
            # when a real WABA is connected the UI prefers Meta-APPROVED templates instead.
            default_templates = [
                {"id": str(uuid.uuid4()), "brand_id": None, "name": "welcome_offer", "category": "MARKETING", "language": "en",
                 "body": "Hi {{1}}, this is {{2}} from Manohar Jewellers. Our Grand Chain & Bangles Fest is on 17-20 September - flat 50% off making charges on gold chains and bangles, making from 2.99%. Reply YES to know more.",
                 "variables": ["Customer Name", "Agent Name"], "created_at": datetime.now(timezone.utc).isoformat()},
                {"id": str(uuid.uuid4()), "brand_id": None, "name": "fest_invite", "category": "MARKETING", "language": "en",
                 "body": "Hi {{1}}, our biggest ever chain and bangles collection - Dubai, Italian and Singapore designs - is on display 17-20 September, 11 AM to 9 PM. Walk in at Sojti Gate, C Road or Satsang Bhawan, no booking needed.",
                 "variables": ["Customer Name"], "created_at": datetime.now(timezone.utc).isoformat()},
                {"id": str(uuid.uuid4()), "brand_id": None, "name": "making_charges_offer", "category": "MARKETING", "language": "en",
                 "body": "Hi {{1}}, for the first time in Jodhpur our making charges start from just 2.99% on gold chains and bangles - that is flat 50% off making, only from 17 to 20 September. Reply YES and I'll share designs.",
                 "variables": ["Customer Name"], "created_at": datetime.now(timezone.utc).isoformat()},
                {"id": str(uuid.uuid4()), "brand_id": None, "name": "design_shortlist_followup", "category": "UTILITY", "language": "en",
                 "body": "Hi {{1}}, sharing a few {{2}} designs from our fest collection. Let me know which one you like and I'll keep it ready for you to see.",
                 "variables": ["Customer Name", "Chains/Bangles"], "created_at": datetime.now(timezone.utc).isoformat()},
                {"id": str(uuid.uuid4()), "brand_id": None, "name": "visit_confirmation", "category": "UTILITY", "language": "en",
                 "body": "Hi {{1}}, we have noted your visit for {{2}}. No booking needed - just walk in between 11 AM and 9 PM at our {{3}} showroom. See you at Manohar Jewellers!",
                 "variables": ["Customer Name", "Date", "Showroom"], "created_at": datetime.now(timezone.utc).isoformat()},
                {"id": str(uuid.uuid4()), "brand_id": None, "name": "last_days_reminder", "category": "MARKETING", "language": "en",
                 "body": "Hi {{1}}, just a reminder that our Chain & Bangles Fest ends on 20 September. After that, making charges go back to full price. Do visit us before then!",
                 "variables": ["Customer Name"], "created_at": datetime.now(timezone.utc).isoformat()},
            ]
            await mongo_db.brandsxai_wa_templates.insert_many(default_templates)

        # WhatsApp indexes (compound indexes match the hot query paths for fast thread switching + polling)
        await mongo_db.brandsxai_wa_conversations.create_index([("brand_id", 1), ("last_message_at", -1)])
        await mongo_db.brandsxai_wa_conversations.create_index([("brand_id", 1), ("lead_phone", 1)])
        await mongo_db.brandsxai_wa_conversations.create_index("id", unique=True)
        await mongo_db.brandsxai_wa_messages.create_index([("conversation_id", 1), ("created_at", 1)])
        await mongo_db.brandsxai_wa_messages.create_index("wa_message_id")
        await mongo_db.brandsxai_wa_appointments.create_index([("conversation_id", 1), ("created_at", -1)])
        await mongo_db.brandsxai_wa_media.create_index("media_id", unique=True)

        # Create claim processing indexes
        await mongo_db.brandsxai_claim_sessions.create_index("user_id")
        await mongo_db.brandsxai_claim_sessions.create_index("brand_id")
        await mongo_db.brandsxai_claim_messages.create_index("session_id")
        
        # Default brands
        brand_x = await mongo_db.brandsxai_brands.find_one({"name": "Brand X"})
        if not brand_x:
            await mongo_db.brandsxai_brands.insert_one({"id": 1, "name": "Brand X", "created_at": datetime.now(timezone.utc).isoformat()})
            await mongo_db.brandsxai_brands.insert_one({"id": 2, "name": "Brand Y", "created_at": datetime.now(timezone.utc).isoformat()})
        
        logger.info("MongoDB collections initialized")
    except Exception as e:
        logger.error(f"MongoDB initialization error: {e}")

# Create the main app
app = FastAPI(title="BrandsXAI API", version="1.0.0")
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

# ==================== CLAIM PROCESSING MODELS ====================

class ClaimSessionCreate(BaseModel):
    title: Optional[str] = "New Claim Session"

class ClaimMessage(BaseModel):
    content: str
    file_data: Optional[List[dict]] = None  # [{filename, content_type, base64_data}]
    mode: Optional[str] = None  # "extract" | "refine"; inferred when omitted

class ICD10Code(BaseModel):
    code: str
    description: str
    source_text: Optional[str] = None
    confidence: Optional[float] = None

class ClaimSessionResponse(BaseModel):
    id: str
    title: str
    status: str
    extracted_codes: List[dict]
    created_at: str
    updated_at: str

class CodeUpdateRequest(BaseModel):
    codes: List[dict]  # [{code, description}]

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
    """BrandsXAI Admin login"""
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
    notes: Optional[str] = None

class OpportunityStageUpdate(BaseModel):
    stage: str

class OpportunityUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    business_name: Optional[str] = None
    notes: Optional[str] = None
    call_summary: Optional[str] = None
    recording_url: Optional[str] = None
    call_duration: Optional[int] = None
    call_outcome: Optional[str] = None

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
                    (campaign_id, brand_id, name, phone, email, business_name, notes, stage)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'dialing')
                """, (campaign_id, brand_id, opportunity.name, opportunity.phone, opportunity.email,
                      opportunity.business_name, opportunity.notes))
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
        "notes": opportunity.notes,
        "stage": "dialing",
        "call_summary": None,
        "recording_url": None,
        "call_duration": None,
        "call_outcome": None,
        "last_called_at": None,
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

@api_router.get("/opportunities/{opportunity_id}")
async def get_opportunity(opportunity_id: int, current_user: dict = Depends(get_current_user)):
    """Get single opportunity details"""
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    
    brand_id = current_user.get('brand_id')
    
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                cursor.execute("SELECT * FROM brandsxai_opportunities WHERE id = %s AND brand_id = %s", (opportunity_id, brand_id))
                result = cursor.fetchone()
                if not result:
                    raise HTTPException(status_code=404, detail="Opportunity not found")
                return {"opportunity": result, "db_source": "mysql"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"MySQL get opportunity error: {e}")
        finally:
            mysql_conn.close()
    
    # MongoDB fallback
    opp = await mongo_db.brandsxai_opportunities.find_one({"id": opportunity_id, "brand_id": brand_id}, {"_id": 0})
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return {"opportunity": opp, "db_source": "mongodb"}

@api_router.put("/opportunities/{opportunity_id}")
async def update_opportunity(opportunity_id: int, update: OpportunityUpdate, current_user: dict = Depends(get_current_user)):
    """Update opportunity details"""
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    
    brand_id = current_user.get('brand_id')
    
    # Build update dict with non-None values
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                set_clause = ", ".join([f"{k} = %s" for k in update_data.keys()])
                values = list(update_data.values()) + [opportunity_id, brand_id]
                cursor.execute(
                    f"UPDATE brandsxai_opportunities SET {set_clause} WHERE id = %s AND brand_id = %s",
                    values
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
            logger.error(f"MySQL update opportunity error: {e}")
        finally:
            mysql_conn.close()
    
    # MongoDB fallback
    result = await mongo_db.brandsxai_opportunities.update_one(
        {"id": opportunity_id, "brand_id": brand_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        # Check if exists
        existing = await mongo_db.brandsxai_opportunities.find_one({"id": opportunity_id, "brand_id": brand_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Opportunity not found")
    
    opp = await mongo_db.brandsxai_opportunities.find_one({"id": opportunity_id}, {"_id": 0})
    return {"opportunity": opp, "db_source": "mongodb"}

class DialRequest(BaseModel):
    phone: str

# AI Voice Calling API Configuration
AI_CALL_API_URL = "http://16.16.213.64:8000/api/call"
AI_CALL_API_KEY = "kj-neha-2024-xK9p"

def validate_phone_number(phone: str) -> tuple[bool, str]:
    """Validate phone number format - must be 10 digits (excluding country code)"""
    import re
    # Remove all non-digit characters except + at the start
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Check if it has country code (+91 or 91) and 10 digit number
    if cleaned.startswith('+91'):
        digits = cleaned[3:]  # Remove +91
    elif cleaned.startswith('91') and len(cleaned) >= 12:
        digits = cleaned[2:]  # Remove 91
    else:
        digits = cleaned.lstrip('+')  # Just the digits
    
    # Check if we have exactly 10 digits
    if len(digits) == 10 and digits.isdigit():
        # Format properly with country code
        formatted = f"+91{digits}"
        return True, formatted
    
    return False, "Phone number must be 10 digits (excluding country code)"

@api_router.post("/opportunities/{opportunity_id}/dial")
async def dial_opportunity(opportunity_id: int, dial_req: DialRequest, current_user: dict = Depends(get_current_user)):
    """Initiate AI voice call to an opportunity using external AI calling service"""
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    
    brand_id = current_user.get('brand_id')
    
    # Validate phone number
    is_valid, result = validate_phone_number(dial_req.phone)
    if not is_valid:
        raise HTTPException(status_code=400, detail=result)
    
    formatted_phone = result
    
    # Auto-open a WhatsApp thread for this lead (voice agent outreach -> WhatsApp handoff)
    await _wa_auto_open_from_opportunity(opportunity_id, formatted_phone, brand_id, current_user.get('username'))
    
    # Call the AI Voice Calling API
    import httpx
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                AI_CALL_API_URL,
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": AI_CALL_API_KEY
                },
                json={"phone_number": formatted_phone}
            )
            
            if response.status_code == 200:
                call_response = response.json()
                
                if call_response.get('success'):
                    # Call initiated successfully
                    update_data = {
                        'call_id': call_response.get('call_id'),
                        'last_called_at': datetime.now(timezone.utc).isoformat(),
                        'updated_at': datetime.now(timezone.utc).isoformat()
                    }
                    
                    # Update MongoDB
                    await mongo_db.brandsxai_opportunities.update_one(
                        {"id": opportunity_id, "brand_id": brand_id},
                        {"$set": update_data}
                    )
                    
                    return {
                        "success": True,
                        "message": "Call initiated successfully",
                        "call_id": call_response.get('call_id'),
                        "room_name": call_response.get('room_name'),
                        "phone_number": formatted_phone,
                        "timestamp": call_response.get('timestamp')
                    }
                else:
                    raise HTTPException(status_code=400, detail="AI service returned failure")
            else:
                error_detail = f"AI calling service error: HTTP {response.status_code}"
                try:
                    error_body = response.json()
                    if 'detail' in error_body:
                        error_detail = error_body['detail']
                except:
                    pass
                raise HTTPException(status_code=502, detail=error_detail)
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI calling service timeout - please try again")
    except httpx.RequestError as e:
        logger.error(f"AI call API request error: {e}")
        raise HTTPException(status_code=502, detail="Failed to connect to AI calling service")

@api_router.get("/contacts")
async def get_all_contacts(current_user: dict = Depends(get_current_user)):
    """Get all contacts/opportunities across all campaigns for the user's brand"""
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    
    brand_id = current_user.get('brand_id')
    
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                cursor.execute("""
                    SELECT o.*, c.name as campaign_name 
                    FROM brandsxai_opportunities o
                    JOIN brandsxai_campaigns c ON o.campaign_id = c.id
                    WHERE o.brand_id = %s
                    ORDER BY o.created_at DESC
                """, (brand_id,))
                contacts = cursor.fetchall()
                return {"contacts": contacts, "count": len(contacts), "db_source": "mysql"}
        except Exception as e:
            logger.error(f"MySQL get contacts error: {e}")
        finally:
            mysql_conn.close()
    
    # MongoDB fallback
    # First get campaign names
    campaigns = await mongo_db.brandsxai_campaigns.find({"brand_id": brand_id}, {"_id": 0}).to_list(100)
    campaign_map = {c['id']: c['name'] for c in campaigns}
    
    # Get all opportunities
    opportunities = await mongo_db.brandsxai_opportunities.find(
        {"brand_id": brand_id}, {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    # Add campaign names
    for opp in opportunities:
        opp['campaign_name'] = campaign_map.get(opp.get('campaign_id'), 'Unknown')
    
    return {"contacts": opportunities, "count": len(opportunities), "db_source": "mongodb"}

# ==================== SESSION/CALLS ====================

@api_router.get("/sessions/calls")
async def get_session_calls(current_user: dict = Depends(get_current_user)):
    """Get all call sessions for the user's brand"""
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    
    brand_id = current_user.get('brand_id')
    
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM brandsxai_calls 
                    WHERE brand_id = %s 
                    ORDER BY started_at DESC 
                    LIMIT 100
                """, (brand_id,))
                calls = cursor.fetchall()
                
                total_duration = sum(c.get('duration', 0) or 0 for c in calls)
                avg_duration = total_duration // len(calls) if calls else 0
                active_calls = len([c for c in calls if c.get('status') == 'active'])
                calls_with_issues = len([c for c in calls if c.get('has_issue')])
                
                return {
                    "calls": calls,
                    "stats": {
                        "totalCalls": len(calls),
                        "totalDuration": total_duration,
                        "avgDuration": avg_duration,
                        "activeCalls": active_calls,
                        "callsWithIssues": calls_with_issues
                    },
                    "db_source": "mysql"
                }
        except Exception as e:
            logger.error(f"MySQL get calls error: {e}")
        finally:
            mysql_conn.close()
    
    # MongoDB fallback
    calls = await mongo_db.brandsxai_calls.find(
        {"brand_id": brand_id}, {"_id": 0}
    ).sort("started_at", -1).limit(100).to_list(100)
    
    total_duration = sum(c.get('duration', 0) or 0 for c in calls)
    avg_duration = total_duration // len(calls) if calls else 0
    active_calls = len([c for c in calls if c.get('status') == 'active'])
    calls_with_issues = len([c for c in calls if c.get('has_issue')])
    
    return {
        "calls": calls,
        "stats": {
            "totalCalls": len(calls),
            "totalDuration": total_duration,
            "avgDuration": avg_duration,
            "activeCalls": active_calls,
            "callsWithIssues": calls_with_issues
        },
        "db_source": "mongodb"
    }

# ==================== CLAIM PROCESSING ====================

# Autocomplete suggestions only. This is not a validation source: a complete
# ICD-10-CM table with billable flags is required before codes can be verified.
ICD10_COMMON_CODES = {
    "E11.9": "Type 2 diabetes mellitus without complications",
    "I10": "Essential (primary) hypertension",
    "J06.9": "Acute upper respiratory infection, unspecified",
    "K21.0": "Gastro-esophageal reflux disease with esophagitis",
    "K21.9": "Gastro-esophageal reflux disease without esophagitis",
    "E53.8": "Deficiency of other specified B group vitamins",
    "Z98.84": "Bariatric surgery status",
    "R05.3": "Chronic cough",
    "R05.9": "Cough, unspecified",
    "M54.50": "Low back pain, unspecified",
    "M54.51": "Vertebrogenic low back pain",
    "M54.59": "Other low back pain",
    "F32.9": "Major depressive disorder, single episode, unspecified",
    "J45.909": "Unspecified asthma, uncomplicated",
    "E78.5": "Hyperlipidemia, unspecified",
    "N39.0": "Urinary tract infection, site not specified",
    "J18.9": "Pneumonia, unspecified organism",
    "G43.909": "Migraine, unspecified, not intractable, without status migrainosus",
    "K59.00": "Constipation, unspecified",
    "R10.9": "Unspecified abdominal pain",
    "R51.9": "Headache, unspecified",
    "Z87.891": "Personal history of nicotine dependence",
    "Z79.01": "Long term (current) use of anticoagulants",
    "Z79.02": "Long term (current) use of antithrombotics/antiplatelets",
    "Z79.4": "Long term (current) use of insulin",
    "Z79.52": "Long term (current) use of systemic steroids",
    "Z79.899": "Other long term (current) drug therapy",
}

# A pasted note this long is treated as a document to code rather than a chat message.
NOTE_TEXT_MIN_CHARS = 400

# Messages replayed into the prompt so corrections keep their context.
CLAIM_HISTORY_TURNS = 6

ICD10_CODING_RULES = """You are a certified medical coder assigning ICD-10-CM codes for claim submission.

CODE VALIDITY
- Assign only billable, submittable codes at full leaf-level specificity.
- Never assign a category or subcategory header. When a category has been expanded into
  children you must choose a child. M54.5, R05, K59.0 and Z99.8 are headers, not codes.
- `description` must be the official ICD-10-CM title of that exact code, not a restatement
  of the clinical phrase. If you cannot state the official title, lower `confidence`.
- Choose the code that names the documented condition directly over an "other specified" or
  "unspecified" sibling. Documented retinopathy in type 1 diabetes is E10.319, not E10.39.

COMPLETENESS
- Code the header/problem list AND the Assessment & Plan. A problem that appears only in the
  header problem list is still reportable and must not be skipped.
- Include chronic conditions documented as "stable", "controlled", or "at baseline".
- Put anything you cannot confidently code into `unmapped_problems` instead of dropping it.

REQUIRED PAIRINGS AND STATUS CODES
- Diabetes with ulcer (E10.62-/E11.62-) requires an additional ulcer site code (L97.-/L98.-).
- Coronary disease with documented bypass graft status (Z95.1) uses the graft codes I25.81-,
  not native-vessel I25.10.
- Transplants, implants, and devices each get their own status code (Z94.- transplanted organ,
  Z95.- cardiac graft/device, Z96.- implants, Z99.- device dependence).
- Every chronic medication in the note gets its long term drug therapy code: anticoagulants
  Z79.01, antiplatelets Z79.02, insulin Z79.4, systemic steroids Z79.52, immunosuppressants
  Z79.62-, bisphosphonates Z79.83. Z79.899 is only for drugs with no specific code; it is
  never a substitute for the specific ones.
- Before you answer, re-read the codes you just assigned and check these interactions against
  each other. A status code you assigned changes which diagnosis code is correct.

EVIDENCE
- Every code carries `source_text` quoted verbatim from the note. Never paraphrase and never
  invent supporting text. If you cannot quote the note, do not assign the code.

RESPONSE TEXT
- `response_text` describes what you coded and any judgement calls you made. Never state how
  many codes you assigned and never list them: the interface counts and lists them, and your
  count will contradict it whenever two mentions of one code are merged into a single entry."""

EXTRACT_TASK = """TASK: Extract ICD-10-CM codes from the clinical note above.
Pass over the note twice: first the header/problem list line by line, then the Assessment &
Plan section by section. Return everything you find in `new_codes` and leave
`codes_to_remove` empty. Set `response_text` to a short summary for the user."""

REFINE_TASK = """TASK: The user is reviewing codes that were already extracted. Apply their feedback.
- Codes to add go in `new_codes`; codes to retract go in `codes_to_remove`.
- To correct a code, put the wrong one in `codes_to_remove` and the right one in `new_codes`.
- Re-read the source note above and quote it in `source_text`; do not code from memory of
  this conversation alone.
- If the user only asked a question, answer it in `response_text` and leave both arrays empty."""

CLAIM_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "response_text": {"type": "string"},
        "new_codes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "description": {"type": "string"},
                    "source_text": {"type": "string"},
                    "confidence": {"type": "number"},
                },
                "required": ["code", "description", "source_text", "confidence"],
            },
        },
        "codes_to_remove": {"type": "array", "items": {"type": "string"}},
        "unmapped_problems": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["response_text", "new_codes", "codes_to_remove", "unmapped_problems"],
}


def normalize_icd10_code(code: str) -> str:
    """Canonical key for comparing codes, so I25.10 / i2510 / 'I25.10 ' collapse to one."""
    return re.sub(r'[^A-Z0-9]', '', (code or '').upper())


def merge_extracted_codes(existing: List[dict], new_codes: List[dict], codes_to_remove: List[str]) -> List[dict]:
    """Apply an AI turn to the session's code list, matching on normalized codes."""
    removal_keys = {normalize_icd10_code(c) for c in codes_to_remove if c}
    merged, index = [], {}

    for entry in existing:
        key = normalize_icd10_code(entry.get('code'))
        if not key or key in removal_keys or key in index:
            continue
        index[key] = len(merged)
        merged.append(entry)

    for entry in new_codes:
        key = normalize_icd10_code(entry.get('code'))
        if not key or key in removal_keys:
            continue
        entry = {**entry, 'code': str(entry.get('code', '')).strip().upper()}
        if key in index:
            merged[index[key]] = entry  # a re-emitted code carries fresher evidence
        else:
            index[key] = len(merged)
            merged.append(entry)

    return merged


def format_codes_for_prompt(codes: List[dict]) -> str:
    if not codes:
        return "(none yet)"
    return "\n".join(
        f"- {c.get('code', '?')}: {c.get('description', '')}".rstrip() for c in codes
    )


async def load_claim_history(session_id: str, limit: int) -> str:
    """Recent turns, oldest first, so follow-up corrections have their context."""
    rows, from_mysql = [], False
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                cursor.execute("""
                    SELECT role, content FROM brandsxai_claim_messages
                    WHERE session_id = %s
                    ORDER BY id DESC
                    LIMIT %s
                """, (session_id, limit))
                rows = list(reversed(cursor.fetchall() or []))
                from_mysql = True
        except Exception as e:
            logger.error(f"MySQL load claim history error: {e}")
        finally:
            mysql_conn.close()

    if not from_mysql:
        docs = await mongo_db.brandsxai_claim_messages.find(
            {"session_id": session_id}, {"_id": 0, "role": 1, "content": 1}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        rows = list(reversed(docs))

    return "\n".join(
        f"{r.get('role', 'user')}: {(r.get('content') or '')[:600]}" for r in rows
    )


def parse_claim_ai_response(ai_result) -> dict:
    """Read the model's JSON, failing loudly so a bad turn can never look like zero codes."""
    candidates = getattr(ai_result, 'candidates', None) or []
    finish_reason = getattr(candidates[0], 'finish_reason', None) if candidates else None

    try:
        raw = ai_result.text or ""
    except Exception:
        raw = ""

    if not raw.strip():
        logger.error(
            f"Claim AI returned no text (finish_reason={finish_reason}, "
            f"prompt_feedback={getattr(ai_result, 'prompt_feedback', None)})"
        )
        raise HTTPException(
            status_code=502,
            detail=f"The AI returned an empty response (finish_reason={finish_reason}). Nothing was saved; please retry."
        )

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"Claim AI returned non-JSON (finish_reason={finish_reason}): {raw[:2000]}")
        raise HTTPException(
            status_code=502,
            detail="The AI response could not be parsed. Nothing was saved; please retry."
        ) from e

    if not isinstance(parsed, dict):
        logger.error(f"Claim AI returned {type(parsed).__name__}, expected an object: {raw[:2000]}")
        raise HTTPException(
            status_code=502,
            detail="The AI response had an unexpected shape. Nothing was saved; please retry."
        )

    return parsed

@api_router.post("/claim-processing/sessions")
async def create_claim_session(
    request: ClaimSessionCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new claim processing session"""
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    
    import uuid
    session_id = str(uuid.uuid4())
    user_id = int(current_user.get('sub'))
    brand_id = current_user.get('brand_id')
    
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO brandsxai_claim_sessions (id, user_id, brand_id, title, extracted_codes)
                    VALUES (%s, %s, %s, %s, %s)
                """, (session_id, user_id, brand_id, request.title, json.dumps([])))
                mysql_conn.commit()
                
                return {
                    "id": session_id,
                    "title": request.title,
                    "status": "active",
                    "extracted_codes": [],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "db_source": "mysql"
                }
        except Exception as e:
            logger.error(f"MySQL create claim session error: {e}")
        finally:
            mysql_conn.close()
    
    # MongoDB fallback
    session = {
        "id": session_id,
        "user_id": user_id,
        "brand_id": brand_id,
        "title": request.title,
        "status": "active",
        "extracted_codes": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await mongo_db.brandsxai_claim_sessions.insert_one(session)
    del session['_id']
    session['db_source'] = 'mongodb'
    return session

@api_router.get("/claim-processing/sessions")
async def get_claim_sessions(current_user: dict = Depends(get_current_user)):
    """Get all claim sessions for the user"""
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    
    user_id = int(current_user.get('sub'))
    
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, title, status, extracted_codes, created_at, updated_at
                    FROM brandsxai_claim_sessions 
                    WHERE user_id = %s 
                    ORDER BY updated_at DESC
                    LIMIT 50
                """, (user_id,))
                sessions = cursor.fetchall()
                
                for s in sessions:
                    if isinstance(s.get('extracted_codes'), str):
                        s['extracted_codes'] = json.loads(s['extracted_codes'])
                    s['created_at'] = s['created_at'].isoformat() if s.get('created_at') else None
                    s['updated_at'] = s['updated_at'].isoformat() if s.get('updated_at') else None
                
                return {"sessions": sessions, "db_source": "mysql"}
        except Exception as e:
            logger.error(f"MySQL get claim sessions error: {e}")
        finally:
            mysql_conn.close()
    
    # MongoDB fallback
    sessions = await mongo_db.brandsxai_claim_sessions.find(
        {"user_id": user_id}, {"_id": 0}
    ).sort("updated_at", -1).limit(50).to_list(50)
    
    return {"sessions": sessions, "db_source": "mongodb"}

@api_router.get("/claim-processing/sessions/{session_id}")
async def get_claim_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific claim session with messages"""
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    
    user_id = int(current_user.get('sub'))
    
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM brandsxai_claim_sessions 
                    WHERE id = %s AND user_id = %s
                """, (session_id, user_id))
                session = cursor.fetchone()
                
                if not session:
                    raise HTTPException(status_code=404, detail="Session not found")
                
                cursor.execute("""
                    SELECT id, role, content, file_info, codes_extracted, created_at
                    FROM brandsxai_claim_messages 
                    WHERE session_id = %s 
                    ORDER BY created_at ASC
                """, (session_id,))
                messages = cursor.fetchall()
                
                if isinstance(session.get('extracted_codes'), str):
                    session['extracted_codes'] = json.loads(session['extracted_codes'])
                session['created_at'] = session['created_at'].isoformat() if session.get('created_at') else None
                session['updated_at'] = session['updated_at'].isoformat() if session.get('updated_at') else None
                
                for m in messages:
                    if isinstance(m.get('file_info'), str):
                        m['file_info'] = json.loads(m['file_info'])
                    if isinstance(m.get('codes_extracted'), str):
                        m['codes_extracted'] = json.loads(m['codes_extracted'])
                    m['created_at'] = m['created_at'].isoformat() if m.get('created_at') else None
                
                return {"session": session, "messages": messages, "db_source": "mysql"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"MySQL get claim session error: {e}")
        finally:
            mysql_conn.close()
    
    # MongoDB fallback
    session = await mongo_db.brandsxai_claim_sessions.find_one(
        {"id": session_id, "user_id": user_id}, {"_id": 0}
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = await mongo_db.brandsxai_claim_messages.find(
        {"session_id": session_id}, {"_id": 0}
    ).sort("created_at", 1).to_list(1000)
    
    return {"session": session, "messages": messages, "db_source": "mongodb"}

@api_router.post("/claim-processing/sessions/{session_id}/chat")
async def chat_with_claim_session(
    session_id: str,
    request: ClaimMessage,
    current_user: dict = Depends(get_current_user)
):
    """Send a message to the claim processing AI"""
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    
    user_id = int(current_user.get('sub'))
    
    # Verify session exists
    session = None
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                cursor.execute("SELECT * FROM brandsxai_claim_sessions WHERE id = %s AND user_id = %s", (session_id, user_id))
                session = cursor.fetchone()
        except Exception as e:
            logger.error(f"MySQL session check error: {e}")
        finally:
            mysql_conn.close()
    
    if not session:
        session = await mongo_db.brandsxai_claim_sessions.find_one({"id": session_id, "user_id": user_id})
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get existing codes from session
    existing_codes = session.get('extracted_codes', [])
    if isinstance(existing_codes, str):
        existing_codes = json.loads(existing_codes)

    # A long pasted message is the note itself, not chat. Keep it so later turns can re-read it.
    source_document = session.get('source_document') or ""
    pasted_note = (
        request.content.strip()
        if not request.file_data and len(request.content.strip()) >= NOTE_TEXT_MIN_CHARS
        else ""
    )
    if pasted_note:
        source_document = pasted_note

    mode = (request.mode or "").strip().lower()
    if mode not in ("extract", "refine"):
        mode = "extract" if (request.file_data or pasted_note) else "refine"

    history = await load_claim_history(session_id, CLAIM_HISTORY_TURNS)
    
    # Prepare the AI prompt
    try:
        import google.generativeai as genai
        import asyncio as _asyncio

        gemini_key = os.environ.get('EMERGENT_LLM_KEY') or os.environ.get('GOOGLE_API_KEY')
        if not gemini_key:
            raise HTTPException(status_code=500, detail="AI service not configured")

        genai.configure(api_key=gemini_key)

        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=ICD10_CODING_RULES,
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 16384,
                "response_mime_type": "application/json",
                "response_schema": CLAIM_RESPONSE_SCHEMA,
            }
        )

        sections = []
        if source_document:
            sections.append(f"SOURCE CLINICAL NOTE:\n{source_document}")
        if request.file_data:
            sections.append("SOURCE CLINICAL NOTE: also provided as the attached document(s).")
        sections.append(f"CODES CURRENTLY ON THIS CLAIM:\n{format_codes_for_prompt(existing_codes)}")
        if history:
            sections.append(f"EARLIER IN THIS CONVERSATION:\n{history}")
        sections.append(
            "USER MESSAGE:\n" + ("(the clinical note above)" if pasted_note else request.content)
        )
        sections.append(EXTRACT_TASK if mode == "extract" else REFINE_TASK)

        # Build parts list (text + optional file attachments)
        parts = ["\n\n".join(sections)]
        file_info = []
        if request.file_data:
            for f in request.file_data:
                parts.append({
                    "inline_data": {
                        "mime_type": f.get('content_type', 'application/pdf'),
                        "data": f.get('base64_data', '')
                    }
                })
                file_info.append({
                    "filename": f.get('filename', 'document'),
                    "content_type": f.get('content_type')
                })

        # Send to AI (run sync SDK in thread to avoid blocking the event loop)
        ai_result = await _asyncio.to_thread(model.generate_content, parts)
        ai_response = parse_claim_ai_response(ai_result)

        assistant_text = ai_response.get('response_text') or ""
        new_codes = ai_response.get('new_codes') or []
        codes_to_remove = ai_response.get('codes_to_remove') or []
        unmapped_problems = ai_response.get('unmapped_problems') or []

        if unmapped_problems:
            assistant_text = (
                f"{assistant_text}\n\nCould not be coded confidently: "
                + "; ".join(unmapped_problems)
            ).strip()

        updated_codes = merge_extracted_codes(existing_codes, new_codes, codes_to_remove)
        
        # Save to database
        mysql_conn = try_mysql_connection()
        if mysql_conn:
            try:
                with mysql_conn.cursor() as cursor:
                    # Save user message
                    cursor.execute("""
                        INSERT INTO brandsxai_claim_messages (session_id, role, content, file_info)
                        VALUES (%s, 'user', %s, %s)
                    """, (session_id, request.content, json.dumps(file_info) if file_info else None))
                    
                    # Save assistant message
                    cursor.execute("""
                        INSERT INTO brandsxai_claim_messages (session_id, role, content, codes_extracted)
                        VALUES (%s, 'assistant', %s, %s)
                    """, (session_id, assistant_text, json.dumps(new_codes) if new_codes else None))
                    
                    # Update session codes
                    cursor.execute("""
                        UPDATE brandsxai_claim_sessions 
                        SET extracted_codes = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (json.dumps(updated_codes), session_id))

                    # Best-effort: never let the newer column jeopardise saving codes
                    if source_document:
                        try:
                            cursor.execute("""
                                UPDATE brandsxai_claim_sessions
                                SET source_document = %s
                                WHERE id = %s
                            """, (source_document, session_id))
                        except Exception as e:
                            logger.error(f"Could not persist source_document: {e}")
                    
                    mysql_conn.commit()
            except Exception as e:
                logger.error(f"MySQL save chat error: {e}")
            finally:
                mysql_conn.close()
        else:
            # MongoDB fallback
            await mongo_db.brandsxai_claim_messages.insert_one({
                "session_id": session_id,
                "role": "user",
                "content": request.content,
                "file_info": file_info if file_info else None,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            await mongo_db.brandsxai_claim_messages.insert_one({
                "session_id": session_id,
                "role": "assistant",
                "content": assistant_text,
                "codes_extracted": new_codes if new_codes else None,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            await mongo_db.brandsxai_claim_sessions.update_one(
                {"id": session_id},
                {"$set": {
                    "extracted_codes": updated_codes,
                    "source_document": source_document or None,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
        
        return {
            "response": assistant_text,
            "mode": mode,
            "new_codes": new_codes,
            "codes_removed": codes_to_remove,
            "unmapped_problems": unmapped_problems,
            "all_codes": updated_codes
        }
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        raise HTTPException(status_code=500, detail="AI service not available")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@api_router.put("/claim-processing/sessions/{session_id}/codes")
async def update_session_codes(
    session_id: str,
    request: CodeUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Manually update the codes in a session"""
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    
    user_id = int(current_user.get('sub'))
    
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE brandsxai_claim_sessions 
                    SET extracted_codes = %s, updated_at = NOW()
                    WHERE id = %s AND user_id = %s
                """, (json.dumps(request.codes), session_id, user_id))
                mysql_conn.commit()
                
                if cursor.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Session not found")
                
                return {"success": True, "codes": request.codes, "db_source": "mysql"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"MySQL update codes error: {e}")
        finally:
            mysql_conn.close()
    
    # MongoDB fallback
    result = await mongo_db.brandsxai_claim_sessions.update_one(
        {"id": session_id, "user_id": user_id},
        {"$set": {"extracted_codes": request.codes, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"success": True, "codes": request.codes, "db_source": "mongodb"}

@api_router.get("/claim-processing/icd10/search")
async def search_icd10_codes(q: str = "", current_user: dict = Depends(get_current_user)):
    """Search ICD-10 codes for autocomplete"""
    if not current_user:
        raise HTTPException(status_code=403, detail="Authentication required")
    
    if len(q) < 2:
        return {"codes": []}
    
    q_lower = q.lower()
    results = []
    
    for code, desc in ICD10_COMMON_CODES.items():
        if q_lower in code.lower() or q_lower in desc.lower():
            results.append({"code": code, "description": desc})
    
    return {"codes": results[:20]}

@api_router.get("/claim-processing/sessions/{session_id}/export")
async def export_session_codes(session_id: str, current_user: dict = Depends(get_current_user)):
    """Export session codes as Excel file"""
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    
    user_id = int(current_user.get('sub'))
    
    # Get session
    session = None
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        try:
            with mysql_conn.cursor() as cursor:
                cursor.execute("SELECT * FROM brandsxai_claim_sessions WHERE id = %s AND user_id = %s", (session_id, user_id))
                session = cursor.fetchone()
        except Exception as e:
            logger.error(f"MySQL export error: {e}")
        finally:
            mysql_conn.close()
    
    if not session:
        session = await mongo_db.brandsxai_claim_sessions.find_one({"id": session_id, "user_id": user_id})
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    codes = session.get('extracted_codes', [])
    if isinstance(codes, str):
        codes = json.loads(codes)
    
    # Create Excel file
    import io
    try:
        import openpyxl
        from openpyxl import Workbook
        
        wb = Workbook()
        ws = wb.active
        ws.title = "ICD-10 Codes"
        
        # Header row
        ws['A1'] = "ICD-10 Codes"
        
        # Single row with all codes
        code_list = [c.get('code', '') for c in codes]
        ws['A2'] = ", ".join(code_list)
        
        # Second sheet with details
        ws2 = wb.create_sheet("Code Details")
        ws2['A1'] = "Code"
        ws2['B1'] = "Description"
        ws2['C1'] = "Source Text"
        
        for i, code in enumerate(codes, start=2):
            ws2[f'A{i}'] = code.get('code', '')
            ws2[f'B{i}'] = code.get('description', '')
            ws2[f'C{i}'] = code.get('source_text', '')
        
        # Save to buffer
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        from fastapi.responses import StreamingResponse
        
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=icd10_codes_{session_id[:8]}.xlsx"}
        )
    except ImportError:
        # Fallback to CSV
        import csv
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["ICD-10 Codes"])
        writer.writerow([", ".join([c.get('code', '') for c in codes])])
        
        from fastapi.responses import Response
        return Response(
            content=buffer.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=icd10_codes_{session_id[:8]}.csv"}
        )

# ==================== WHATSAPP AI ====================

from fastapi import Request, Query
from fastapi.responses import PlainTextResponse, StreamingResponse

class WATemplateCreate(BaseModel):
    name: str
    category: str = "MARKETING"
    language: str = "en"
    body: str
    variables: List[str] = []

class WAConversationCreate(BaseModel):
    lead_name: str
    lead_phone: str
    campaign_id: Optional[int] = None
    campaign_name: Optional[str] = None
    opportunity_id: Optional[int] = None
    product_interest: Optional[str] = None
    template_name: str
    template_body_rendered: str          # final text after variables filled (for our records / display)
    body_variables: List[str] = []       # values for {{1}}, {{2}}...
    language: str = "en"

class WATextSend(BaseModel):
    content: str
    msg_type: str = "text"               # text | image | video
    media_url: Optional[str] = None

class WASimulateInbound(BaseModel):
    content: str = ""
    msg_type: str = "text"               # text | image | video
    media_url: Optional[str] = None

class WAUploadInit(BaseModel):
    filename: str
    content_type: Optional[str] = None

class WAUploadComplete(BaseModel):
    upload_id: str
    filename: str
    content_type: Optional[str] = None

class WAAppointmentCreate(BaseModel):
    date: str
    time: str
    notes: Optional[str] = None

def wa_config():
    return {
        "version": os.environ.get("META_GRAPH_VERSION", "v22.0"),
        "phone_number_id": os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "").strip(),
        "token": os.environ.get("META_ACCESS_TOKEN", "").strip(),
        "app_secret": os.environ.get("META_APP_SECRET", "").strip(),
        "verify_token": os.environ.get("WEBHOOK_VERIFY_TOKEN", "").strip(),
    }

def wa_account_ids() -> dict:
    """The live WhatsApp Business account this process is currently wired to."""
    return {
        "waba_id": (os.environ.get("WHATSAPP_WABA_ID", "") or "").strip() or None,
        "wa_phone_number_id": wa_config()["phone_number_id"] or None,
    }

def wa_default_brand_id() -> int:
    """Brand that owns brand-new / unmatched inbound WhatsApp conversations.

    There is currently a single WhatsApp Business phone number shared by the whole
    platform, so the webhook has no reliable way to know which brand a never-seen-before
    phone number belongs to. Configurable via WA_DEFAULT_BRAND_ID so this doesn't stay
    hardcoded to whichever brand happened to be seeded first.
    """
    try:
        return int(os.environ.get("WA_DEFAULT_BRAND_ID", "1").strip() or "1")
    except ValueError:
        return 1

async def _wa_validate_default_brand() -> None:
    """Warn loudly if inbound WhatsApp threads would land on a brand nobody can see.

    GET /whatsapp/conversations filters by the logged-in user's brand_id, so if
    WA_DEFAULT_BRAND_ID points at a brand with no users, every inbound conversation is
    written correctly and is still invisible in the portal - which looks exactly like
    "WhatsApp is broken". Fail loudly instead of silently.
    """
    try:
        bid = wa_default_brand_id()

        # Users can live in MySQL (source of truth when reachable) or the MongoDB
        # fallback, so both have to be checked - a brand can be "empty" in one and
        # populated in the other.
        mysql_brand_ids: set = set()
        mysql_conn = try_mysql_connection()
        if mysql_conn:
            try:
                with mysql_conn.cursor() as cursor:
                    cursor.execute("SELECT DISTINCT brand_id FROM brandsxai_users WHERE brand_id IS NOT NULL")
                    mysql_brand_ids = {row["brand_id"] for row in cursor.fetchall()}
            except Exception as e:
                logger.warning(f"WA default-brand validation: MySQL user check failed: {str(e)[:150]}")
            finally:
                mysql_conn.close()

        if bid in mysql_brand_ids:
            logger.info(f"WA default brand {bid} has MySQL portal user(s) - inbound threads will be visible")
            return

        mongo_users = await mongo_db.brandsxai_users.count_documents({"brand_id": bid})
        if mongo_users:
            logger.info(f"WA default brand {bid} has {mongo_users} MongoDB portal user(s) - inbound threads will be visible")
            return

        brands = await mongo_db.brandsxai_brands.find({}, {"_id": 0, "id": 1, "name": 1}).to_list(50)
        mongo_usable = sorted({u.get("brand_id") for u in
                               await mongo_db.brandsxai_users.find({}, {"brand_id": 1}).to_list(200)
                               if u.get("brand_id") is not None})
        usable = sorted(mysql_brand_ids | set(mongo_usable))
        logger.critical(
            "WA_DEFAULT_BRAND_ID=%s has NO portal users (checked MySQL + MongoDB), so inbound WhatsApp "
            "conversations will be INVISIBLE in the app. Existing brands: %s. Brands that have users: %s. "
            "Set WA_DEFAULT_BRAND_ID to one of those and restart.",
            bid, [(b.get("id"), b.get("name")) for b in brands], usable,
        )
    except Exception as e:
        logger.warning(f"WA default-brand validation skipped: {str(e)[:150]}")


async def _wa_backfill_account_tags() -> None:
    """Stamp untagged threads with the live WABA / phone number id.

    Threads created before we started recording the receiving account would otherwise
    look orphaned after an account switch, or worse spawn a duplicate on the next inbound.
    """
    acc = wa_account_ids()
    if not acc["waba_id"] and not acc["wa_phone_number_id"]:
        return
    try:
        res = await mongo_db.brandsxai_wa_conversations.update_many(
            {"$or": [
                {"waba_id": {"$exists": False}},
                {"waba_id": None},
                {"waba_id": ""},
                {"wa_phone_number_id": {"$exists": False}},
                {"wa_phone_number_id": None},
                {"wa_phone_number_id": ""},
            ]},
            {"$set": {k: v for k, v in acc.items() if v}},
        )
        if res.modified_count:
            logger.info(f"WA account-tag backfill: stamped {res.modified_count} conversation(s) "
                        f"with waba={acc['waba_id']} pnid={acc['wa_phone_number_id']}")
    except Exception as e:
        logger.warning(f"WA account-tag backfill skipped: {str(e)[:150]}")


def wa_verify_tokens():
    """All accepted webhook verify tokens (supports both env var names)."""
    toks = [
        os.environ.get("WEBHOOK_VERIFY_TOKEN", "").strip(),
        os.environ.get("WHATSAPP_VERIFY_TOKEN", "").strip(),
    ]
    return [t for t in toks if t]

def wa_app_secrets():
    """All configured app secrets. META_APP_SECRET may hold a comma-separated list,
    which is handy when several Meta apps could own the WABA."""
    raw = os.environ.get("META_APP_SECRET", "") or ""
    return [s.strip() for s in raw.split(",") if s.strip()]

# Cached result of checking META_APP_SECRET against Meta (avoids a Graph call per webhook)
_WA_SECRET_STATE = {"checked_at": 0.0, "valid": None, "app_id": None, "detail": ""}

async def wa_check_app_secret(force: bool = False) -> dict:
    """Ask Meta whether the configured app secret really belongs to the app that owns this token.

    Uses the app-token grant: an App ID + App Secret pair that do not belong together are
    rejected with 'Error validating client secret.' This is what lets us tell a genuine
    forged-signature attempt apart from a simple misconfiguration.
    """
    import time as _time
    if not force and _WA_SECRET_STATE["valid"] is not None and (_time.time() - _WA_SECRET_STATE["checked_at"]) < 600:
        return _WA_SECRET_STATE

    secrets = wa_app_secrets()
    c = wa_config()
    if not secrets or not c["token"]:
        _WA_SECRET_STATE.update({"checked_at": _time.time(), "valid": None,
                                 "detail": "No app secret or access token configured"})
        return _WA_SECRET_STATE
    import httpx
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            d = await client.get(f"https://graph.facebook.com/{c['version']}/debug_token",
                                 headers={"Authorization": f"Bearer {c['token']}"},
                                 params={"input_token": c["token"]})
            if d.status_code != 200:
                _WA_SECRET_STATE.update({"checked_at": _time.time(), "valid": None,
                                         "detail": "Could not introspect access token"})
                return _WA_SECRET_STATE
            app_id = str(((d.json() or {}).get("data") or {}).get("app_id") or "")
            if not app_id:
                _WA_SECRET_STATE.update({"checked_at": _time.time(), "valid": None,
                                         "detail": "Access token has no app_id"})
                return _WA_SECRET_STATE
            for sec in secrets:
                r = await client.get("https://graph.facebook.com/oauth/access_token",
                                     params={"client_id": app_id, "client_secret": sec,
                                             "grant_type": "client_credentials"})
                if r.status_code == 200 and "access_token" in r.text:
                    _WA_SECRET_STATE.update({"checked_at": _time.time(), "valid": True, "app_id": app_id,
                                             "detail": f"App secret is valid for app {app_id}"})
                    return _WA_SECRET_STATE
            _WA_SECRET_STATE.update({
                "checked_at": _time.time(), "valid": False, "app_id": app_id,
                "detail": (f"META_APP_SECRET does not belong to app {app_id}, which owns this WABA. "
                           f"Copy it from App Dashboard > Settings > Basic > App Secret of app {app_id}."),
            })
            return _WA_SECRET_STATE
    except Exception as e:
        _WA_SECRET_STATE.update({"checked_at": _time.time(), "valid": None, "detail": f"check failed: {str(e)[:120]}"})
        return _WA_SECRET_STATE

def wa_payload_is_ours(payload: dict) -> bool:
    """Sanity-check that a webhook payload really concerns OUR WABA / phone number.

    Used as a secondary guard when the signature cannot be validated because the app
    secret is misconfigured, so we never ingest messages meant for someone else.
    """
    waba = (os.environ.get("WHATSAPP_WABA_ID", "") or "").strip()
    pnid = wa_config()["phone_number_id"]
    for entry in (payload.get("entry") or []):
        if waba and str(entry.get("id") or "") == waba:
            return True
        for change in (entry.get("changes") or []):
            meta = ((change.get("value") or {}).get("metadata") or {})
            if pnid and str(meta.get("phone_number_id") or "") == pnid:
                return True
    return False

def wa_is_live():
    c = wa_config()
    return bool(c["phone_number_id"] and c["token"])

def _norm_phone(phone: str) -> str:
    return re.sub(r"[^0-9]", "", phone or "")

async def wa_send_template(to: str, template_name: str, language: str, body_vars: List[str]):
    """Send an approved template message via Meta. Falls back to simulation if not configured."""
    if not wa_is_live():
        return {"simulated": True, "message_id": f"sim-{uuid.uuid4()}"}
    import httpx
    c = wa_config()
    url = f"https://graph.facebook.com/{c['version']}/{c['phone_number_id']}/messages"
    components = []
    if body_vars:
        components.append({"type": "body", "parameters": [{"type": "text", "text": v} for v in body_vars]})
    payload = {
        "messaging_product": "whatsapp", "to": _norm_phone(to), "type": "template",
        "template": {"name": template_name, "language": {"code": language},
                     **({"components": components} if components else {})}
    }
    headers = {"Authorization": f"Bearer {c['token']}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(url, headers=headers, json=payload)
    if r.is_error:
        logger.error(f"WA template send error: {r.status_code} {r.text[:300]}")
        raise HTTPException(status_code=502, detail={"meta_status": r.status_code, "meta_error": r.json().get("error", {})})
    data = r.json()
    return {"simulated": False, "message_id": (data.get("messages") or [{}])[0].get("id")}

async def wa_send_text(to: str, body: str):
    """Send a free-form text message (only valid inside the 24h window). Simulation fallback."""
    if not wa_is_live():
        return {"simulated": True, "message_id": f"sim-{uuid.uuid4()}"}
    import httpx
    c = wa_config()
    url = f"https://graph.facebook.com/{c['version']}/{c['phone_number_id']}/messages"
    payload = {"messaging_product": "whatsapp", "recipient_type": "individual",
               "to": _norm_phone(to), "type": "text", "text": {"preview_url": True, "body": body}}
    headers = {"Authorization": f"Bearer {c['token']}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(url, headers=headers, json=payload)
    if r.is_error:
        logger.error(f"WA text send error: {r.status_code} {r.text[:300]}")
        raise HTTPException(status_code=502, detail={"meta_status": r.status_code, "meta_error": r.json().get("error", {})})
    data = r.json()
    return {"simulated": False, "message_id": (data.get("messages") or [{}])[0].get("id")}

# ---- Real-time fan-out to open inboxes (Server-Sent Events) ----
# Every message path already funnels through _wa_touch_conversation, so publishing from
# there covers inbound webhooks, portal sends, voice-agent ingest and adopted external
# sends without each caller having to remember to announce itself.
WA_EVENT_SUBSCRIBERS: set = set()


def wa_publish(event: dict) -> None:
    """Hand an inbox event to every connected browser. Never raises, never blocks.

    A subscriber that has stopped reading (dead tab, frozen laptop) is dropped rather than
    allowed to apply backpressure to the webhook that is trying to persist a message.
    """
    for q in list(WA_EVENT_SUBSCRIBERS):
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:
            WA_EVENT_SUBSCRIBERS.discard(q)


async def _wa_touch_conversation(conv_id: str, last_message: str, direction: str):
    """Update conversation preview + unread counters + window on new message."""
    now = datetime.now(timezone.utc)
    update = {"last_message": last_message[:120], "last_message_at": now.isoformat(), "updated_at": now.isoformat()}
    inc = {}
    if direction == "inbound":
        inc = {"unread_count": 1}
        # Customer message (re)opens the 24h service window
        update["window_expires_at"] = (now + timedelta(hours=24)).isoformat()
    ops = {"$set": update}
    if inc:
        ops["$inc"] = inc
    conv = await mongo_db.brandsxai_wa_conversations.find_one_and_update(
        {"id": conv_id}, ops, projection={"_id": 0, "brand_id": 1}, return_document=ReturnDocument.AFTER)
    wa_publish({
        "type": "message", "conversation_id": conv_id, "direction": direction,
        "brand_id": (conv or {}).get("brand_id"), "preview": last_message[:120],
        "at": now.isoformat(),
    })

# -------- Media storage + chunked upload --------
WA_MEDIA_DIR = ROOT_DIR / "wa_media"
WA_MEDIA_TMP = WA_MEDIA_DIR / "tmp"
WA_MEDIA_DIR.mkdir(exist_ok=True)
WA_MEDIA_TMP.mkdir(exist_ok=True)

def _media_kind(content_type: str) -> str:
    ct = (content_type or "").lower()
    if ct.startswith("video"):
        return "video"
    if ct.startswith("image"):
        return "image"
    if ct.startswith("audio"):
        return "audio"
    return "document"

def _ext_for(filename: str) -> str:
    import os as _os
    return _os.path.splitext(filename or "")[1][:10]

async def wa_send_media(to: str, media_url_or_path: str, kind: str, caption: str = ""):
    """Best-effort media send. Simulation fallback when Meta not configured."""
    if not wa_is_live():
        return {"simulated": True, "message_id": f"sim-{uuid.uuid4()}"}
    import httpx
    c = wa_config()
    # In live mode a publicly reachable link is required by Meta; we serve media over REACT_APP_BACKEND_URL.
    base = os.environ.get("PUBLIC_BASE_URL", "").strip()
    link = media_url_or_path if str(media_url_or_path).startswith("http") else f"{base}{media_url_or_path}"
    url = f"https://graph.facebook.com/{c['version']}/{c['phone_number_id']}/messages"
    mtype = kind if kind in ("image", "video", "audio") else "document"
    payload = {"messaging_product": "whatsapp", "to": _norm_phone(to), "type": mtype,
               mtype: {"link": link, **({"caption": caption} if caption and mtype in ("image", "video", "document") else {})}}
    headers = {"Authorization": f"Bearer {c['token']}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, headers=headers, json=payload)
    if r.is_error:
        logger.error(f"WA media send error: {r.status_code} {r.text[:300]}")
        raise HTTPException(status_code=502, detail={"meta_status": r.status_code, "meta_error": r.json().get("error", {})})
    data = r.json()
    return {"simulated": False, "message_id": (data.get("messages") or [{}])[0].get("id")}

async def _wa_download_meta_media(meta_media_id: str, mime_type: Optional[str] = None):
    """Download a media file from Meta by media id, store locally, return served path."""
    import httpx
    c = wa_config()
    headers = {"Authorization": f"Bearer {c['token']}"}
    async with httpx.AsyncClient(timeout=40) as client:
        meta = await client.get(f"https://graph.facebook.com/{c['version']}/{meta_media_id}", headers=headers)
        if meta.is_error:
            return None
        info = meta.json()
        media_link = info.get("url")
        ct = info.get("mime_type") or mime_type or "application/octet-stream"
        if not media_link:
            return None
        dl = await client.get(media_link, headers=headers)
        if dl.is_error:
            return None
        content = dl.content
    media_id = str(uuid.uuid4())
    kind = _media_kind(ct)
    ext = "." + (ct.split("/")[-1].split(";")[0]) if "/" in ct else ""
    stored_name = f"{media_id}{ext[:10]}"
    (WA_MEDIA_DIR / stored_name).write_bytes(content)
    await mongo_db.brandsxai_wa_media.insert_one({
        "media_id": media_id, "filename": f"inbound{ext}", "stored_name": stored_name,
        "content_type": ct, "kind": kind, "brand_id": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    return f"/api/whatsapp/media/{media_id}"

@api_router.post("/whatsapp/upload/init")
async def wa_upload_init(req: WAUploadInit, current_user: dict = Depends(get_current_user)):
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    upload_id = str(uuid.uuid4())
    # create empty temp file
    (WA_MEDIA_TMP / upload_id).write_bytes(b"")
    return {"upload_id": upload_id}

@api_router.post("/whatsapp/upload/chunk")
async def wa_upload_chunk(request: Request, upload_id: str = Query(...), index: int = Query(0),
                          current_user: dict = Depends(get_current_user)):
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    tmp_path = WA_MEDIA_TMP / upload_id
    if not tmp_path.exists():
        raise HTTPException(status_code=404, detail="Upload session not found")
    chunk = await request.body()
    with open(tmp_path, "ab") as f:
        f.write(chunk)
    return {"ok": True, "index": index, "size": tmp_path.stat().st_size}

@api_router.post("/whatsapp/upload/complete")
async def wa_upload_complete(req: WAUploadComplete, current_user: dict = Depends(get_current_user)):
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    tmp_path = WA_MEDIA_TMP / req.upload_id
    if not tmp_path.exists():
        raise HTTPException(status_code=404, detail="Upload session not found")
    media_id = str(uuid.uuid4())
    ext = _ext_for(req.filename)
    final_name = f"{media_id}{ext}"
    final_path = WA_MEDIA_DIR / final_name
    tmp_path.rename(final_path)
    content_type = req.content_type or "application/octet-stream"
    kind = _media_kind(content_type)
    await mongo_db.brandsxai_wa_media.insert_one({
        "media_id": media_id, "filename": req.filename, "stored_name": final_name,
        "content_type": content_type, "kind": kind, "brand_id": current_user.get('brand_id'),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    return {"media_id": media_id, "url": f"/api/whatsapp/media/{media_id}", "kind": kind, "content_type": content_type, "filename": req.filename}

@api_router.get("/whatsapp/media/{media_id}")
async def wa_get_media(media_id: str):
    """Public media serving (unguessable UUID) so <img>/<video> tags can load it."""
    from fastapi.responses import FileResponse
    doc = await mongo_db.brandsxai_wa_media.find_one({"media_id": media_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Media not found")
    path = WA_MEDIA_DIR / doc["stored_name"]
    if not path.exists():
        raise HTTPException(status_code=404, detail="Media file missing")
    return FileResponse(str(path), media_type=doc.get("content_type", "application/octet-stream"), filename=doc.get("filename"))

# -------- Auto-open WhatsApp thread when the voice agent reaches out --------
async def _wa_auto_open_from_opportunity(opportunity_id: int, phone: str, brand_id, agent_username: str):
    """Create a WhatsApp conversation + send the intro template for a lead the voice agent just dialed.
    Idempotent per phone number. Best-effort: never raises."""
    try:
        digits = _norm_phone(phone)
        if not digits:
            return None
        existing = await mongo_db.brandsxai_wa_conversations.find_one({"brand_id": brand_id, "lead_phone": digits})
        if existing:
            return existing  # thread already exists; do not duplicate

        opp = await mongo_db.brandsxai_opportunities.find_one({"id": opportunity_id}, {"_id": 0}) or {}
        lead_name = opp.get("name") or "there"
        product = opp.get("business_name") or opp.get("notes") or ""
        campaign_name = None
        cid = opp.get("campaign_id")
        if cid:
            camp = await mongo_db.brandsxai_campaigns.find_one({"id": cid}, {"_id": 0})
            campaign_name = camp.get("name") if camp else None

        tpl = await mongo_db.brandsxai_wa_templates.find_one({"name": "welcome_offer"}, {"_id": 0})
        body_vars = [lead_name, agent_username or "our team"]
        rendered = (tpl.get("body") if tpl else
                    f"Hi {{{{1}}}}, this is {{{{2}}}} from {WA_BRAND_NAME}. Our Grand Chain & Bangles Fest is on "
                    "17-20 September - flat 50% off making charges on gold chains and bangles. Reply YES to know more.")
        for i, v in enumerate(body_vars, start=1):
            rendered = rendered.replace(f"{{{{{i}}}}}", v)

        send_res = await wa_send_template(digits, "welcome_offer", (tpl.get("language") if tpl else "en") or "en", body_vars)
        now = datetime.now(timezone.utc)
        conv_id = str(uuid.uuid4())
        conv = {
            "id": conv_id, "brand_id": brand_id, "campaign_id": cid, "campaign_name": campaign_name,
            "opportunity_id": opportunity_id, "lead_name": lead_name, "lead_phone": digits,
            "product_interest": (str(product).strip() or None),
            "stage": "Contacted", "status": "open", "unread_count": 0,
            "last_message": rendered[:120], "last_message_at": now.isoformat(),
            "assigned_agent": agent_username, "intent": None, "temperature": "warm",
            "source": "voice_agent", "window_expires_at": None,
            **wa_account_ids(),
            "created_at": now.isoformat(), "updated_at": now.isoformat()
        }
        await mongo_db.brandsxai_wa_conversations.insert_one(conv)
        await mongo_db.brandsxai_wa_messages.insert_one({
            "id": str(uuid.uuid4()), "conversation_id": conv_id, "direction": "outbound",
            "sender_type": "bot", "content": rendered, "msg_type": "template",
            "template_name": "welcome_offer", "media_url": None, "status": "sent",
            "wa_message_id": send_res.get("message_id"), "simulated": send_res.get("simulated", False),
            "created_at": now.isoformat()
        })
        return conv
    except Exception as e:
        logger.error(f"WA auto-open error: {e}")
        return None

# -------- AI (Claude) helpers --------
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

# ==================== SALES AI: BRAND + EVENT BRIEF ====================
# SINGLE SOURCE OF TRUTH for every WhatsApp AI prompt (strategist ideas, reply
# suggestions, draft-from-idea, summary). When the offer or the dates change, edit
# ONLY this block - all four prompts read it through _wa_context_block().

WA_BRAND_NAME = os.environ.get("WA_BRAND_NAME", "Manohar Jewellers")

# The two failure modes this brief is written to prevent:
#   1. The AI presenting "flat 50% off" and "from 2.99%" as two stacked discounts.
#      They are ONE deal - 2.99% is what the 50% off works out to.
#   2. The AI implying the GOLD RATE is discounted. Only making charges are cut.
WA_EVENT_BRIEF = """EVENT BRIEF - these are the ONLY facts. Never state an offer that is not here.

Business: Manohar Jewellers, Jodhpur - premium jeweller with three showrooms.
Event: Grand Chain & Bangles Fest.
Dates: 17 to 20 September - four days only. Before the 17th, making charges are full price.
Timing: 11 AM to 9 PM on all four days.
Showrooms: Sojti Gate, C Road, and Satsang Bhawan.
Entry: walk in directly. There is NO booking, NO appointment and NO slot to reserve.

THE OFFER (one single deal - never split it into two):
- Flat 50% off making charges on gold chains and bangles.
- After that 50% off, making starts from 2.99%.
- "Flat 50% off" and "from 2.99%" are the SAME deal: 2.99% is what the 50% off comes to.
  NEVER present them as two stacked discounts, and never say "50% off PLUS 2.99%".
- The gold rate stays the normal market rate. Only the jeweller's own making charges are
  cut. Never imply any discount on the gold itself.
- This is the first time Manohar Jewellers has brought making charges this low in Jodhpur.

Collection: their biggest ever chain and bangles collection - Dubai, Italian and Singapore
designs - available at all three showrooms.

SCOPE LIMIT: the 50% off / from-2.99% making applies ONLY to gold chains and bangles. All
other jewellery is on display to see, but NOT at fest making rates."""

# Everything a rep must never promise. The levers in the strategist prompt are deliberately
# limited to what the brief actually supports; this list closes the remaining gaps.
WA_OFFER_GUARDRAILS = """NOT AVAILABLE - never offer, hint at or invent any of these:
zero/nil making charges, any discount on the gold rate, old-gold exchange schemes, free gold
coins or gifts, EMI or 0% finance, rate lock or pre-booking, home delivery, private or VIP
slots, appointments, stylist consultations, referral gifts, extended dates, or a fest discount
on any jewellery other than gold chains and bangles.
If the customer asks for something outside the brief, offer to check with the store instead of
promising it."""

async def _wa_build_transcript(conv_id: str, limit: int = 20) -> str:
    msgs = await mongo_db.brandsxai_wa_messages.find({"conversation_id": conv_id}, {"_id": 0}).sort("created_at", 1).to_list(200)
    msgs = msgs[-limit:]
    lines = []
    for m in msgs:
        who = "CUSTOMER" if m.get("direction") == "inbound" else "BUSINESS"
        lines.append(f"{who}: {m.get('content', '')}")
    return "\n".join(lines)

async def _wa_claude_json(system_message: str, user_text: str, session_id: str) -> dict:
    import httpx
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        raise HTTPException(status_code=500, detail="AI service not configured")
    headers = {"x-api-key": key, "anthropic-version": ANTHROPIC_VERSION, "content-type": "application/json"}
    payload = {
        "model": CLAUDE_MODEL,
        "max_tokens": 1024,
        "system": system_message,
        "messages": [{"role": "user", "content": user_text}],
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(ANTHROPIC_API_URL, headers=headers, json=payload)
    if r.is_error:
        logger.error(f"Anthropic API error ({session_id}): {r.status_code} {r.text[:300]}")
        raise HTTPException(status_code=502, detail="AI service unavailable")
    text = "".join(b.get("text", "") for b in r.json().get("content", []) if b.get("type") == "text")
    # strip markdown fences / extract JSON object
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned).rstrip("`").strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start != -1 and end != -1:
        cleaned = cleaned[start:end + 1]
    try:
        return json.loads(cleaned)
    except Exception as e:
        logger.error(f"WA Claude JSON parse error: {e} raw={text[:300]}")
        return {}

def _wa_clean_line(text) -> str:
    """One-line, quote-free, markdown-free text — the panel shows plays and replies as plain chips."""
    line = re.sub(r"\s+", " ", str(text or "")).strip()
    line = re.sub(r"^[-*\d.\s]+", "", line)
    line = line.strip("`*_")
    if len(line) > 1 and line[0] in "\"'“‘" and line[-1] in "\"'”’":
        line = line[1:-1].strip()
    return line

def _wa_split_coach_output(raw_ideas, raw_suggestions) -> tuple:
    """Keep the coach's two halves genuinely separate.

    A play is strategy for the rep; a suggestion is text for the customer. The model
    occasionally returns a play that is really just a rephrased version of one of the
    messages, which makes the panel look duplicated — those get dropped.
    """
    from difflib import SequenceMatcher

    def words(s):
        return re.findall(r"[a-z0-9]+", s.lower())

    suggestions, seen = [], set()
    for s in raw_suggestions or []:
        line = _wa_clean_line(s)
        key = " ".join(words(line))
        if line and key not in seen:
            seen.add(key)
            suggestions.append(line)
    sugg_keys = [" ".join(words(s)) for s in suggestions]

    ideas = []
    for idea in raw_ideas or []:
        line = _wa_clean_line(idea)
        if not line:
            continue
        key = " ".join(words(line))
        if any(SequenceMatcher(None, key, sk).ratio() > 0.62 for sk in sugg_keys):
            continue
        if any(SequenceMatcher(None, key, " ".join(words(i))).ratio() > 0.7 for i in ideas):
            continue
        ideas.append(line)
    return ideas, suggestions

def _wa_context_block(conv: dict) -> str:
    """Lead context + the authoritative event brief, injected into every WhatsApp AI prompt."""
    return (
        f"Campaign: {conv.get('campaign_name') or 'N/A'}\n"
        f"Customer name: {conv.get('lead_name')}\n"
        f"Interested in: {conv.get('product_interest') or 'not stated yet'}\n"
        f"Current stage: {conv.get('stage') or 'N/A'}\n"
        f"Current temperature: {conv.get('temperature') or 'unknown'}\n"
        f"Business: {WA_BRAND_NAME} (goal: get this lead to walk into one of the three "
        f"showrooms during 17-20 September and buy).\n\n"
        f"{WA_EVENT_BRIEF}\n\n{WA_OFFER_GUARDRAILS}"
    )

# -------- Template endpoints --------
@api_router.get("/whatsapp/templates")
async def wa_list_templates(refresh: bool = Query(False), current_user: dict = Depends(get_current_user)):
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    brand_id = current_user.get('brand_id')
    # When connected to a real WABA, only Meta-approved templates are sendable.
    # Prefer those so the UI never offers a template Meta will reject (error 132001).
    if wa_is_live():
        # Opening the new-chat picker passes refresh=1 so newly approved templates
        # appear immediately. Other callers still use the TTL-guarded cache.
        if refresh:
            try:
                await _wa_sync_templates_from_meta(brand_id)
            except Exception as e:
                logger.warning(f"WA template refresh failed, serving cache: {str(e)[:200]}")
        else:
            await _wa_maybe_autosync_templates(brand_id)
        waba = (os.environ.get("WHATSAPP_WABA_ID", "") or "").strip()
        meta_tpls = await mongo_db.brandsxai_wa_templates.find(
            {"brand_id": brand_id, "source": "meta", "status": "APPROVED",
             **({"waba_id": waba} if waba else {})}, {"_id": 0}
        ).to_list(200)
        if meta_tpls:
            return {"templates": meta_tpls, "source": "meta", "live_mode": True,
                    "waba_id": waba, "synced": True}
    tpls = await mongo_db.brandsxai_wa_templates.find(
        {"$or": [{"brand_id": None}, {"brand_id": brand_id}]}, {"_id": 0}
    ).to_list(100)
    return {"templates": tpls, "source": "local", "live_mode": wa_is_live()}

@api_router.post("/whatsapp/templates")
async def wa_create_template(req: WATemplateCreate, current_user: dict = Depends(get_current_user)):
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    tpl = {"id": str(uuid.uuid4()), "brand_id": current_user.get('brand_id'), "name": req.name,
           "category": req.category, "language": req.language, "body": req.body,
           "variables": req.variables, "created_at": datetime.now(timezone.utc).isoformat()}
    await mongo_db.brandsxai_wa_templates.insert_one(tpl)
    tpl.pop("_id", None)
    return tpl

# Auto-sync bookkeeping: brand+WABA -> last attempt (monotonic seconds).
WA_TEMPLATE_SYNC_TTL = int(os.environ.get("WA_TEMPLATE_SYNC_TTL", "300"))
_WA_TPL_SYNC_STATE: dict = {}


async def _wa_sync_templates_from_meta(brand_id) -> dict:
    """Pull the REAL approved templates from the connected Meta WABA into the portal.

    Meta rejects any template name/language that is not approved on the WABA
    (error 132001), so the portal must offer exactly what Meta has - including the
    exact language code (e.g. en_US, not en) and the correct number of {{n}} variables.

    Also prunes rows Meta no longer approves, and rows left over from a different WABA,
    so switching WhatsApp accounts cannot leave unsendable templates in the picker.
    """
    c = wa_config()
    waba = (os.environ.get("WHATSAPP_WABA_ID", "") or "").strip()
    if not wa_is_live() or not waba:
        raise HTTPException(status_code=400, detail="WhatsApp not configured (need META_ACCESS_TOKEN + WHATSAPP_WABA_ID)")

    import httpx
    url = f"https://graph.facebook.com/{c['version']}/{waba}/message_templates"
    headers = {"Authorization": f"Bearer {c['token']}"}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, headers=headers,
                             params={"fields": "name,status,category,language,components", "limit": 200})
    if r.is_error:
        err = (r.json() or {}).get("error", {})
        logger.error(f"WA template sync error: {r.status_code} {r.text[:300]}")
        raise HTTPException(status_code=502, detail={"meta_status": r.status_code, "meta_error": err})

    now = datetime.now(timezone.utc).isoformat()
    synced, skipped = [], 0
    for t in (r.json() or {}).get("data", []):
        if t.get("status") != "APPROVED":
            skipped += 1
            continue
        body_text, header_text, footer_text = "", "", ""
        example = []
        for comp in t.get("components", []) or []:
            ctype = (comp.get("type") or "").upper()
            if ctype == "BODY":
                body_text = comp.get("text") or ""
                ex = (comp.get("example") or {}).get("body_text") or []
                if ex and isinstance(ex[0], list):
                    example = ex[0]
            elif ctype == "HEADER" and (comp.get("format") or "").upper() == "TEXT":
                header_text = comp.get("text") or ""
            elif ctype == "FOOTER":
                footer_text = comp.get("text") or ""
        # {{1}}, {{2}} ... in order of appearance, de-duplicated
        nums, seen = [], set()
        for m in re.findall(r"\{\{\s*(\d+)\s*\}\}", body_text):
            if m not in seen:
                seen.add(m)
                nums.append(m)
        # Human-readable labels for the {{n}} placeholders, using Meta's own examples as hints
        variables = []
        for i, n in enumerate(nums):
            hint = example[i] if i < len(example) else ""
            variables.append(f"Variable {n} (e.g. {hint})" if hint else f"Variable {n}")
        doc = {
            "brand_id": brand_id,
            "name": t.get("name"),
            "category": t.get("category") or "UTILITY",
            "language": t.get("language"),          # exact Meta code, e.g. en_US
            "body": body_text,
            "header": header_text,
            "footer": footer_text,
            "variables": variables,
            "variable_count": len(variables),
            "example_values": example,
            "status": t.get("status"),
            "source": "meta",
            "waba_id": waba,
            "synced_at": now,
        }
        await mongo_db.brandsxai_wa_templates.update_one(
            {"brand_id": brand_id, "name": doc["name"], "language": doc["language"], "source": "meta"},
            {"$set": doc, "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now}},
            upsert=True,
        )
        synced.append({"name": doc["name"], "language": doc["language"],
                       "variable_count": doc["variable_count"], "category": doc["category"]})

    # Prune: anything Meta no longer approves, plus leftovers from a previous WABA.
    # Without this, switching WhatsApp accounts leaves templates in the picker that
    # Meta will reject with error 132001.
    keep = [(t["name"], t["language"]) for t in synced]
    pruned = 0
    if keep:
        stale = await mongo_db.brandsxai_wa_templates.delete_many({
            "brand_id": brand_id, "source": "meta",
            "$nor": [{"name": n, "language": l} for n, l in keep],
        })
        pruned = stale.deleted_count
    other_waba = await mongo_db.brandsxai_wa_templates.delete_many(
        {"source": "meta", "waba_id": {"$exists": True, "$ne": waba}})
    pruned += other_waba.deleted_count

    logger.info(f"WA template sync: {len(synced)} approved synced, {skipped} non-approved skipped, "
                f"{pruned} stale removed (brand {brand_id}, waba {waba})")
    return {"synced_count": len(synced), "skipped_not_approved": skipped, "pruned": pruned,
            "waba_id": waba, "templates": synced}


async def _wa_maybe_autosync_templates(brand_id) -> None:
    """Refresh Meta templates when the cache is empty or older than the TTL.

    Never raises: if Meta is unreachable the caller must still be able to serve
    whatever is already cached.
    """
    waba = (os.environ.get("WHATSAPP_WABA_ID", "") or "").strip()
    if not wa_is_live() or not waba:
        return
    import time as _time
    now = _time.monotonic()
    key = (brand_id, waba)
    have = await mongo_db.brandsxai_wa_templates.count_documents(
        {"brand_id": brand_id, "source": "meta", "status": "APPROVED", "waba_id": waba})
    # Empty cache -> always sync, so the very first load already shows real templates.
    if have and (now - _WA_TPL_SYNC_STATE.get(key, 0.0)) < WA_TEMPLATE_SYNC_TTL:
        return
    _WA_TPL_SYNC_STATE[key] = now
    try:
        res = await _wa_sync_templates_from_meta(brand_id)
        logger.info(f"WA template auto-sync: {res.get('synced_count')} approved for brand {brand_id}")
    except Exception as e:
        logger.warning(f"WA template auto-sync failed, serving cached list: {str(e)[:200]}")


@api_router.post("/whatsapp/templates/sync")
async def wa_sync_templates(current_user: dict = Depends(get_current_user)):
    """Manual force-refresh of the Meta template cache."""
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    return await _wa_sync_templates_from_meta(current_user.get('brand_id'))

# -------- Conversation endpoints --------
@api_router.get("/whatsapp/events")
async def wa_events(request: Request, current_user: dict = Depends(get_current_user)):
    """Live inbox stream. Replaces tight polling so a message shows up the moment it lands."""
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    brand_id = current_user.get('brand_id')
    queue: asyncio.Queue = asyncio.Queue(maxsize=200)
    WA_EVENT_SUBSCRIBERS.add(queue)

    async def stream():
        try:
            # Tell EventSource how fast to come back, and prove the stream is open so the
            # client can stand its polling backstop down.
            yield "retry: 3000\n\n"
            yield f"event: ready\ndata: {json.dumps({'brand_id': brand_id})}\n\n"
            while not await request.is_disconnected():
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=20)
                except asyncio.TimeoutError:
                    # Idle streams get culled by ngrok/proxies; a comment keeps it warm.
                    yield ": keepalive\n\n"
                    continue
                if event.get("brand_id") not in (None, brand_id):
                    continue
                yield f"data: {json.dumps(event)}\n\n"
        finally:
            WA_EVENT_SUBSCRIBERS.discard(queue)

    return StreamingResponse(stream(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    })


@api_router.get("/whatsapp/conversations")
async def wa_list_conversations(current_user: dict = Depends(get_current_user)):
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    brand_id = current_user.get('brand_id')
    acc = wa_account_ids()
    query = {"brand_id": brand_id}
    # Only show threads that belong to the WhatsApp account currently in .env.
    # Untagged rows (created before we started stamping) stay visible so a just-received
    # inbound message is not hidden after an account switch.
    if acc["waba_id"] or acc["wa_phone_number_id"]:
        ors = [{"waba_id": {"$in": [None, ""]}}, {"waba_id": {"$exists": False}}]
        if acc["waba_id"]:
            ors.append({"waba_id": acc["waba_id"]})
        if acc["wa_phone_number_id"]:
            ors.append({"wa_phone_number_id": acc["wa_phone_number_id"]})
        query["$or"] = ors
    convs = await mongo_db.brandsxai_wa_conversations.find(query, {"_id": 0}).sort("last_message_at", -1).to_list(200)
    return {"conversations": convs, "live_mode": wa_is_live(), "account": acc}

@api_router.post("/whatsapp/conversations")
async def wa_create_conversation(req: WAConversationCreate, current_user: dict = Depends(get_current_user)):
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    brand_id = current_user.get('brand_id')
    phone = _norm_phone(req.lead_phone)
    now = datetime.now(timezone.utc)

    # Validate input (edge cases)
    if not (req.lead_name or "").strip():
        raise HTTPException(status_code=400, detail="Lead name is required")
    if len(phone) < 10:
        raise HTTPException(status_code=400, detail="Enter a valid phone number with country code")
    if not (req.template_name or "").strip():
        raise HTTPException(status_code=400, detail="A template is required to start a conversation")

    # Send template via Meta (or simulation)
    send_res = await wa_send_template(phone, req.template_name, req.language, req.body_variables)

    # WhatsApp = ONE thread per phone number. Reuse an existing thread instead of duplicating it.
    existing = await mongo_db.brandsxai_wa_conversations.find_one({"brand_id": brand_id, "lead_phone": phone})
    if existing:
        conv_id = existing["id"]
        msg = {
            "id": str(uuid.uuid4()), "conversation_id": conv_id, "direction": "outbound",
            "sender_type": "bot", "content": req.template_body_rendered, "msg_type": "template",
            "template_name": req.template_name, "media_url": None,
            "status": "sent", "wa_message_id": send_res.get("message_id"),
            "simulated": send_res.get("simulated", False), "created_at": now.isoformat()
        }
        await mongo_db.brandsxai_wa_messages.insert_one(msg)
        await mongo_db.brandsxai_wa_conversations.update_one(
            {"id": conv_id},
            {"$set": {"last_message": req.template_body_rendered[:120], "last_message_at": now.isoformat(),
                      "updated_at": now.isoformat(), "status": "open"}}
        )
        conv = await mongo_db.brandsxai_wa_conversations.find_one({"id": conv_id}, {"_id": 0})
        msg.pop("_id", None)
        return {"conversation": conv, "message": msg, "reused": True}

    conv_id = str(uuid.uuid4())
    acc = wa_account_ids()
    conv = {
        "id": conv_id, "brand_id": brand_id, "campaign_id": req.campaign_id, "campaign_name": req.campaign_name,
        "opportunity_id": req.opportunity_id, "lead_name": req.lead_name, "lead_phone": phone,
        "product_interest": req.product_interest, "stage": "Contacted", "status": "open",
        "unread_count": 0, "last_message": req.template_body_rendered[:120], "last_message_at": now.isoformat(),
        "assigned_agent": current_user.get('username'), "intent": None, "temperature": "warm",
        "waba_id": acc["waba_id"], "wa_phone_number_id": acc["wa_phone_number_id"],
        "window_expires_at": None, "created_at": now.isoformat(), "updated_at": now.isoformat()
    }
    await mongo_db.brandsxai_wa_conversations.insert_one(conv)

    msg = {
        "id": str(uuid.uuid4()), "conversation_id": conv_id, "direction": "outbound",
        "sender_type": "bot", "content": req.template_body_rendered, "msg_type": "template",
        "template_name": req.template_name, "media_url": None,
        "status": "sent", "wa_message_id": send_res.get("message_id"),
        "simulated": send_res.get("simulated", False), "created_at": now.isoformat()
    }
    await mongo_db.brandsxai_wa_messages.insert_one(msg)

    conv.pop("_id", None)
    msg.pop("_id", None)
    return {"conversation": conv, "message": msg, "reused": False}

@api_router.get("/whatsapp/conversations/{conv_id}")
async def wa_get_conversation(conv_id: str, current_user: dict = Depends(get_current_user)):
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    # Run all reads + the mark-read write concurrently (single round-trip latency instead of 4)
    conv, msgs, appts, _ = await asyncio.gather(
        mongo_db.brandsxai_wa_conversations.find_one({"id": conv_id}, {"_id": 0}),
        mongo_db.brandsxai_wa_messages.find({"conversation_id": conv_id}, {"_id": 0}).sort("created_at", 1).to_list(500),
        mongo_db.brandsxai_wa_appointments.find({"conversation_id": conv_id}, {"_id": 0}).sort("created_at", -1).to_list(20),
        mongo_db.brandsxai_wa_conversations.update_one({"id": conv_id}, {"$set": {"unread_count": 0}}),
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conv["unread_count"] = 0
    return {"conversation": conv, "messages": msgs, "appointments": appts, "live_mode": wa_is_live()}

@api_router.get("/whatsapp/conversations/{conv_id}/messages")
async def wa_poll_messages(conv_id: str, after: Optional[str] = Query(None), current_user: dict = Depends(get_current_user)):
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    query = {"conversation_id": conv_id}
    if after:
        query["created_at"] = {"$gt": after}
    msgs = await mongo_db.brandsxai_wa_messages.find(query, {"_id": 0}).sort("created_at", 1).to_list(200)
    return {"messages": msgs}

@api_router.get("/whatsapp/conversations/{conv_id}/message-status")
async def wa_message_statuses(conv_id: str, current_user: dict = Depends(get_current_user)):
    """Compact delivery-status map for a thread's outbound messages.

    The message poll uses ?after= and therefore only ever APPENDS new messages, so it can
    never refresh the tick of a message already on screen. Meta delivers 'delivered' and
    'read' for messages we sent minutes ago, so the UI polls this cheap endpoint to keep
    the ticks live.
    """
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    msgs = await mongo_db.brandsxai_wa_messages.find(
        {"conversation_id": conv_id, "direction": "outbound"},
        {"_id": 0, "id": 1, "status": 1, "status_timestamps": 1},
    ).sort("created_at", -1).to_list(200)
    return {"statuses": msgs}

@api_router.post("/whatsapp/conversations/{conv_id}/messages")
async def wa_send_message(conv_id: str, req: WATextSend, current_user: dict = Depends(get_current_user)):
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    conv = await mongo_db.brandsxai_wa_conversations.find_one({"id": conv_id})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    now = datetime.now(timezone.utc)
    is_media = req.msg_type in ("image", "video", "audio", "document") and req.media_url
    if is_media:
        send_res = await wa_send_media(conv["lead_phone"], req.media_url, req.msg_type, caption=req.content or "")
        preview = f"[{req.msg_type}]" + (f" {req.content}" if req.content else "")
    else:
        send_res = await wa_send_text(conv["lead_phone"], req.content)
        preview = req.content
    msg = {
        "id": str(uuid.uuid4()), "conversation_id": conv_id, "direction": "outbound",
        "sender_type": "human", "content": req.content, "msg_type": req.msg_type,
        "media_url": req.media_url, "status": "sent", "wa_message_id": send_res.get("message_id"),
        "simulated": send_res.get("simulated", False), "created_at": now.isoformat()
    }
    await mongo_db.brandsxai_wa_messages.insert_one(msg)
    await _wa_touch_conversation(conv_id, preview, "outbound")
    msg.pop("_id", None)
    return {"message": msg}

@api_router.post("/whatsapp/conversations/{conv_id}/simulate-inbound")
async def wa_simulate_inbound(conv_id: str, req: WASimulateInbound, current_user: dict = Depends(get_current_user)):
    """Demo helper: simulate a customer reply (used when real WhatsApp webhook is not connected)."""
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    conv = await mongo_db.brandsxai_wa_conversations.find_one({"id": conv_id})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    now = datetime.now(timezone.utc)
    is_media = req.msg_type in ("image", "video", "audio", "document") and req.media_url
    preview = (f"[{req.msg_type}]" + (f" {req.content}" if req.content else "")) if is_media else req.content
    msg = {
        "id": str(uuid.uuid4()), "conversation_id": conv_id, "direction": "inbound",
        "sender_type": "customer", "content": req.content, "msg_type": req.msg_type or "text",
        "media_url": req.media_url, "status": "delivered", "wa_message_id": f"sim-in-{uuid.uuid4()}",
        "simulated": True, "created_at": now.isoformat()
    }
    await mongo_db.brandsxai_wa_messages.insert_one(msg)
    await _wa_touch_conversation(conv_id, preview or "[media]", "inbound")
    msg.pop("_id", None)
    return {"message": msg}

# -------- System ingest (voice AI platform / external systems push messages here) --------
class WAIngestMessage(BaseModel):
    lead_phone: str
    lead_name: Optional[str] = None
    # Left unset on purpose: an explicit default here would win over WA_DEFAULT_BRAND_ID and
    # file the thread under a brand whose users cannot see it, which looks like message loss.
    brand_id: Optional[int] = None
    campaign_name: Optional[str] = None
    product_interest: Optional[str] = None
    direction: str = "outbound"          # outbound (business/voice-agent) | inbound (customer)
    sender_type: Optional[str] = None    # bot | human | customer
    content: str = ""
    msg_type: str = "text"               # text | template | image | video | document
    media_url: Optional[str] = None
    template_name: Optional[str] = None
    wa_message_id: Optional[str] = None  # Meta message id (so later status webhooks map to it)

async def _wa_find_or_create_conv(brand_id, phone, lead_name=None, campaign_name=None,
                                   product_interest=None, source=None):
    conv = await mongo_db.brandsxai_wa_conversations.find_one({"brand_id": brand_id, "lead_phone": phone})
    if conv:
        return conv, False
    now = datetime.now(timezone.utc)
    conv = {
        "id": str(uuid.uuid4()), "brand_id": brand_id, "campaign_id": None, "campaign_name": campaign_name,
        "opportunity_id": None, "lead_name": lead_name or phone, "lead_phone": phone,
        "product_interest": product_interest, "stage": "Contacted", "status": "open",
        "unread_count": 0, "last_message": "", "last_message_at": now.isoformat(),
        "assigned_agent": None, "intent": None, "temperature": "warm", "source": source,
        "window_expires_at": None, **wa_account_ids(),
        "created_at": now.isoformat(), "updated_at": now.isoformat()
    }
    await mongo_db.brandsxai_wa_conversations.insert_one(conv)
    return conv, True

@api_router.post("/whatsapp/ingest/message")
async def wa_ingest_message(req: WAIngestMessage, request: Request):
    """System-to-system: the voice AI platform (or WhatsApp middleware) pushes any message it sent or
    received. The thread appears automatically in the inbox — no manual 'start chat' needed.
    Secured with the X-Ingest-Token header (env WA_INGEST_TOKEN)."""
    ingest_token = os.environ.get("WA_INGEST_TOKEN", "").strip()
    if ingest_token:
        if request.headers.get("X-Ingest-Token", "") != ingest_token:
            raise HTTPException(status_code=403, detail="Invalid ingest token")
    phone = _norm_phone(req.lead_phone)
    if len(phone) < 10:
        raise HTTPException(status_code=400, detail="Valid phone with country code required")
    direction = "inbound" if req.direction == "inbound" else "outbound"
    default_sender = "customer" if direction == "inbound" else ("bot" if req.msg_type == "template" else "human")
    sender_type = req.sender_type or default_sender

    conv, created = await _wa_find_or_create_conv(
        req.brand_id or wa_default_brand_id(), phone, req.lead_name, req.campaign_name, req.product_interest, source="voice_agent"
    )
    conv_id = conv["id"]
    now = datetime.now(timezone.utc)

    # Idempotency: skip if this exact Meta message id was already recorded
    if req.wa_message_id:
        dupe = await mongo_db.brandsxai_wa_messages.find_one({"wa_message_id": req.wa_message_id})
        if dupe:
            existing_conv = await mongo_db.brandsxai_wa_conversations.find_one({"id": conv_id}, {"_id": 0})
            return {"conversation": existing_conv, "message": {k: v for k, v in dupe.items() if k != "_id"}, "duplicate": True}

    is_media = req.msg_type in ("image", "video", "audio", "document") and req.media_url
    preview = (f"[{req.msg_type}]" + (f" {req.content}" if req.content else "")) if is_media else (req.content or f"[{req.msg_type}]")
    msg = {
        "id": str(uuid.uuid4()), "conversation_id": conv_id, "direction": direction,
        "sender_type": sender_type, "content": req.content, "msg_type": req.msg_type,
        "template_name": req.template_name, "media_url": req.media_url, "status": "delivered" if direction == "inbound" else "sent",
        "wa_message_id": req.wa_message_id or f"ext-{uuid.uuid4()}", "simulated": False, "created_at": now.isoformat()
    }
    await mongo_db.brandsxai_wa_messages.insert_one(msg)
    await _wa_touch_conversation(conv_id, preview, direction)
    conv = await mongo_db.brandsxai_wa_conversations.find_one({"id": conv_id}, {"_id": 0})
    msg.pop("_id", None)
    return {"conversation": conv, "message": msg, "thread_created": created}

# -------- AI endpoints --------
@api_router.post("/whatsapp/conversations/{conv_id}/suggestions")
async def wa_suggestions(conv_id: str, current_user: dict = Depends(get_current_user)):
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    conv = await mongo_db.brandsxai_wa_conversations.find_one({"id": conv_id})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    transcript = await _wa_build_transcript(conv_id)
    system = (
        f"You are the sharpest sales coach at {WA_BRAND_NAME}, a premium jeweller in Jodhpur. You sit beside "
        "ONE human rep who is on WhatsApp with ONE lead about the Grand Chain & Bangles Fest (17-20 September). "
        "The rep reads you in a narrow side panel between customer replies, so every word must earn its place.\n"
        "Write EVERYTHING in English.\n\n"
        "You produce TWO things that must never blur into each other:\n"
        "  creative_ideas = coaching for the REP's eyes. Strategy. Never words the customer sees.\n"
        "  suggestions    = the exact words the CUSTOMER sees. Never strategy talk.\n\n"
        "===== 1) creative_ideas: 2-3 plays, for the rep only =====\n"
        "A play is an angle this rep would not have thought of by themselves. Build each one this way:\n"
        "  a. Read the ONE real signal in this chat: the word they repeated, who they are buying for, the "
        "occasion behind it, what they asked twice, what they pointedly did NOT answer, how fast they reply, "
        "whether they talk price, weight or design first.\n"
        "  b. Name the single honest reason this lead would not walk in during the four days.\n"
        "  c. Pick the ONE lever that removes that reason:\n"
        "     value (flat 50% off making, from 2.99% - the lowest making Jodhpur has seen) / occasion (wedding, "
        "anniversary, birthday, festival, gift for mother or wife) / collection (biggest ever chain and bangles "
        "range, Dubai, Italian, Singapore designs) / convenience (any of the four days 11 AM-9 PM, no booking, "
        "nearest of Sojti Gate, C Road, Satsang Bhawan) / social (bring family, send a 3-design shortlist to "
        "show her mother or husband) / reassurance (try the piece on in person before deciding) / urgency "
        "(four days only; before the 17th making is full price).\n"
        "  d. The move must be something the rep can do in the next five minutes inside WhatsApp.\n"
        "FORM: each idea is ONE line, 12 words or fewer, imperative, addressed to the rep, and it must name "
        "the specific detail it hangs on - e.g. 'Shortlist 3 bangles for her mother's anniversary', 'She "
        "asked weight twice - quote per gram', 'Offer C Road, she works near Sojti Gate'.\n"
        "Count the words. If a play runs past 12, cut the adjectives and the explanation - the rep only needs "
        "the signal and the move.\n"
        "NEVER write an idea as a sentence the rep could paste and send, and never put quoted message text in "
        "an idea. No two ideas may use the same lever or the same signal.\n\n"
        "===== 2) suggestions: exactly 3 messages, ready to send =====\n"
        "These are the real words going to the customer. HARD LIMIT: 18 words per message, and aim for 12. "
        "One line, one thought - if it needs a comma splice or a second clause, cut it.\n"
        "Type like a person on a phone: contractions, plain words, no markdown, no bullets, no 'Dear' or "
        "'Greetings', at most one emoji across all three, no repeating the customer's name in every message.\n"
        "Three different routes: (a) answer or acknowledge exactly what they said last, (b) dissolve the "
        "hesitation you named above, (c) ask for the next small commitment - which day, which showroom, chain "
        "or bangles, who it is for.\n"
        "At least two must end with a question they can answer in three words.\n"
        "Never recite offer copy. Do not write lines like 'the lowest making ever offered in Jodhpur' or "
        "'biggest ever collection' - that is brochure language and the customer feels it. If the offer needs "
        "saying, say it once, plainly, as it affects THEM ('making is half price till the 20th').\n"
        "A message must never restate an idea's wording or read like a broadcast.\n\n"
        "===== THE BAR =====\n"
        "Test every single line before you answer: could it be pasted into a different lead's chat without "
        "changing one word? If yes it is generic - delete it and write one that only makes sense for THIS "
        "person. Use their words, their occasion, their budget hints, their timing.\n"
        "Hold both heads at once. As the customer: 'why would I leave my house and walk into a jewellery "
        "showroom this week?' As the rep: 'what moves this lead one stage forward today?' (Contacted -> "
        "Engaged -> Qualified -> Visit Confirmed -> Reminded -> Visited -> Purchased.)\n"
        "Cold lead: lower the ask - a design photo, one easy question - do not push the visit. Warm lead: get "
        "a preference on record (chain or bangles, gramage, who it is for). Hot lead: lock which day and which "
        "showroom, and ask what to keep ready to show them.\n"
        "If only the opening template has been sent, work from the campaign and product interest and open the "
        "conversation - never pretend the customer said something they did not.\n\n"
        "===== FACTS =====\n"
        "Never state an offer that is not in the EVENT BRIEF.\n"
        "Flat 50% off making IS 'making from 2.99%' - one deal, never two stacked discounts.\n"
        "The gold rate is never discounted; only making charges are cut. HARD RULE: the word 'gold' must never "
        "appear in the same sentence as a saving, a discount, a budget or a price - no 'cheaper gold', no "
        "'better gold rate', no 'your budget stretches further on the gold', no 'more grams for your money'. "
        "The saving belongs to the making charge and nothing else.\n"
        "Fest making rates cover gold chains and bangles ONLY.\n"
        "There is no slot or appointment - the commitment to ask for is WHICH DAY and WHICH SHOWROOM.\n\n"
        "Also classify the lead's buying intent as one of: hot, warm, cold.\n"
        "Respond ONLY with strict JSON: {\"creative_ideas\":[\"...\",\"...\"],\"suggestions\":[\"...\",\"...\",\"...\"],"
        "\"intent\":\"short phrase\",\"temperature\":\"hot|warm|cold\"}"
    )
    user_text = f"CAMPAIGN & LEAD CONTEXT:\n{_wa_context_block(conv)}\n\nCONVERSATION SO FAR:\n{transcript or '(only the first template message has been sent)'}\n\nCoach the rep now: 2-3 plays for their eyes, then the 3 best messages to send."
    result = await _wa_claude_json(system, user_text, f"wa-sugg-{conv_id}")
    creative_ideas, suggestions = _wa_split_coach_output(
        result.get("creative_ideas"), result.get("suggestions")
    )
    temperature = result.get("temperature")
    intent = result.get("intent")
    # persist intent/temperature onto conversation
    upd = {}
    if temperature in ("hot", "warm", "cold"):
        upd["temperature"] = temperature
    if intent:
        upd["intent"] = intent
    if upd:
        await mongo_db.brandsxai_wa_conversations.update_one({"id": conv_id}, {"$set": upd})
    return {"suggestions": suggestions[:3], "creative_ideas": creative_ideas[:3], "intent": intent, "temperature": temperature}

class WADraftFromIdea(BaseModel):
    idea: str

@api_router.post("/whatsapp/conversations/{conv_id}/draft-from-idea")
async def wa_draft_from_idea(conv_id: str, req: WADraftFromIdea, current_user: dict = Depends(get_current_user)):
    """Turn a creative strategic idea into one ready-to-send WhatsApp message."""
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    conv = await mongo_db.brandsxai_wa_conversations.find_one({"id": conv_id})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    transcript = await _wa_build_transcript(conv_id)
    system = (
        f"You are a WhatsApp sales rep for {WA_BRAND_NAME}, a premium jeweller in Jodhpur. The PLAY below is "
        "private coaching written to you. Execute it as ONE message to the customer, in English.\n"
        "ONE line, max 22 words, ideally under 15. Type like a person on a phone: contractions, plain words, "
        "no markdown, no 'Dear' or 'Greetings', at most one emoji, and end with a question they can answer in "
        "three words whenever it fits.\n"
        "Carry out the play - never describe it, never quote its wording, and never mention coaching, "
        "strategy or AI. Hang the message on the specific detail the play points at (their occasion, the "
        "person they are buying for, what they asked about).\n"
        "Stick strictly to the EVENT BRIEF in the context - never invent an offer. The deal is ONE thing: flat "
        "50% off making charges on gold chains and bangles, which is what 'making from 2.99%' means - never "
        "present them as two separate discounts. Never suggest the gold rate is discounted. Never ask them to "
        "book a slot or appointment; the ask is which day and which showroom they will walk into (17-20 "
        "September, 11 AM-9 PM).\n"
        "Respond ONLY with strict JSON: {\"message\":\"...\"}"
    )
    user_text = (
        f"CAMPAIGN & LEAD CONTEXT:\n{_wa_context_block(conv)}\n\n"
        f"CONVERSATION SO FAR:\n{transcript or '(only the first template message has been sent)'}\n\n"
        f"PLAY TO EXECUTE: {req.idea}\n\nWrite the message now."
    )
    result = await _wa_claude_json(system, user_text, f"wa-idea-{conv_id}")
    return {"message": _wa_clean_line(result.get("message", ""))}

@api_router.get("/whatsapp/conversations/{conv_id}/summary")
async def wa_summary(conv_id: str, current_user: dict = Depends(get_current_user)):
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    conv = await mongo_db.brandsxai_wa_conversations.find_one({"id": conv_id})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    transcript = await _wa_build_transcript(conv_id, limit=40)
    system = (
        f"You read a WhatsApp sales conversation for {WA_BRAND_NAME}, a premium jeweller running a Grand "
        "Chain & Bangles Fest from 17-20 September, and brief the rep in English. Judge how close this lead "
        "is to walking into a showroom during the fest and buying.\n"
        "The summary says what this lead actually wants, who it is for, and the one thing holding them back - "
        "not a replay of the messages. The next_step is ONE concrete action the rep can take on WhatsApp now, "
        "max 15 words, specific to this lead, consistent with the EVENT BRIEF - no invented offers, and no "
        "slot or appointment booking (the fest is walk-in; the ask is which day and which showroom).\n"
        "Return ONLY strict JSON: {\"summary\":\"2-3 sentence summary\",\"next_step\":\"one recommended next action\",\"temperature\":\"hot|warm|cold\"}"
    )
    user_text = f"CONTEXT:\n{_wa_context_block(conv)}\n\nCONVERSATION:\n{transcript}"
    result = await _wa_claude_json(system, user_text, f"wa-sum-{conv_id}")
    return {"summary": _wa_clean_line(result.get("summary", "")),
            "next_step": _wa_clean_line(result.get("next_step", "")),
            "temperature": result.get("temperature")}

# -------- Appointment (showroom visit) --------
@api_router.post("/whatsapp/conversations/{conv_id}/appointment")
async def wa_book_appointment(conv_id: str, req: WAAppointmentCreate, current_user: dict = Depends(get_current_user)):
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")
    conv = await mongo_db.brandsxai_wa_conversations.find_one({"id": conv_id})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    now = datetime.now(timezone.utc)
    appt = {
        "id": str(uuid.uuid4()), "conversation_id": conv_id, "brand_id": conv.get("brand_id"),
        "lead_name": conv.get("lead_name"), "lead_phone": conv.get("lead_phone"),
        "date": req.date, "time": req.time, "status": "scheduled", "notes": req.notes,
        "created_at": now.isoformat()
    }
    await mongo_db.brandsxai_wa_appointments.insert_one(appt)
    # Send a confirmation message + move stage to Visit Confirmed.
    # The fest is walk-in, so this is not a reserved slot - it records the day the customer
    # said they would come so the rep can remind them.
    confirm = (
        f"Wonderful! We have noted your visit for {req.date}, around {req.time}. No booking needed - "
        f"just walk in any time between 11 AM and 9 PM. See you at {WA_BRAND_NAME}!"
    )
    send_res = await wa_send_text(conv["lead_phone"], confirm)
    msg = {
        "id": str(uuid.uuid4()), "conversation_id": conv_id, "direction": "outbound",
        "sender_type": "human", "content": confirm, "msg_type": "text", "media_url": None,
        "status": "sent", "wa_message_id": send_res.get("message_id"),
        "simulated": send_res.get("simulated", False), "created_at": now.isoformat()
    }
    await mongo_db.brandsxai_wa_messages.insert_one(msg)
    await mongo_db.brandsxai_wa_conversations.update_one(
        {"id": conv_id}, {"$set": {"stage": "Visit Confirmed", "last_message": confirm[:120],
                                    "last_message_at": now.isoformat(), "updated_at": now.isoformat()}}
    )
    appt.pop("_id", None)
    msg.pop("_id", None)
    return {"appointment": appt, "message": msg}

# -------- Webhook (public, no auth) --------

# -------- Connection diagnostics (validates Meta credentials live) --------
def _wa_token_shape(tok: str) -> dict:
    """Surface-level shape info for the access token.

    NOTE: do NOT infer corruption from the absence of '_' / '-'. Meta system-user
    tokens legitimately contain none. Validity is decided only by the live Graph
    API call below.
    """
    if not tok:
        return {"present": False}
    return {
        "present": True,
        "length": len(tok),
        "prefix": tok[:8],
        "starts_with_EAA": tok.startswith("EAA"),
        "charset_valid_base64url": bool(re.fullmatch(r"[A-Za-z0-9_\-]+", tok)),
    }


@api_router.get("/whatsapp/status")
async def wa_status(current_user: dict = Depends(get_current_user)):
    """Live health check of the WhatsApp Business (Meta Cloud API) connection.

    Verifies the access token against Meta, returns the verified business profile,
    quality rating and the REAL approved template list from the WABA, plus a
    format check of the app secret / verify token and the exact webhook URL to
    register in the Meta dashboard.
    """
    if not current_user or current_user.get('type') == 'admin':
        raise HTTPException(status_code=403, detail="User access required")

    c = wa_config()
    secret = c["app_secret"]
    base = (os.environ.get("PUBLIC_BASE_URL", "") or "").strip().rstrip("/")

    result = {
        "live_mode": wa_is_live(),
        "graph_version": c["version"],
        "config": {
            "phone_number_id": c["phone_number_id"] or None,
            "access_token": _wa_token_shape(c["token"]),
            "app_secret": {
                "present": bool(secret),
                "length": len(secret),
                # Meta app secrets are exactly 32 lowercase hex chars
                "valid_format": bool(re.fullmatch(r"[0-9a-fA-F]{32}", secret or "")),
            },
            "verify_token": {"present": bool(c["verify_token"]), "length": len(c["verify_token"])},
        },
        "webhook": {
            "callback_url": (f"{base}/api/whatsapp/webhook" if base else "/api/whatsapp/webhook"),
            "verify_token_to_use": c["verify_token"] or None,
            "subscribe_to_field": "messages",
        },
        "token_valid": False,
        "phone_number": None,
        "waba_ids": [],
        "approved_templates": [],
        "webhook_traffic": dict(WA_WEBHOOK_STATS),
        "errors": [],
        "checks": [],
    }

    def _chk(name, ok, detail=""):
        result["checks"].append({"check": name, "ok": bool(ok), "detail": detail})

    # Does the app secret actually belong to the app that owns this WABA?
    secret_state = await wa_check_app_secret()
    result["config"]["app_secret"]["matches_app"] = secret_state.get("valid")
    result["config"]["app_secret"]["app_id"] = secret_state.get("app_id")
    result["config"]["app_secret"]["detail"] = secret_state.get("detail")
    result["signature_mode"] = (os.environ.get("WA_REQUIRE_SIGNATURE", "auto").strip().lower() or "auto")
    if secret_state.get("valid") is False:
        _chk("app_secret_matches_app", False, secret_state.get("detail") or "")
    elif secret_state.get("valid") is True:
        _chk("app_secret_matches_app", True, secret_state.get("detail") or "")

    # Surface webhook signature failures - the classic "wrong app secret" symptom, which
    # otherwise silently drops every inbound message and delivery receipt.
    if WA_WEBHOOK_STATS["signature_fail_count"] > 0 and WA_WEBHOOK_STATS["signature_ok_count"] == 0:
        _chk("webhook_signature", False,
             f"{WA_WEBHOOK_STATS['signature_fail_count']} webhook(s) from Meta were REJECTED for "
             f"signature mismatch. META_APP_SECRET does not match the app that owns this WABA.")
    elif WA_WEBHOOK_STATS["signature_ok_count"] > 0:
        _chk("webhook_signature", True,
             f"{WA_WEBHOOK_STATS['signature_ok_count']} verified webhook(s) received")

    _chk("phone_number_id_set", bool(c["phone_number_id"]),
         "Set WHATSAPP_PHONE_NUMBER_ID" if not c["phone_number_id"] else "")
    _chk("access_token_set", bool(c["token"]), "Set META_ACCESS_TOKEN" if not c["token"] else "")
    _chk("app_secret_format", result["config"]["app_secret"]["valid_format"],
         "META_APP_SECRET must be the 32-char hex App Secret (Settings > Basic > App Secret). "
         "A wrong value makes Meta's real webhooks fail signature checks with 403."
         if not result["config"]["app_secret"]["valid_format"] else "")
    _chk("verify_token_set", bool(c["verify_token"]), "Set WEBHOOK_VERIFY_TOKEN" if not c["verify_token"] else "")
    _chk("token_charset", result["config"]["access_token"].get("charset_valid_base64url", False),
         "Token contains characters outside the base64url alphabet - it was likely truncated or "
         "mangled in transit." if not result["config"]["access_token"].get("charset_valid_base64url") else "")

    if not wa_is_live():
        result["errors"].append("Not configured - running in SIMULATION mode.")
        _chk("meta_reachable", False, "Skipped, credentials incomplete")
        return result

    import httpx
    headers = {"Authorization": f"Bearer {c['token']}"}
    try:
        async with httpx.AsyncClient(timeout=25) as client:
            # 1. Validate token + read the phone number node
            r = await client.get(
                f"https://graph.facebook.com/{c['version']}/{c['phone_number_id']}",
                headers=headers,
                params={"fields": "id,display_phone_number,verified_name,quality_rating,"
                                  "code_verification_status,platform_type,throughput"},
            )
            if r.status_code == 200:
                result["token_valid"] = True
                result["phone_number"] = r.json()
                _chk("meta_reachable", True, "Token accepted by Meta")
                _chk("phone_number_id_valid", True,
                     f"Verified name: {r.json().get('verified_name')}")
            else:
                err = (r.json() or {}).get("error", {})
                result["errors"].append({"stage": "phone_number_node", "http": r.status_code, "error": err})
                hint = ""
                if err.get("code") == 190:
                    msg = (err.get("message") or "").lower()
                    if "decrypted" in msg or "malformed" in msg:
                        hint = ("Token is malformed or revoked. Generate a fresh permanent System User "
                                "token (Business Settings > System Users) with whatsapp_business_messaging "
                                "+ whatsapp_business_management scopes.")
                    elif "expired" in msg:
                        hint = "Token has expired. Temporary tokens last 24h - generate a System User token."
                    else:
                        hint = "Token rejected by Meta (invalid, revoked, or wrong app)."
                _chk("meta_reachable", False, hint or str(err.get("message", ""))[:200])

            # 2. Discover WABA id(s) via token introspection, then list real templates
            if result["token_valid"]:
                waba_ids = []
                env_waba = (os.environ.get("WHATSAPP_WABA_ID", "") or "").strip()
                if env_waba:
                    waba_ids.append(env_waba)
                try:
                    d = await client.get(
                        f"https://graph.facebook.com/{c['version']}/debug_token",
                        headers=headers, params={"input_token": c["token"]},
                    )
                    if d.status_code == 200:
                        data = (d.json() or {}).get("data", {})
                        result["token_info"] = {
                            "app_id": data.get("app_id"),
                            "application": data.get("application"),
                            "type": data.get("type"),
                            "expires_at": data.get("expires_at"),
                            "never_expires": data.get("expires_at") == 0,
                            "scopes": data.get("scopes", []),
                        }
                        for gs in data.get("granular_scopes", []) or []:
                            if "whatsapp_business" in (gs.get("scope") or ""):
                                for t in gs.get("target_ids", []) or []:
                                    if t not in waba_ids:
                                        waba_ids.append(t)
                        _chk("token_never_expires", data.get("expires_at") == 0,
                             "Temporary token - it will stop working. Use a System User token for production."
                             if data.get("expires_at") != 0 else "")
                except Exception as e:
                    result["errors"].append({"stage": "debug_token", "error": str(e)[:200]})

                result["waba_ids"] = waba_ids
                for waba in waba_ids:
                    try:
                        t = await client.get(
                            f"https://graph.facebook.com/{c['version']}/{waba}/message_templates",
                            headers=headers, params={"fields": "name,status,category,language", "limit": 100},
                        )
                        if t.status_code == 200:
                            for tpl in (t.json() or {}).get("data", []):
                                result["approved_templates"].append({
                                    "waba_id": waba, "name": tpl.get("name"),
                                    "status": tpl.get("status"), "category": tpl.get("category"),
                                    "language": tpl.get("language"),
                                })
                        else:
                            result["errors"].append({"stage": f"templates:{waba}", "http": t.status_code,
                                                     "error": (t.json() or {}).get("error", {})})
                    except Exception as e:
                        result["errors"].append({"stage": f"templates:{waba}", "error": str(e)[:200]})
                approved = [t for t in result["approved_templates"] if t.get("status") == "APPROVED"]
                _chk("has_approved_templates", bool(approved),
                     "No APPROVED templates found - the first message to a new contact MUST be an "
                     "approved template." if not approved else f"{len(approved)} approved")
    except Exception as e:
        result["errors"].append({"stage": "network", "error": str(e)[:300]})
        _chk("meta_reachable", False, f"Network error: {str(e)[:160]}")

    result["ready_to_send"] = bool(result["token_valid"] and result["config"]["app_secret"]["valid_format"])
    return result


@api_router.get("/whatsapp/webhook")
async def wa_webhook_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    import hmac as _hmac
    c = wa_config()
    accepted = wa_verify_tokens()
    if hub_mode == "subscribe" and accepted and any(
        _hmac.compare_digest(hub_verify_token or "", t) for t in accepted
    ):
        logger.info("WA webhook verified successfully")
        return PlainTextResponse(content=hub_challenge or "")
    logger.warning(f"WA webhook verification FAILED (mode={hub_mode}, supplied_token_len={len(hub_verify_token or '')})")
    raise HTTPException(status_code=403, detail="Webhook verification failed")

WA_STATUS_RANK = {"failed": 0, "sent": 1, "delivered": 2, "read": 3}

# Lightweight in-process webhook telemetry, surfaced via GET /api/whatsapp/status
WA_WEBHOOK_STATS = {
    "last_received_at": None,
    "received_count": 0,
    "signature_ok_count": 0,
    "signature_fail_count": 0,
    "last_signature_error_at": None,
    "processed_messages": 0,
    "processed_statuses": 0,
    "adopted_external_outbound": 0,
    "last_error": None,
}

WA_EXTERNAL_OUTBOUND_PLACEHOLDER = "[sent outside the portal — WhatsApp does not report the text]"


async def _wa_adopt_external_outbound(status: dict, recv_pnid, recv_waba, now):
    """Create a local row for an outbound message that was sent outside this portal.

    Cloud API status webhooks are the only trace we ever get of a send made from Business
    Manager, an API client or another system, and they carry no message body, so the row is
    a placeholder whose purpose is to keep the thread chronologically complete rather than
    leave a silent gap. Returns None when the recipient cannot be resolved.
    """
    phone = _norm_phone(status.get("recipient_id"))
    wamid = status.get("id")
    if not phone or not wamid:
        return None
    # Same thread resolution as inbound: scoped to the business number that sent it, with a
    # fallback for threads created before we started stamping the receiving number.
    conv = await mongo_db.brandsxai_wa_conversations.find_one(
        {"lead_phone": phone, "wa_phone_number_id": recv_pnid})
    if not conv and recv_pnid:
        conv = await mongo_db.brandsxai_wa_conversations.find_one({
            "lead_phone": phone,
            "$or": [
                {"wa_phone_number_id": {"$in": [None, ""]}},
                {"wa_phone_number_id": {"$exists": False}},
            ],
        })
    if conv:
        conv_id = conv["id"]
    else:
        conv_id = str(uuid.uuid4())
        await mongo_db.brandsxai_wa_conversations.insert_one({
            "id": conv_id, "brand_id": wa_default_brand_id(), "lead_name": phone,
            "lead_phone": phone, "wa_phone_number_id": recv_pnid, "waba_id": recv_waba,
            "stage": "Contacted", "status": "open", "unread_count": 0,
            "temperature": "warm", "source": "external_outbound",
            "created_at": now.isoformat(), "updated_at": now.isoformat(),
        })
    # Order the message by when Meta acted on it, not when this webhook happened to arrive.
    try:
        created_at = datetime.fromtimestamp(int(status.get("timestamp")), timezone.utc).isoformat()
    except (TypeError, ValueError):
        created_at = now.isoformat()
    # Upsert, because sent/delivered/read for one wamid can arrive concurrently and only the
    # first of them may create the row.
    await mongo_db.brandsxai_wa_messages.update_one(
        {"wa_message_id": wamid},
        {"$setOnInsert": {
            "id": str(uuid.uuid4()), "conversation_id": conv_id, "direction": "outbound",
            "sender_type": "human", "content": WA_EXTERNAL_OUTBOUND_PLACEHOLDER,
            "msg_type": "text", "template_name": None, "media_url": None,
            "status": "sent", "wa_message_id": wamid, "wa_phone_number_id": recv_pnid,
            "origin": "external", "simulated": False, "created_at": created_at,
        }},
        upsert=True,
    )
    doc = await mongo_db.brandsxai_wa_messages.find_one({"wa_message_id": wamid})
    if doc and doc.get("origin") == "external":
        WA_WEBHOOK_STATS["adopted_external_outbound"] += 1
        logger.info(f"WA adopted externally-sent message {wamid} to {phone} -> conversation {conv_id}")
        await _wa_touch_conversation(conv_id, WA_EXTERNAL_OUTBOUND_PLACEHOLDER, "outbound")
    return doc


@api_router.post("/whatsapp/webhook")
async def wa_webhook_receive(request: Request):
    import hmac as _hmac, hashlib as _hashlib
    raw = await request.body()
    c = wa_config()
    now = datetime.now(timezone.utc)
    WA_WEBHOOK_STATS["received_count"] += 1
    WA_WEBHOOK_STATS["last_received_at"] = now.isoformat()

    # ---- Signature verification (HMAC-SHA256 of the RAW body with the app secret) ----
    # WA_REQUIRE_SIGNATURE:
    #   "true"  -> always reject a bad/missing signature (strictest)
    #   "false" -> never reject (debug only)
    #   "auto"  -> DEFAULT. Reject only when the app secret is PROVEN valid for the app that
    #              owns this WABA (so a mismatch is a real forgery). If Meta tells us the
    #              configured secret does not belong to that app, the signature can never
    #              match, so we accept the payload - but only if it concerns our own WABA /
    #              phone number - and scream about it in the logs and in /api/whatsapp/status.
    #              This stops a simple misconfiguration from silently destroying every
    #              inbound message and delivery receipt.
    mode = (os.environ.get("WA_REQUIRE_SIGNATURE", "auto").strip().lower() or "auto")
    secrets = wa_app_secrets()
    if secrets:
        supplied = request.headers.get("X-Hub-Signature-256", "")
        matched = False
        expected_first = ""
        for sec in secrets:
            expected = "sha256=" + _hmac.new(sec.encode(), raw, _hashlib.sha256).hexdigest()
            if not expected_first:
                expected_first = expected
            if supplied and _hmac.compare_digest(supplied, expected):
                matched = True
                break
        if matched:
            WA_WEBHOOK_STATS["signature_ok_count"] += 1
        else:
            WA_WEBHOOK_STATS["signature_fail_count"] += 1
            WA_WEBHOOK_STATS["last_signature_error_at"] = now.isoformat()
            secret_state = await wa_check_app_secret()
            WA_WEBHOOK_STATS["last_error"] = (
                "X-Hub-Signature-256 mismatch. " + (secret_state.get("detail") or "")
            )
            logger.error(
                "WA webhook SIGNATURE MISMATCH (mode=%s, app_secret_valid=%s). supplied=%s expected=%s body_len=%d",
                mode, secret_state.get("valid"), supplied[:25] or "<none>", expected_first[:25], len(raw),
            )
            reject = True
            if mode == "false":
                reject = False
            elif mode == "auto":
                # Only fail open when the secret is PROVEN wrong (so verification is impossible)
                if secret_state.get("valid") is False:
                    reject = False
            if reject:
                raise HTTPException(status_code=403, detail="Invalid signature")
            # Secondary guard: never ingest traffic that is not for our own WABA/number
            try:
                _probe = json.loads(raw.decode("utf-8"))
            except Exception:
                return {"ok": True}
            if not wa_payload_is_ours(_probe):
                logger.error("WA webhook rejected: unverified payload does not match our WABA/phone_number_id")
                raise HTTPException(status_code=403, detail="Invalid signature")
            logger.critical(
                "WA webhook ACCEPTED WITHOUT SIGNATURE VERIFICATION because META_APP_SECRET is wrong. "
                "FIX IT: %s", secret_state.get("detail"),
            )
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception:
        return {"ok": True}
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            # WHICH of our business numbers received this. A thread is scoped to
            # (customer number + our receiving number), so switching WhatsApp accounts
            # starts a clean thread instead of appending to the previous account's history.
            recv_pnid = str(((value.get("metadata") or {}).get("phone_number_id")) or "") or None
            recv_waba = str(entry.get("id") or "") or None
            # Map wa_id -> WhatsApp profile name so new threads get a real name, not a number
            profile_names = {}
            for ct in value.get("contacts", []) or []:
                nm = ((ct.get("profile") or {}).get("name") or "").strip()
                if ct.get("wa_id") and nm:
                    profile_names[_norm_phone(ct.get("wa_id"))] = nm
            for m in value.get("messages", []):
                wa_id = m.get("from")
                phone = _norm_phone(wa_id)
                mtype = m.get("type", "text")
                display_name = profile_names.get(phone) or phone
                conv = await mongo_db.brandsxai_wa_conversations.find_one(
                    {"lead_phone": phone, "wa_phone_number_id": recv_pnid})
                if not conv and recv_pnid:
                    # Same customer, thread created before we stamped the receiving number
                    conv = await mongo_db.brandsxai_wa_conversations.find_one({
                        "lead_phone": phone,
                        "$or": [
                            {"wa_phone_number_id": {"$in": [None, ""]}},
                            {"wa_phone_number_id": {"$exists": False}},
                        ],
                    })
                if not conv:
                    # create a bare conversation for unknown inbound
                    conv_id = str(uuid.uuid4())
                    conv = {"id": conv_id, "brand_id": wa_default_brand_id(), "lead_name": display_name, "lead_phone": phone,
                            "wa_phone_number_id": recv_pnid, "waba_id": recv_waba,
                            "stage": "Contacted", "status": "open", "unread_count": 0,
                            "temperature": "warm", "source": "inbound_webhook",
                            "created_at": now.isoformat(), "updated_at": now.isoformat()}
                    await mongo_db.brandsxai_wa_conversations.insert_one(conv)
                else:
                    conv_id = conv["id"]
                    stamp = {}
                    if recv_pnid and not conv.get("wa_phone_number_id"):
                        stamp["wa_phone_number_id"] = recv_pnid
                    if recv_waba and not conv.get("waba_id"):
                        stamp["waba_id"] = recv_waba
                    # Upgrade a placeholder name (bare phone number) to the real profile name
                    if display_name != phone and (conv.get("lead_name") or "") in ("", phone):
                        stamp["lead_name"] = display_name
                    if stamp:
                        await mongo_db.brandsxai_wa_conversations.update_one(
                            {"id": conv_id}, {"$set": stamp})
                existing = await mongo_db.brandsxai_wa_messages.find_one({"wa_message_id": m.get("id")})
                if existing:
                    continue
                # Resolve content + media for text and media message types
                media_url = None
                caption = ""
                if mtype == "text":
                    content = (m.get("text") or {}).get("body") or ""
                elif mtype in ("image", "video", "audio", "document", "sticker"):
                    media_obj = m.get(mtype) or {}
                    caption = media_obj.get("caption") or ""
                    content = caption
                    meta_media_id = media_obj.get("id")
                    # Live mode: download the media from Meta and serve it locally so it's viewable in the portal
                    if meta_media_id and wa_is_live():
                        try:
                            local = await _wa_download_meta_media(meta_media_id, media_obj.get("mime_type"))
                            if local:
                                media_url = local
                        except Exception as e:
                            logger.error(f"WA media download error: {e}")
                    if not content:
                        content = f"[{mtype}]"
                elif mtype == "reaction":
                    content = (m.get("reaction") or {}).get("emoji") or "[reaction]"
                elif mtype == "location":
                    loc = m.get("location") or {}
                    content = loc.get("name") or f"[location {loc.get('latitude')},{loc.get('longitude')}]"
                elif mtype in ("button", "interactive"):
                    obj = m.get(mtype) or {}
                    content = obj.get("text") or json.dumps(obj)[:150]
                else:
                    content = m.get(mtype, {}).get("body", f"[{mtype}]") if isinstance(m.get(mtype), dict) else f"[{mtype}]"
                await mongo_db.brandsxai_wa_messages.insert_one({
                    "id": str(uuid.uuid4()), "conversation_id": conv_id, "direction": "inbound",
                    "sender_type": "customer", "content": content, "msg_type": mtype,
                    "media_url": media_url, "status": "delivered", "wa_message_id": m.get("id"),
                    "wa_phone_number_id": recv_pnid,
                    "simulated": False, "created_at": now.isoformat()
                })
                WA_WEBHOOK_STATS["processed_messages"] += 1
                logger.info(f"WA inbound {mtype} from {phone} -> conversation {conv_id}")
                preview = (f"[{mtype}]" + (f" {caption}" if caption else "")) if media_url or mtype != "text" else content
                await _wa_touch_conversation(conv_id, preview, "inbound")
            for status in value.get("statuses", []):
                new_status = status.get("status")
                wamid = status.get("id")
                if not wamid or not new_status:
                    continue
                doc = await mongo_db.brandsxai_wa_messages.find_one({"wa_message_id": wamid})
                if not doc:
                    # Never seen this id, so the message was sent outside the portal. Record it
                    # instead of dropping it, otherwise the send is invisible in the inbox.
                    doc = await _wa_adopt_external_outbound(status, recv_pnid, recv_waba, now)
                if not doc:
                    continue
                # Meta retries arrive OUT OF ORDER, so never downgrade read -> delivered -> sent
                cur_rank = WA_STATUS_RANK.get(doc.get("status"), -1)
                new_rank = WA_STATUS_RANK.get(new_status, -1)
                set_fields = {f"status_timestamps.{new_status}": status.get("timestamp")}
                if new_status == "failed":
                    set_fields["status"] = "failed"
                    set_fields["error"] = (status.get("errors") or [{}])[0]
                    logger.error(f"WA message {wamid} FAILED: {status.get('errors')}")
                elif new_rank > cur_rank:
                    set_fields["status"] = new_status
                if status.get("pricing"):
                    set_fields["pricing"] = status.get("pricing")
                if status.get("conversation"):
                    set_fields["wa_conversation"] = status.get("conversation")
                await mongo_db.brandsxai_wa_messages.update_one({"wa_message_id": wamid}, {"$set": set_fields})
                WA_WEBHOOK_STATS["processed_statuses"] += 1
                logger.info(f"WA status {new_status} for {wamid} (was {doc.get('status')})")
                conv = await mongo_db.brandsxai_wa_conversations.find_one(
                    {"id": doc.get("conversation_id")}, {"_id": 0, "brand_id": 1})
                wa_publish({
                    "type": "status", "conversation_id": doc.get("conversation_id"),
                    "brand_id": (conv or {}).get("brand_id"), "wa_message_id": wamid,
                    "status": new_status, "at": now.isoformat(),
                })
    return {"ok": True}


# ==================== UTILITY ====================

@api_router.get("/")
async def root():
    return {"message": "BrandsXAI API", "version": "2.0.0"}

@api_router.get("/db-status")
async def db_status():
    mysql_status = try_mysql_connection() is not None
    return {"mysql_available": mysql_status, "mongodb_available": True, "primary_db": "mysql" if mysql_status else "mongodb"}

# Include router & middleware
app.include_router(api_router)
app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
async def startup_event():
    # Probe MySQL once off the event loop (so startup never blocks), then keep probing in the background
    await asyncio.to_thread(_probe_mysql)
    start_mysql_prober()
    mysql_conn = try_mysql_connection()
    if mysql_conn:
        init_mysql_tables(mysql_conn)
        mysql_conn.close()
    await init_mongodb_collections()
    logger.info("Database initialization complete")
    await _wa_validate_default_brand()
    await _wa_backfill_account_tags()
