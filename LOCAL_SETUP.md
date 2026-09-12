# BrandsXAI — Local Server Setup (WhatsApp AI / Meta Cloud API)

Verified against the running cloud instance on 2026-09-12.

---

## 0. Prerequisites

| Tool | Version used | Check |
|---|---|---|
| Python | **3.11** | `python3 --version` |
| Node.js | **20.x** | `node -v` |
| Yarn | **1.22** (classic) | `yarn -v` |
| MongoDB | 6/7 local | `mongod --version` |
| ngrok | v3.39+ | `ngrok version` |

> Use **yarn**, never npm — npm resolves different versions and breaks the build.

Install Yarn if missing: `npm install -g yarn@1.22.22`

---

## 1. Get the code + install dependencies

```bash
git clone <your-repo> brandsxai && cd brandsxai

# ---------- Backend ----------
cd backend
python3.11 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

# ---------- Frontend ----------
cd ../frontend
yarn install
```

---

## 2. Start MongoDB

```bash
# macOS (Homebrew)
brew services start mongodb-community

# Ubuntu/Debian
sudo systemctl start mongod && sudo systemctl enable mongod

# Docker (easiest, any OS)
docker run -d --name brandsxai-mongo -p 27017:27017 -v brandsxai_mongo:/data/db mongo:7
```

Verify: `mongosh --eval "db.runCommand({ping:1})"`

The app **auto-seeds** users, features and templates on first boot — no migration step.

---

## 3. Credentials — exactly where each value goes

### 3a. `backend/.env`  ← create this file

```ini
# ---------- Database ----------
MONGO_URL="mongodb://localhost:27017"
DB_NAME="brandsxai_db"
CORS_ORIGINS="*"
JWT_SECRET="change-me-to-a-long-random-string"

# ---------- MySQL (optional; app falls back to MongoDB automatically) ----------
MYSQL_HOST=""
MYSQL_PORT="3306"
MYSQL_USER=""
MYSQL_PASSWORD=""
MYSQL_DATABASE=""

# ---------- WhatsApp Business Cloud API (Meta) ----------
META_GRAPH_VERSION="v22.0"
WHATSAPP_PHONE_NUMBER_ID="1236101482916191"
WHATSAPP_WABA_ID="971659015904015"
META_ACCESS_TOKEN="<your System User token, starts with EAA...>"
META_APP_SECRET="<32-char hex from App Dashboard > Settings > Basic > App Secret>"
WEBHOOK_VERIFY_TOKEN="brandsxai_wa_verify_7bK9mQ2xP4"
WHATSAPP_VERIFY_TOKEN="asdfghjkl1234567890"   # optional 2nd accepted verify token

# Strict webhook signature checking. Keep "true" in production.
# Only set "false" if you must debug with a mismatched app secret.
WA_REQUIRE_SIGNATURE="true"

# Token for pushing messages in from another system (X-Ingest-Token header)
WA_INGEST_TOKEN="brandsxai_ingest_9fT3nQ8wZ1"

# Public HTTPS base used to build absolute media links -> your ngrok domain
PUBLIC_BASE_URL="https://shily-orthopneic-shawnna.ngrok-free.dev"

# ---------- AI (WhatsApp suggested replies + AI summary) ----------
# REQUIRED or the sparkle/Generate buttons return 500 "AI service not configured"
ANTHROPIC_API_KEY=""
CLAUDE_MODEL="claude-sonnet-4-6"

# ---------- AI (Claim Processing / ICD-10) ----------
EMERGENT_LLM_KEY=""
GOOGLE_API_KEY=""
```

**Where each Meta value comes from**

| Variable | Where in the Meta dashboard |
|---|---|
| `WHATSAPP_PHONE_NUMBER_ID` | WhatsApp → **API Setup** → "Phone number ID" |
| `WHATSAPP_WABA_ID` | WhatsApp → **API Setup** → "WhatsApp Business Account ID" |
| `META_ACCESS_TOKEN` | Business Settings → **System Users** → Generate token → scopes `whatsapp_business_messaging` + `whatsapp_business_management` (never expires) |
| `META_APP_SECRET` | App Dashboard → **Settings → Basic → App Secret → Show** (32 hex chars) |
| `WEBHOOK_VERIFY_TOKEN` | You invent it. Must match what you type in the webhook screen. |

