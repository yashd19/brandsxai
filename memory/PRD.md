# MadOver AI - Product Requirements Document

## Project Overview
MadOver AI is a multi-tenant SaaS platform for Voice AI calling campaigns. Features landing page, admin portal, and role-based dashboards.

## User Personas
1. **MadOver AI Admins**: Manage brands, users, and feature access
2. **Brand Users**: Access features assigned to their brand

## Database Schema (brandsxai_ prefix)
- `brandsxai_admins` - Admin accounts
- `brandsxai_brands` - Customer organizations
- `brandsxai_features` - Platform features
- `brandsxai_feature_pages` - Pages within features
- `brandsxai_users` - Brand user accounts
- `brandsxai_user_features` - User feature access
- `brandsxai_campaigns` - Voice AI campaigns
- `brandsxai_opportunities` - Lead opportunities (with call_summary, recording_url, call_duration, call_outcome, last_called_at)
- `brandsxai_calls` - Call session logs
- `brandsxai_leads` - Contact form submissions

## Implementation Status

### Completed ✅
- [x] Landing page with hero, metrics, case studies
- [x] Contact page for lead capture
- [x] Admin Portal (/admin/login) - user/brand/feature management
- [x] Brand User Login (/login)
- [x] Multi-tenant RBAC system
- [x] Dynamic Dashboard with feature sidebar and page tabs
- [x] **Campaign Management Feature**
  - [x] Campaign list with cards (text overflow fixed)
  - [x] Create Campaign modal
  - [x] Kanban board with 6 stages
  - [x] Opportunity cards with action icons
  - [x] Drag-and-drop between stages
  - [x] Opportunity detail modal (contact info, call recording, AI summary, notes, timeline)
  - [x] **CSV Bulk Import** with preview
  - [x] **"Trigger AI Calls"** button (structure ready for integration)
  - [x] **List View Toggle** with table display
  - [x] **Advanced Filters** (only in list view) - Stage, Has Recording
  - [x] Sort functionality
- [x] **Session Page** (dark theme)
  - [x] Stats cards (Total Calls, Duration, Average)
  - [x] Active Calls chart with line graph
  - [x] Calls with Issues chart
  - [x] Calls table with sortable columns
  - [x] Filters and search
- [x] JWT authentication
- [x] MySQL-first, MongoDB-fallback strategy

### Test Credentials
| Login | Username | Password |
|-------|----------|----------|
| Admin Portal | madoveradmin | admin@123 |
| Brand User | mukesh | mukesh123 |

### Pending Tasks
- [ ] **P1**: Integrate actual AI calling service (API endpoint ready)
- [ ] **P1**: Populate Contacts, Dashboards pages
- [ ] **P2**: About Us page content
- [ ] **P2**: Case study detail pages
- [ ] **P2**: Refactor server.py into modular routers
- [ ] **P3**: Real-time call updates via WebSocket

### Known Issues
- MySQL RDS connection blocked (MongoDB fallback active)

## API Endpoints

### Authentication
- `POST /api/admin/login` - Admin login
- `POST /api/auth/login` - Brand user login

### Campaigns
- `GET /api/campaigns` - List campaigns
- `POST /api/campaigns` - Create campaign
- `GET /api/campaigns/{id}` - Get campaign with opportunities
- `POST /api/campaigns/{id}/opportunities` - Add opportunity
- `PUT /api/opportunities/{id}/stage` - Update stage (drag-drop)
- `GET /api/opportunities/{id}` - Get opportunity details
- `PUT /api/opportunities/{id}` - Update opportunity (call_summary, recording_url, etc.)

### Sessions
- `GET /api/sessions/calls` - Get call sessions with stats

## Key Files
- `/app/backend/server.py` - API server
- `/app/frontend/src/pages/Campaign.jsx` - Campaign management
- `/app/frontend/src/pages/Campaign.css` - Campaign styles
- `/app/frontend/src/pages/Session.jsx` - Session page (dark theme)
- `/app/frontend/src/pages/Session.css` - Session styles
- `/app/frontend/src/pages/Dashboard.jsx` - Dashboard container

## AI Integration Structure (Ready for Implementation)
When AI calling service is integrated:
1. User uploads CSV or adds opportunities manually
2. Opportunities start in "Dialing" stage
3. Click "Trigger AI Calls" to initiate calls
4. After each call, backend webhook updates:
   - `call_summary` - AI-generated summary
   - `recording_url` - S3 link to recording
   - `call_duration` - Duration in seconds
   - `call_outcome` - Result of call
   - `stage` - Move to appropriate stage based on outcome
5. Session page shows real-time call logs

## Technical Stack
- **Frontend**: React 18, Tailwind CSS, Lucide React
- **Backend**: FastAPI, Python
- **Database**: MySQL (primary), MongoDB (fallback)
- **Auth**: JWT (24hr expiration)
