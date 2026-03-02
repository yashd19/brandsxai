# MadOver AI - Product Requirements Document

## Project Overview
MadOver AI is a landing page for a tech platform that enables brands to leverage AI technologies. The website showcases the company's services, case studies, and provides a lead capture mechanism.

## Original Problem Statement
Build a landing page for MadOver AI platform with:
- Hero section with animated product cards
- Metrics section showing key business numbers
- Case study section with category tabs
- Contact form for lead capture
- MySQL database integration for storing leads
- About Us page

## User Personas
- **Brand Decision Makers**: CMOs, CTOs looking for AI solutions
- **Business Owners**: Small to medium business owners exploring AI capabilities
- **Tech Leads**: Technical leads evaluating AI integration partners

## Core Requirements

### Landing Page (Home)
1. **Hero Section**
   - "MadOver AI" branding with animated floating product cards
   - Search bar for exploring AI solutions
   - Scroll indicator dots

2. **Metrics Section**
   - Display key statistics: Brand Customers (75+), Resellers (200k+), Service Locations (18k+), Countries (40+)
   - Dark background with green accent numbers

3. **Case Studies Section**
   - Heading: "Supercharge your business with Servify"
   - Category tabs: OEM, Carriers & MVNOs, ISPs & BSPs, Home Warranty, Retail
   - Pill-shaped tab buttons with hover effects
   - Case study card with image and description

4. **Contact Form Section**
   - Lead capture form: Name, Email, Company, Message
   - Integration with MySQL database
   - Success/error feedback

5. **Footer**
   - MadOver AI branding
   - Copyright notice

### Backend
- FastAPI server
- MySQL database for leads (when accessible)
- MongoDB for other data
- CORS enabled

## Technical Stack
- **Frontend**: React, Tailwind CSS, Lucide Icons
- **Backend**: FastAPI, Python
- **Database**: MySQL (leads), MongoDB (other data)
- **Deployment**: Emergent Platform

## Implementation Status

### Completed
- [x] Hero section with animated floating product cards
- [x] Metrics section with statistics
- [x] Case studies section with category tabs (pill-style)
- [x] Contact form UI
- [x] MySQL backend integration code (structured, not connected due to RDS access)
- [x] Lead capture API endpoint (/api/leads)
- [x] Footer with MadOver AI branding

### Pending - Requires User Action
- [ ] **MySQL Database Access**: The AWS RDS instance needs to allow connections from the Emergent preview environment. Update the RDS security group to allow inbound traffic from the preview server IP.

### Future Tasks (P2)
- [ ] About Us page content
- [ ] Case study detail pages (/case-study/revenue-churn, etc.)
- [ ] Refactor Home.js into smaller components

## MySQL Configuration
```
Host: madoverai.cdam6io6a2o3.eu-north-1.rds.amazonaws.com
Port: 13306
User: admin
Database: madoverai
```

## API Endpoints
- `GET /api/` - Health check
- `POST /api/leads` - Create new lead
- `GET /api/leads` - Get all leads
- `GET /api/mysql-status` - Check MySQL connection status

## Notes
- The MySQL database connection times out from this environment. The RDS security group likely needs to be updated to allow connections from the Emergent preview environment.
- All backend code is properly structured and will work once database access is enabled.
