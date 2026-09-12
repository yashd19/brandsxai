# Test Credentials

## >>> APP URL (open THIS in the browser) <<<
https://f11fcb3b-5aba-4b2b-a12a-6a2028a9906c.preview.emergentagent.com/login

DO NOT open https://shily-orthopneic-shawnna.ngrok-free.dev in a browser - that ngrok
tunnel points at port 8001 (the BACKEND API only) and is used solely for Meta webhooks.
It has no UI and will just return JSON / 404 for /login.

All three logins below were verified working by the frontend testing agent.

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

## WhatsApp / Meta Cloud API - LIVE & WORKING (backend/.env)
- Business: "Swad Mania" | display number +1 551-550-6716 | quality GREEN | CLOUD_API
- WHATSAPP_PHONE_NUMBER_ID: 1236101482916191
- WHATSAPP_WABA_ID: 971659015904015
- META_ACCESS_TOKEN: SYSTEM_USER token, NEVER EXPIRES (expires_at=0), app "SWAD MANIA LLAC" (1565083148587185)
- META_APP_SECRET: d04f21b2f00b198c88bfb07eb95b3fe6 (32-hex, valid - signature checks verified)
- Verify token (either is accepted): brandsxai_wa_verify_7bK9mQ2xP4  OR  asdfghjkl1234567890
- WA_INGEST_TOKEN (X-Ingest-Token header): brandsxai_ingest_9fT3nQ8wZ1
- Webhook callback URL (ngrok -> this container, verified): https://shily-orthopneic-shawnna.ngrok-free.dev/api/whatsapp/webhook
- Test recipient: +1 201 268 8622 (E.164 12012688622) - real hello_world message delivered to it
- Diagnostics: GET /api/whatsapp/status (login testuser/test123) -> expect 9/9 checks PASS, ready_to_send=true
- Sync real templates: POST /api/whatsapp/templates/sync -> 14 approved (hello_world has 0 vars; others 1-4 vars, language en_US)
- Restart tunnel if container restarts:
  nohup ngrok http 8001 --url=https://shily-orthopneic-shawnna.ngrok-free.dev --log=stdout > /tmp/ngrok.log 2>&1 &
