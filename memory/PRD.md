# MadOver AI - Product Requirements Document

## Project Overview
MadOver AI is a multi-tenant SaaS platform that enables brands to leverage AI technologies. The platform features a landing page showcasing services, case studies, lead capture, and a full role-based access control (RBAC) system with dynamic dashboards.

## Original Problem Statement
Build a comprehensive tech platform for MadOver AI with:
- Landing page with hero section, metrics, and case studies
- Contact page for lead capture
- Multi-tenant authentication system (Admin + Brand Users)
- Dynamic dashboard with feature-based access control
- Campaign Management with Kanban-style Lead Opportunity Tracker
- MySQL database integration with MongoDB fallback

## User Personas
1. **MadOver AI Admins**: Internal employees who manage brands, users, and feature access
2. **Brand Users**: Client employees who access features assigned to their brand

## Database Schema

### Core Tables (MySQL/MongoDB - `brandsxai_` prefix)

| Table | Description |
|-------|-------------|
| brandsxai_admins | MadOver AI internal admin accounts |
| brandsxai_brands | Customer/Brand organizations |
| brandsxai_features | Available platform features (Voice AI, Claim Processing, etc.) |
| brandsxai_feature_pages | Pages within each feature |
| brandsxai_users | Brand user accounts |
| brandsxai_user_features | User-to-feature access mapping |
| brandsxai_campaigns | Voice AI campaigns |
| brandsxai_opportunities | Lead opportunities for campaigns |
| brandsxai_leads | Contact form submissions |

## Implementation Status

### Completed ✅
- [x] Landing page (HomeNew.jsx) with hero, metrics, case studies
- [x] Navigation sidebar with tooltips
- [x] Contact page for lead capture
- [x] Separate admin login (/admin/login) and user login (/login)
- [x] Admin Portal for user/brand/feature management
- [x] Multi-tenant RBAC system
- [x] Dynamic Dashboard with feature sidebar and page tabs
- [x] **Campaign Management Feature (NEW)**
  - [x] Campaign list view with cards
  - [x] Create Campaign modal
  - [x] Kanban board with 6 stages (Dialing, Interested, Not Interested, Call back, Store Visit, Invalid Number)
  - [x] Opportunity cards with avatar, value, action icons
  - [x] Drag-and-drop between stages
  - [x] Add Opportunity modal
  - [x] Search and filter controls
- [x] JWT authentication
- [x] MySQL-first, MongoDB-fallback database strategy

### Test Credentials
| Login | Username | Password |
|-------|----------|----------|
| Admin Portal | madoveradmin | admin@123 |
| Brand User | mukesh | mukesh123 |

### Pending Tasks
- [ ] **P1**: Populate Contacts, Dashboards, Session pages (Voice AI feature)
- [ ] **P2**: About Us page content
- [ ] **P2**: Case study detail pages
- [ ] **P2**: Refactor server.py into modular routers
- [ ] **P2**: Refactor HomeNew.jsx into smaller components

### Known Issues
- **MySQL Connection**: AWS RDS instance not accessible from preview environment. MongoDB fallback is active and stable.

## API Endpoints

### Authentication
- `POST /api/admin/login` - Admin login
- `POST /api/auth/login` - Brand user login

### Admin Portal
- `GET /api/admin/users` - List all users
- `POST /api/admin/users` - Create user
- `PUT /api/admin/users/{id}/features` - Update user features
- `DELETE /api/admin/users/{id}` - Deactivate user
- `GET /api/admin/brands` - List brands
- `POST /api/admin/brands` - Create brand
- `GET /api/admin/features` - List features

### Campaigns
- `GET /api/campaigns` - List campaigns (brand-filtered)
- `POST /api/campaigns` - Create campaign
- `GET /api/campaigns/{id}` - Get campaign with opportunities
- `POST /api/campaigns/{id}/opportunities` - Add opportunity
- `PUT /api/opportunities/{id}/stage` - Update opportunity stage (drag-drop)

### Other
- `POST /api/leads` - Submit contact form
- `GET /api/db-status` - Check database status

## Technical Architecture

### Frontend
- **Framework**: React 18
- **Styling**: Tailwind CSS, Custom CSS modules
- **Icons**: Lucide React
- **Components**: Shadcn/UI
- **State**: React hooks, localStorage for auth

### Backend
- **Framework**: FastAPI
- **Auth**: JWT with 24hr expiration
- **Password**: Bcrypt with cost factor 12
- **Database**: MySQL (primary), MongoDB (fallback)

### Key Files
- `/app/backend/server.py` - API server (1000+ lines)
- `/app/frontend/src/pages/Dashboard.jsx` - Main dashboard container
- `/app/frontend/src/pages/Campaign.jsx` - Campaign management UI
- `/app/frontend/src/pages/AdminPortal.jsx` - Admin management UI
- `/app/frontend/src/pages/HomeNew.jsx` - Landing page

## Test Coverage
- **Backend**: 9 pytest tests for campaign APIs
- **Frontend**: 15 Playwright E2E tests across 3 spec files
- Test files located in `/app/tests/e2e/` and `/app/backend/tests/`

## Notes
- All data is brand-isolated (multi-tenant)
- MongoDB fallback ensures development continuity
- Campaign feature matches user's reference Kanban UI
