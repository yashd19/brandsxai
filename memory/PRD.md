# BrandsXAI - Product Requirements Document

## Project Overview
BrandsXAI is a multi-tenant SaaS platform for Voice AI calling campaigns. Features landing page, admin portal, and role-based dashboards.

## User Personas
1. **BrandsXAI Admins**: Manage brands, users, and feature access
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
  - [x] **"Dial with AI" button** in opportunity modal (for dialing stage contacts) - INTEGRATED with real AI calling API
  - [x] **Phone number validation** - 10 digit check before allowing calls
- [x] **Session Page** (light theme)
  - [x] Stats cards (Total Calls, Duration, Average)
  - [x] Active Calls chart with line graph
  - [x] Calls with Issues chart
  - [x] Calls table with sortable columns
  - [x] Filters and search
- [x] **Contacts Page**
  - [x] Consolidated view of all contacts/opportunities
  - [x] Backend endpoint /api/contacts
- [x] **KPI Dashboard** (March 2026)
  - [x] Call Success Rate gauge chart
  - [x] Call Outcomes donut chart
  - [x] Call Status donut chart  
  - [x] Top Campaigns table
  - [x] Total Call Minutes
  - [x] Contacts by Stage donut chart
  - [x] Quick stats row (Total Contacts, In Queue, Converted, Avg Duration)
- [x] JWT authentication
- [x] MySQL-first, MongoDB-fallback strategy

### Test Credentials
| Login | Username | Password |
|-------|----------|----------|
| Admin Portal | madoveradmin | admin@123 |
| Brand User | mukesh | mukesh123 |

### Completed (March 2026 Session)
- [x] **FoundAI Product Page** - Exact replica of user-provided HTML file
  - GEO (Generative Engine Optimization) landing page
  - Terminal simulation animation
  - All sections: Hero, Why GEO, Services, Process, GEO vs SEO, Who We Serve, Footer
  - Exact fonts (Syne, IBM Plex Mono, Instrument Serif) and colors (#C8F135 lime)
  - Grid background pattern and noise overlay
  - Updated with BrandsXAI header (Back to main site) and footer
- [x] **SettleAI Product Page** - Created from user-provided HTML file
- [x] **BravoAI Product Page** - Voice AI sales agent landing page
  - Converted from red color scheme to BrandsXAI lime color (#C8F135)
  - All sections: Hero, What We Do, How It Works, Lead Qualifier, Call Simulation, Who It's For
  - BrandsXAI header with "Back to main site" and footer
- [x] **AdornIQ Product Page** - Jewellery AI Suite landing page
  - Elegant gold color scheme preserved
  - Three product cards: Bridal Vision AI, InvenIQ, JewelMatch AI
  - BrandsXAI header with "Back to main site" and footer
- [x] **Landing Page Card Links** - Connected product cards to their pages
  - Bravo AI → /bravo-ai
  - InvenIQ AI → /adorniq
  - Bridal Vision AI → /adorniq
  - JewelMatch AI → /adorniq
- [x] **Claim Processing Feature** (March 16, 2026) - AI-powered ICD-10 code extraction
  - Full-featured UI with dark theme, chat interface, code pills panel
  - Upload clinical documents (PDF, images) for code extraction
  - AI-powered extraction using Gemini 2.5 Flash via emergentintegrations
  - Interactive code pills with remove (X) buttons
  - Manual code addition with ICD-10 search/autocomplete
  - Session history sidebar for previous sessions
  - Excel export functionality (.xlsx with single-row codes + detailed sheet)
  - Conversational AI refinement - ask questions, request corrections
  - Backend: 17 pytest tests, Frontend: 12 E2E Playwright tests
  - Feature assigned to user `mukesh` under "Claim Processing" sidebar

### Pending Tasks
- [ ] **P1**: AI Post-Call Processing (webhooks for call summaries/recordings)
- [ ] **P2**: About Us page content
- [ ] **P2**: Case study detail pages
- [ ] **P2**: Refactor server.py into modular routers
- [ ] **P3**: Real-time call updates via WebSocket
- [ ] **P3**: Call recording and summary integration (after call completion webhook)

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
- `POST /api/opportunities/{id}/dial` - **Initiate AI voice call** (integrated with external AI calling service)

### Contacts & Dashboard
- `GET /api/contacts` - Get all contacts for brand
- `GET /api/sessions/calls` - Get call sessions with stats

### Claim Processing
- `POST /api/claim-processing/sessions` - Create new session
- `GET /api/claim-processing/sessions` - List user's sessions
- `GET /api/claim-processing/sessions/{id}` - Get session with messages
- `POST /api/claim-processing/sessions/{id}/chat` - Send message, AI extracts codes
- `PUT /api/claim-processing/sessions/{id}/codes` - Update codes (add/remove)
- `GET /api/claim-processing/icd10/search?q=` - Search ICD-10 codes
- `GET /api/claim-processing/sessions/{id}/export` - Download Excel file

## Key Files
- `/app/backend/server.py` - API server
- `/app/frontend/src/pages/Campaign.jsx` - Campaign management
- `/app/frontend/src/pages/Session.jsx` - Session analytics
- `/app/frontend/src/pages/Contacts.jsx` - All contacts view
- `/app/frontend/src/pages/Dashboards.jsx` - KPI Dashboard with charts
- `/app/frontend/src/pages/Dashboard.jsx` - Dashboard container
- `/app/frontend/src/pages/ClaimProcessing.jsx` - ICD-10 Code Extractor UI
- `/app/frontend/src/pages/ClaimProcessing.css` - Claim Processing styles
- `/app/frontend/src/pages/FoundAI.jsx` - FoundAI GEO product page
- `/app/frontend/src/pages/FoundAI.css` - FoundAI styles (exact replica)
- `/app/frontend/src/pages/SettleAI.jsx` - SettleAI product page
- `/app/frontend/src/pages/SettleAI.css` - SettleAI styles
- `/app/frontend/src/pages/BravoAI.jsx` - BravoAI Voice AI page
- `/app/frontend/src/pages/BravoAI.css` - BravoAI styles (lime color)
- `/app/frontend/src/pages/AdornIQ.jsx` - AdornIQ Jewellery Suite page
- `/app/frontend/src/pages/AdornIQ.css` - AdornIQ styles (gold color)

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
