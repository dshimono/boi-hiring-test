# FastAPI DataLLMReact

## Authentication

Passwordless authentication via magic links.

### Getting started

```bash
cp .env.example .env      # fill in SECRET_KEY (openssl rand -hex 32); RESEND_API_KEY is optional
make install
make migrate
make up                   # http://localhost:8000 (api), http://localhost:3000 (web)
```

Without a `RESEND_API_KEY`, magic links are logged instead of emailed — useful for local development.

### How it works

1. `POST /api/v1/auth/magic-link` — client submits an email. If no user exists for that email, one is created. A single-use token is generated, hashed, stored with a `MAGIC_LINK_EXPIRE_MINUTES`-minute expiry, and emailed as a sign-in link (or logged, if `RESEND_API_KEY` isn't set).
2. `POST /api/v1/auth/verify` — client submits the raw token from the link. If it's valid, unused, and unexpired, the user is marked verified and a JWT access token is returned.
3. `GET /api/v1/users/me` and the other data routes (`/api/v1/ads`, `/api/v1/metrics/*`, `/api/v1/stats/*`) are protected; they require `Authorization: Bearer <access_token>`.

### Security properties

- **Tokens are stored only as SHA-256 hashes** (`magic_links.token_hash`); the raw token never touches the database, so a database leak yields nothing usable.
- **Single-use.** Redeeming a token sets `used_at`; a second attempt with the same token is rejected.
- **Short-lived.** Magic links expire after `MAGIC_LINK_EXPIRE_MINUTES` (default 15).
- **Anti-enumeration.** `POST /api/v1/auth/magic-link` always returns the same generic message, whether or not an account exists for that email, so the endpoint can't be used to discover registered addresses.
- **JWT access tokens** carry `sub` (user id), `exp`, `iat`, and `type: "access"` claims, signed with `SECRET_KEY`/`ALGORITHM` and valid for `ACCESS_TOKEN_EXPIRE_MINUTES` (default 24h).

### Rollout kill switch

`AUTH_ENABLED=false` + `AUTH_BYPASS_USER_ID=<uuid>` makes every request behave as that user, regardless of any credentials supplied — the documented rollout path for pointing the existing frontend at this API before it speaks the magic-link flow. A migration seeds a `bypass@example.com` user for this purpose; set `AUTH_BYPASS_USER_ID` to its id. Setting `AUTH_ENABLED=false` without `AUTH_BYPASS_USER_ID` fails fast at startup.

### Environment variables

| Variable | Default | Notes |
|---|---|---|
| `SECRET_KEY` | *(required)* | JWT signing key; generate with `openssl rand -hex 32` (must be ≥ 32 bytes for HS256) |
| `ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | JWT access token lifetime |
| `MAGIC_LINK_EXPIRE_MINUTES` | `15` | Magic link token lifetime |
| `AUTH_ENABLED` | `true` | Kill switch; `false` requires `AUTH_BYPASS_USER_ID` |
| `AUTH_BYPASS_USER_ID` | *(unset)* | User id every request resolves to when `AUTH_ENABLED=false` |
| `RESEND_API_KEY` | *(empty)* | Empty means magic links are logged instead of emailed — useful for local development |
| `RESEND_TIMEOUT_SECONDS` | `5` | Resend HTTP client timeout |
| `EMAIL_FROM` | `noreply@example.com` | Sender address for magic-link emails |
| `FRONTEND_URL` | `http://localhost:3000` | Base URL the magic-link email points at (`{FRONTEND_URL}/auth/verify?token=...`) |

See `.env.example` for the full list of variables, including the pre-existing database/CORS/static ones.

### Known public asset path

`/static/ads` is mounted directly in `app/main.py` and bypasses the router (and therefore `get_current_user`) entirely — it remains publicly accessible regardless of `AUTH_ENABLED`. This matches pre-existing behavior and is not changed by this work.

### Testing

```bash
docker compose up -d db   # tests run against this database
make test
```

Each test runs inside a transaction (or an in-memory SQLite session for `tests/unit`) that's rolled back afterwards, so nothing persists between runs. No test sends real email; tests marked `@pytest.mark.real_email` are skipped unless `RESEND_API_KEY` is set.

## Chat with your data

Ask natural-language questions about ad performance; answers come from a typed tool call (`get_ad_performance`) into the same `services/metrics.rank_ads()` function the dashboard's own metrics use, never from the model's own knowledge. The tool-calling loop (`app/ai/chat_service.py`) sends the system prompt, conversation history, and the user's question to the LLM, executes any tool calls it requests, and feeds the JSON results back until it returns a final answer or a 5-iteration cap is hit. If a question needs data the tool can't provide (e.g. ad comments or creative copy), the model is instructed to say so rather than estimate.

**Demo question:** *"Which ad has the best engagement rate, and how many times higher is that than the ad with the worst engagement rate?"* — grounds an actual insight ("Dynamic Synthetic Personas" at ~3.2% is ~3.7x "From Chaos to Clarity" at ~0.85%) and shows the model reasoning over a full ranked tool result rather than a single lookup.

### Provider swap

`app/ai/llm/client.py` is the only file that imports the OpenAI SDK; everything else in `app/ai/` depends only on the neutral `Message`/`ToolCall`/`ToolDef`/`LLMResponse` types and the `LLMClient` protocol. Adding a second provider is one new class in `client.py` plus one `LLM_PROVIDER` env var value — no changes anywhere else.

### Environment variables

| Variable | Default | Notes |
|---|---|---|
| `LLM_PROVIDER` | `openai` | Selects the client in `get_llm_client()`; unknown values raise at startup |
| `LLM_MODEL` | `gpt-4o-mini` | Model name, passed straight through to the provider |
| `LLM_MAX_TOKENS` | `1000` | Response token cap |
| `LLM_TIMEOUT_S` | `30` | Provider request timeout, in seconds |
| `OPENAI_API_KEY` | *(empty)* | Required to actually call the API; the app still boots without it |

### Next features

- `search_comments` over `ad_comments`, via embeddings, once the dataset outgrows prompt-stuffing.
- A second provider `case` branch in `get_llm_client()` (e.g. Gemini) — no stub exists today by design.
