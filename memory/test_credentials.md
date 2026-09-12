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

## WhatsApp / Meta Cloud API (live creds in backend/.env)
- WHATSAPP_PHONE_NUMBER_ID: 1205736552634128
- WEBHOOK_VERIFY_TOKEN: brandsxai_wa_verify_7bK9mQ2xP4
- META_APP_SECRET: 7b28f01a1931401ed7a32b9000d83b7f  (32-char hex, VALID - signature checks verified)
- META_ACCESS_TOKEN: INVALID / CORRUPTED (Meta 401 code 190 "could not be decrypted") - user must re-copy. Outbound sends fail with 502 until replaced.
- WA_INGEST_TOKEN (X-Ingest-Token header): brandsxai_ingest_9fT3nQ8wZ1
- Webhook callback URL (public, verified reachable): https://f11fcb3b-5aba-4b2b-a12a-6a2028a9906c.preview.emergentagent.com/api/whatsapp/webhook
- Prod test recipient number: +1 201 268 8622 (E.164 12012688622)
- Diagnostics: GET /api/whatsapp/status (auth as testuser/test123)