> ⚠️ `.env` gotcha: never leave a value containing `$` unquoted — the shell/dotenv expands it. Always wrap values in double quotes as above.

### 3b. `frontend/.env`  ← create this file

```ini
# Point the UI at your LOCAL backend
REACT_APP_BACKEND_URL=http://localhost:8001
WDS_SOCKET_PORT=3000
```

> Every backend route is under **`/api`**. The frontend builds URLs as
> `${REACT_APP_BACKEND_URL}/api/...` — never hardcode the host.

---

## 4. Run the servers

**Terminal 1 — backend (port 8001):**
```bash
cd backend && source .venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

**Terminal 2 — frontend (port 3000):**
```bash
cd frontend && yarn start
```

**Terminal 3 — ngrok (public HTTPS for Meta webhooks):**
```bash
ngrok config add-authtoken <YOUR_NGROK_AUTHTOKEN>
ngrok http 8001 --url=https://shily-orthopneic-shawnna.ngrok-free.dev
```

Open the app at **http://localhost:3000/login**

> 🚨 The ngrok domain tunnels **port 8001 = backend API only**. Opening it in a
> browser shows JSON, not the app. That is expected — it exists purely for Meta.

### Restart commands

| What changed | Action |
|---|---|
| Backend `.py` code | nothing — `--reload` picks it up |
| **`backend/.env`** | **must restart uvicorn** (Ctrl+C, re-run) — env is read at boot |
| Frontend `.jsx` / `.css` | nothing — hot reload |
| **`frontend/.env`** | **must restart `yarn start`** |
| ngrok died / laptop slept | re-run the `ngrok http` command |
| Everything | Ctrl+C all three terminals, start again |

If you use supervisor instead of raw terminals:
```bash
sudo supervisorctl restart backend
sudo supervisorctl restart frontend
sudo supervisorctl restart all
sudo supervisorctl status
tail -n 100 /var/log/supervisor/backend.err.log    # backend errors
```

---

## 5. Register the webhook in Meta

Meta App Dashboard → **WhatsApp → Configuration → Webhook → Edit**

| Field | Value |
|---|---|
| Callback URL | `https://shily-orthopneic-shawnna.ngrok-free.dev/api/whatsapp/webhook` |
| Verify token | `brandsxai_wa_verify_7bK9mQ2xP4` |

Click **Verify and save**, then **Manage** → subscribe to the **`messages`** field
(that one field carries inbound messages *and* sent/delivered/read receipts).

Watch every raw webhook live at **http://localhost:4040** (ngrok inspector) — it shows
headers, body and lets you **replay** requests.

---

## 6. Login credentials

| Where | Username | Password |
|---|---|---|
| `/login` | `testuser` | `test123` |
| `/login` | `mukesh` | `mukesh123` |
| `/admin/login` | `madoveradmin` | `admin@123` |

---

## 7. Final test cases

### TC1 — Health & connection (do this first)
```bash
curl -s http://localhost:8001/api/ | jq
# -> {"message":"BrandsXAI API","version":"2.0.0"}

TOKEN=$(curl -s -X POST http://localhost:8001/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"testuser","password":"test123"}' | jq -r .access_token)

curl -s http://localhost:8001/api/whatsapp/status -H "Authorization: Bearer $TOKEN" | jq
```
**PASS when:** `token_valid: true`, `ready_to_send: true`, `live_mode: true`,
`phone_number.verified_name: "Swad Mania"`, `token_info.never_expires: true`,
and **every entry in `checks[]` has `ok: true`**.

Any `ok: false` tells you exactly what is wrong — especially:
- `app_secret_format` → your `META_APP_SECRET` isn't 32 hex chars
- `webhook_signature` → app secret doesn't belong to the app that owns the WABA
- `meta_reachable` → access token invalid/revoked

