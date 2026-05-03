# M0 — Authentication

**Goal**: Email + password auth with JWT. Workspace auto-created on register
to enable multi-tenant scaling later without schema rework.

**Sprint**: 1.

## Files

### Backend

| Path | Responsibility |
|------|----------------|
| `backend/app/models/user.py` | `User` model (email, password_hash, role) |
| `backend/app/models/workspace.py` | `Workspace` (FK owner_id → User) |
| `backend/app/schemas/auth.py` | `RegisterRequest`, `LoginRequest`, `TokenResponse`, `UserPublic` |
| `backend/app/core/security.py` | `hash_password`, `verify_password`, `create_access_token`, `decode_token` |
| `backend/app/api/deps.py` | `current_user_id` dep (already drafted) |
| `backend/app/api/v1/auth.py` | `POST /register`, `POST /login` |
| `backend/alembic/versions/0001_init.py` | Migration covering `users` + `workspaces` (and the rest of Sprint-1 tables) |
| `backend/tests/test_auth.py` (new) | Happy-path register/login + token validation |

### Frontend

| Path | Responsibility |
|------|----------------|
| `frontend/app/(auth)/login/page.tsx` | Login form (RHF + Zod mirroring `LoginRequest`) |
| `frontend/app/(auth)/register/page.tsx` (new) | Register form |
| `frontend/lib/stores/authStore.ts` | Persist token + email |
| `frontend/middleware.ts` (new) | Redirect unauthenticated requests off dashboard routes |
| `frontend/lib/api-client.ts` | Already injects `Authorization: Bearer …` |

## DB tables touched

`users`, `workspaces`. Both ship in migration `0001_init.py`.

## Endpoints

| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | `/api/v1/auth/register` | `RegisterRequest` | `TokenResponse` (also creates Workspace) |
| POST | `/api/v1/auth/login` | `LoginRequest` | `TokenResponse` |
| GET | `/api/v1/auth/me` (Sprint 1 stretch) | – | `UserPublic` |

## Extension points

- Adding OAuth providers later: implement an `AuthProvider` interface in
  `app/services/auth/providers/` (analogous to LLMProvider). Out of scope
  for Sprint 1.

## Tasks

- [ ] **M0-BE-01** User SQLAlchemy model
- [ ] **M0-BE-02** Workspace + auto-create on register
- [ ] **M0-BE-03** POST /auth/register
- [ ] **M0-BE-04** POST /auth/login
- [ ] **M0-BE-05** current_user_id dep wired across protected routes
- [ ] **M0-FE-01** Login form
- [ ] **M0-FE-02** Register form
- [ ] **M0-FE-03** authStore + redirect-on-success
- [ ] **M0-FE-04** Route guard (middleware)

## Acceptance criteria

- New user can register → receives token → uses it to call a protected
  endpoint → gets 200.
- Wrong password on login returns 401 with a stable error code.
- JWT `sub` claim equals `User.id` UUID; `decode_token` returns `None` on
  bad signature.
- Workspace count == User count after a fresh registration flow (one-to-one
  for now).

## Out of scope

- Password reset flow.
- OAuth / social login.
- 2FA.
- Multi-workspace UI (schema supports it, UI doesn't).
