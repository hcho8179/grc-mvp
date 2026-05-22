# Greenlight — Security Implementation Status

Last updated: 2026-05-21

---

## ✅ Implemented

### Authentication
| Measure | Detail |
|---|---|
| Password hashing | Argon2id (OWASP recommended) — memory-hard, GPU-resistant |
| Legacy bcrypt migration | Existing bcrypt hashes transparently upgraded to Argon2 on next login |
| Session tokens | JWT HS256, 7-day expiry, signed with `jwt_secret_key` |
| HttpOnly cookies | Auth token stored in HttpOnly cookie — unreadable by JavaScript |
| SameSite=Lax | Prevents CSRF attacks from other domains |
| Password minimum length | 8 characters enforced on register and change-password |

### Password Reset
| Measure | Detail |
|---|---|
| Cryptographic token | `secrets.token_urlsafe(32)` — 256-bit entropy, brute-force proof |
| Token hashing | Only SHA-256 hash stored in DB — raw token never persisted |
| 15-minute expiry | Tokens expire automatically |
| Single-use | Token wiped immediately after use |
| Email enumeration protection | Forgot-password always returns 200 regardless of whether email exists |
| Delivery | Resend — TLS-enforced email delivery |

### Access Control
| Measure | Detail |
|---|---|
| Role-based access | owner / admin / member roles enforced on backend and frontend |
| Member restrictions | Members cannot delete questionnaires, documents, or templates |
| Admin restrictions | Admins cannot change owner role or transfer ownership |
| Owner-only actions | Role changes, ownership transfer restricted to owner only |
| Org scoping | Every DB query filtered by `org_id` — cross-tenant data leakage impossible |
| Protected routes | Frontend redirects to /login if session cookie is invalid |

### Rate Limiting
| Endpoint | Limit |
|---|---|
| POST /api/auth/login | 10 requests/minute per IP |
| POST /api/auth/register | 5 requests/minute per IP |
| POST /api/auth/forgot-password | 3/minute AND 5/hour per IP |
| POST /api/auth/reset-password | 5 requests/minute per IP |

### Database & Queries
| Measure | Detail |
|---|---|
| ORM queries | SQLAlchemy ORM used throughout — parameterised by default |
| Raw SQL (pgvector) | Uses `CAST(:vec AS vector)` bound parameter — injection proof on two layers: bound param + value is mathematically constrained to floats only |
| Credentials | Stored in `.env` — never hardcoded in source |

### Audit Trail
| Measure | Detail |
|---|---|
| Event logging | Every significant action logged to `audit_logs` table |
| Events covered | Login, register, approve, reject, generate, upload, delete, role change, password reset/change, question assignment |
| Org scoped | Audit log filtered by org — tenants cannot see each other's events |
| Visible to | Owner and admin only — members cannot access audit log |

### Comments & Assignment Access Control
| Measure | Detail |
|---|---|
| Assignment restricted | Only owner / admin can assign questions to team members |
| Comment deletion | Authors can delete their own comments; owner / admin can delete any |
| Cross-org isolation | Comments and assignments filtered by `org_id` — tenants cannot see each other's data |

### Security Headers
Added as FastAPI middleware in `app/main.py` — applied to every response automatically.

| Header | What it prevents |
|---|---|
| `Content-Security-Policy` | Scripts/styles loading from untrusted sources (XSS mitigation) |
| `X-Frame-Options: DENY` | Clickjacking — your site being embedded in an iframe on another domain |
| `X-Content-Type-Options: nosniff` | Browser executing a text file as JavaScript |
| `Referrer-Policy` | Your URLs (including tokens) leaking to third-party sites in the Referer header |
| `Permissions-Policy` | Malicious scripts accessing camera, microphone, or geolocation |
| `frame-ancestors 'none'` | Modern equivalent of X-Frame-Options for newer browsers |

> **Reminder:** `Strict-Transport-Security` (HSTS) is already written in `app/main.py` but commented out.
> Uncomment it the moment HTTPS is live — do not enable it while still on HTTP or it will permanently break your site.

### Outbound Connections
| Service | Encryption |
|---|---|
| Gemini / Groq / Cerebras / OpenRouter | HTTPS enforced by provider |
| Voyage AI embeddings | HTTPS enforced by provider |
| Resend email delivery | TLS enforced by provider |

---

## ❌ Not Yet Implemented — Requires Deployment

### HTTPS / TLS
| Item | What's needed | Why it matters |
|---|---|---|
| TLS certificate | Domain + Caddy/Nginx + Let's Encrypt | Encrypts all browser ↔ server traffic |
| Cookie `secure=True` | Enable after HTTPS is live (`app/routes/auth.py`) | Forces browser to only send cookie over HTTPS |
| HSTS header | Add via Caddy config | Prevents HTTP downgrade attacks |
| Production APP_URL | Change `APP_URL` in `.env` to `https://yourdomain.com` | Fixes reset link in emails |
| Production FROM email | Change `RESEND_FROM_EMAIL` to `noreply@yourdomain.com` | Professional sender address |

### To-do when deploying
```
[ ] Buy domain name
[ ] Provision server (DigitalOcean / Hetzner / AWS)
[ ] Point DNS to server IP
[ ] Install Caddy — handles TLS certificate automatically
[ ] Set APP_URL=https://yourdomain.com in .env
[ ] Set RESEND_FROM_EMAIL=noreply@yourdomain.com in .env
[ ] Set secure=True on cookie in app/routes/auth.py
[ ] Rotate all API keys (never reuse dev keys in production)
[ ] Set a strong JWT_SECRET_KEY (random 64-char string)
```

---

## ⚠️ Known Gaps (Future Work)

| Gap | Risk | Recommended Fix |
|---|---|---|
| No refresh token | Stolen cookie valid for 7 days with no revocation | Implement token revocation table |
| No account lockout | 10 attempts/min still allows ~14k guesses/day | Add progressive lockout after N failures |
| localStorage user object | Non-sensitive but still stored in localStorage | Move to sessionStorage or server-side session |
| No 2FA / MFA | Single factor authentication only | Add TOTP (Google Authenticator) support |
| Passwords accept weak values | "password1" passes length check | Add strength scoring (zxcvbn library) |

---

## Architecture Notes

- All secrets in `.env` — never committed to git (ensure `.env` is in `.gitignore`)
- Argon2id defaults: memory=64MB, iterations=3, parallelism=4 (OWASP recommended)
- Reset tokens: 256-bit entropy, SHA-256 hashed at rest, 15-min TTL, single-use
- Every API endpoint verifies JWT/cookie before processing — no unauthenticated endpoints except login/register/forgot-password/reset-password
