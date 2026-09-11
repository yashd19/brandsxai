# Test Credentials

Login lookup order: MySQL first, then MongoDB fallback (MySQL RDS currently blocked, so Mongo is used).

## Admin Portal (/admin/login)
- Username: madoveradmin
- Password: admin@123

## Brand User Login (/login)
- Username: mukesh
- Password: mukesh123
- Brand: Brand X | Features: Voice AI, Claim Processing, WhatsApp AI

## Dedicated Test User (/login) - seeded in MongoDB (works even when MySQL is down)
- Username: testuser
- Password: test123
- Brand: Brand X | Features: Voice AI, Claim Processing, WhatsApp AI
