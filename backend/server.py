from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import pymysql


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# MySQL connection configuration
MYSQL_CONFIG = {
    'host': os.environ.get('MYSQL_HOST', 'madoverai.cdam6io6a2o3.eu-north-1.rds.amazonaws.com'),
    'port': int(os.environ.get('MYSQL_PORT', 13306)),
    'user': os.environ.get('MYSQL_USER', 'admin'),
    'password': os.environ.get('MYSQL_PASSWORD', 'm94IHMwmhb1SHItnl3zP'),
    'database': os.environ.get('MYSQL_DATABASE', 'madoverai'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
    'connect_timeout': 10,
    'read_timeout': 30,
    'write_timeout': 30
}

# MySQL connection status
mysql_available = False

def get_mysql_connection():
    """Get MySQL database connection"""
    global mysql_available
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        mysql_available = True
        return conn
    except pymysql.Error as e:
        mysql_available = False
        raise e

def init_mysql_database():
    """Initialize MySQL database with required tables"""
    global mysql_available
    try:
        connection = get_mysql_connection()
        try:
            with connection.cursor() as cursor:
                # Create leads table if not exists
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS leads (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        email VARCHAR(255) NOT NULL,
                        company VARCHAR(255),
                        message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                connection.commit()
            mysql_available = True
        finally:
            connection.close()
    except pymysql.Error as e:
        mysql_available = False
        raise e

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

# Lead Models for MySQL
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

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

# Lead endpoints (MySQL)
@api_router.post("/leads", response_model=Lead)
async def create_lead(lead: LeadCreate):
    """Create a new lead from contact form submission"""
    connection = get_mysql_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO leads (name, email, company, message)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (lead.name, lead.email, lead.company, lead.message))
            connection.commit()
            
            # Get the inserted lead
            lead_id = cursor.lastrowid
            cursor.execute("SELECT * FROM leads WHERE id = %s", (lead_id,))
            result = cursor.fetchone()
            
            return Lead(**result)
    except pymysql.Error as e:
        logger.error(f"MySQL error creating lead: {e}")
        raise HTTPException(status_code=500, detail="Failed to create lead")
    finally:
        connection.close()

@api_router.get("/leads", response_model=List[Lead])
async def get_leads():
    """Get all leads"""
    connection = get_mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM leads ORDER BY created_at DESC")
            results = cursor.fetchall()
            return [Lead(**row) for row in results]
    except pymysql.Error as e:
        logger.error(f"MySQL error fetching leads: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch leads")
    finally:
        connection.close()

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize databases on startup"""
    try:
        # Initialize MySQL tables
        init_mysql_database()
        logger.info("MySQL database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize MySQL database: {str(e)}")