### TC2 — Template sync (must run once per environment)
```bash
curl -s -X POST http://localhost:8001/api/whatsapp/templates/sync \
  -H "Authorization: Bearer $TOKEN" | jq '.synced_count, .templates[].name'
```
**PASS when:** `synced_count: 14`. Then `GET /api/whatsapp/templates` returns
`source: "meta"` and every template has `language: "en_US"`.
**Why it matters:** Meta rejects any template name/language not approved on your WABA
(error **132001**). Re-run this whenever you add or edit a template in WhatsApp Manager.

### TC3 — Webhook verification
```bash
curl -si "http://localhost:8001/api/whatsapp/webhook?hub.mode=subscribe&hub.challenge=ABC123&hub.verify_token=brandsxai_wa_verify_7bK9mQ2xP4" | head -1
# -> HTTP/1.1 200 OK   and body exactly: ABC123

curl -s -o /dev/null -w '%{http_code}\n' \
  "http://localhost:8001/api/whatsapp/webhook?hub.mode=subscribe&hub.challenge=X&hub.verify_token=nope"
# -> 403
```

### TC4 — Outbound live send + delivery ticks
In the UI: **WhatsApp AI → green "+" → pick `hello_world` → enter a test number → Send.**
The number must be listed under *WhatsApp → API Setup* recipients until your app is
Live-verified.

**PASS when:**
1. The message arrives on the handset.
2. The bubble tick goes **single grey → double grey → double blue** within seconds.
3. Hovering the tick shows real times, e.g. `Sent 20:26 · Delivered 20:26 · Read 20:48`.

If the tick sticks on a single grey check, your webhook is not reaching the backend —
check the ngrok inspector at :4040 and the backend log.

### TC5 — Inbound reply
Reply from the handset.

**PASS when:** within ~4s the thread jumps to the top of the list, shows a **green unread
badge**, the preview text updates, and opening it shows a **white left-aligned bubble**
with your text (inbound bubbles carry **no** ticks). The 24-hour reply window
(`window_expires_at`) is set to now + 24h.

### TC6 — One thread per number (no duplicates)
Send to the same number twice. **PASS when:** the second call returns `"reused": true`
and the chat list still shows **one** thread for that number.

### TC7 — Signature enforcement (security)
With `WA_REQUIRE_SIGNATURE="true"`, post an unsigned body:
```bash
curl -s -o /dev/null -w '%{http_code}\n' -X POST http://localhost:8001/api/whatsapp/webhook \
  -H 'Content-Type: application/json' -d '{"object":"whatsapp_business_account","entry":[]}'
# -> 403
```
**PASS when:** 403. If you get 200, `WA_REQUIRE_SIGNATURE` is still `false`.

### TC8 — Free-form text only inside the 24h window
After the customer replies, type a normal message in the composer and send.
**PASS when:** it delivers. Outside the 24h window Meta rejects free-form text and you
must open with an approved template instead.

---

## 8. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `190 "access token could not be decrypted"` | Token malformed/revoked → regenerate a System User token |
| `190 "Session has expired"` | 24h temporary token expired → use a System User token |
| `132001 template does not exist` | Wrong template name **or** language (`en` vs `en_US`) → re-run TC2 |
| Webhook POSTs return **403** | `META_APP_SECRET` wrong → fix it; check `webhook_signature` in TC1 |
| Meta says "Callback URL could not be validated" | ngrok not running, or verify token mismatch, or you forgot `/api` in the path |
| Ticks never leave single grey | webhook not subscribed to `messages`, or ngrok down |
| Sparkle / AI Summary → `500 AI service not configured` | `ANTHROPIC_API_KEY` empty in `backend/.env` |
| `ERR_NGROK_108` | Free plan allows 3 agent sessions → stop one at dashboard.ngrok.com/agents |
| Login page loads but login fails | You're on the ngrok URL (backend only). Use `http://localhost:3000/login` |
| Backend won't boot | `tail -n 100 /var/log/supervisor/backend.err.log` or read the uvicorn output |
