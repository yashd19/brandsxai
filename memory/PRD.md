# MadOver AI - Product Requirements Document

## Project Overview
MadOver AI is a landing page for a tech platform that enables brands to leverage AI technologies. The website showcases the company's services, case studies, and provides a lead capture mechanism with user authentication.

## Original Problem Statement
Build a landing page for MadOver AI platform with:
- Hero section with animated product cards
- Metrics section showing key business numbers
- Case study section with category tabs
- Contact form for lead capture
- User authentication (Login only, no signup)
- MySQL database integration with `brandsxai_` prefix tables
- About Us page

## Database Schema

### Tables (MySQL - `brandsxai_` prefix)

**brandsxai_users**
| Column | Type | Description |
|--------|------|-------------|
| id | INT AUTO_INCREMENT | Primary Key |
| username | VARCHAR(100) UNIQUE | Login username (indexed) |
| email | VARCHAR(255) | Optional email |
| password_hash | VARCHAR(255) | Bcrypt hashed password |
| created_at | TIMESTAMP | Account creation time |
| last_login | TIMESTAMP | Last login timestamp |
| is_active | BOOLEAN | Account status |

**brandsxai_leads**
| Column | Type | Description |
|--------|------|-------------|
| id | INT AUTO_INCREMENT | Primary Key |
| name | VARCHAR(255) | Contact name |
| email | VARCHAR(255) | Contact email (indexed) |
| company | VARCHAR(255) | Company name |
| message | TEXT | Message |
| created_at | TIMESTAMP | Submission time |

## Performance Strategy
- **JWT Tokens**: Stateless authentication (24hr expiration)
- **Bcrypt cost factor 12**: Secure password hashing
- **Indexed columns**: username, email for fast lookups
- **MongoDB fallback**: For testing when MySQL unavailable
- **Connection reuse**: Efficient database connections

## Implementation Status

### Completed
- [x] Hero section with animated floating product cards
- [x] Metrics section with statistics
- [x] Case studies section with pill-style category tabs
- [x] Case study card with background image and white content overlay
- [x] Navigation sidebar with Home, About Us (brain), Contact Us (rocket), Sign In
- [x] Hover tooltips on sidebar icons
- [x] Login page (no signup) - Username/Password
- [x] JWT authentication backend
- [x] Contact page for brand inquiries
- [x] Footer with subtle separator line

### Test Credentials
- **Username:** `admin`
- **Password:** `admin123`

### Pending - Requires User Action
- [ ] **MySQL Database Access**: The AWS RDS instance needs to allow connections from the Emergent preview environment. Update the RDS security group to allow inbound traffic.

### Future Tasks (P2)
- [ ] About Us page content
- [ ] Case study detail pages
- [ ] Admin dashboard for viewing leads
- [ ] User management

## API Endpoints
- `GET /api/` - Health check
- `POST /api/auth/login` - User login (returns JWT)
- `GET /api/auth/me` - Get current user
- `POST /api/leads` - Create new lead
- `GET /api/leads` - Get all leads (requires auth)
- `GET /api/mysql-status` - Check MySQL connection

## MySQL Configuration
```
Host: madoverai.cdam6io6a2o3.eu-north-1.rds.amazonaws.com
Port: 13306
User: admin
Database: madoverai
Tables: brandsxai_users, brandsxai_leads
```

## Technical Stack
- **Frontend**: React, Tailwind CSS, Lucide Icons
- **Backend**: FastAPI, Python, JWT, Bcrypt
- **Database**: MySQL (primary), MongoDB (fallback)
- **Deployment**: Emergent Platform

## Notes
- Authentication currently uses MongoDB fallback since MySQL RDS is not accessible from preview environment
- Once RDS security groups are updated, authentication will automatically use MySQL
- All backend code is ready for MySQL - no code changes needed
