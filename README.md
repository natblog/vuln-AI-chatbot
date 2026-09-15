# AI Vuln Chat Lab — Prompt Injection (Tool-Call Data Exfiltration)

Vulnerable CPU/GPU/RAM seller chatbot for learning prompt-injection /
excessive-agency exfiltration: prompt chains tools to send another user's
`secret_data` to `someone@evil.ai`, verified in MailHog.

> 🚩 CAPTURE FLAG!

## Architecture

**Stack:** FastAPI + SQLite.

**Tools:**

- `list_products`: Filter by category or product ID.
- `list_customers`: list all customers.
- `get_customer_purchases`: Looks up orders.
- `send_email`: send_email from `assistant@shop.local`.

**LLM:**

- **Engine:** Defaults to local Ollama running `qwen3.5:4b`. OpenAI is also
  supported through an API key and base URL.
- **Config:** Copy `.env.example` to `.env`, then update the settings as needed.

**Services:**

- `frontend/` — React lab page: instructions, challenge, samples, current-user header, tool-call toggle, reset, and MailHog link.
- `backend/` — FastAPI API with SQLite database and LLM tool-calling support.
- `mailhog` — SMTP `:1025` and UI/API `:8025`.
- `data/` — Host-mapped SQLite volume at `./data/shop.db`.

| Service  | URL                   | Notes                               |
|----------|-----------------------|-------------------------------------|
| frontend | http://localhost:3000 | Lab UI                              |
| backend  | http://localhost:8000 | `/api/health` `/api/docs` `/api/chat` |
| mailhog  | http://localhost:8025 | SMTP `:1025`                        |

## Prerequisites

- Docker + Docker Compose
- **Default:** Install Ollama and run `ollama pull qwen3.5:4b`.
- **Optional:** Use an OpenAI API key instead by setting `LLM_PROVIDER=openai`.

## Quickstart

```bash
cp .env.example .env   # optional; edit LLM_PROVIDER / keys / emails
docker compose up --build
```

Open http://localhost:3000. Current user is `alice@example.com` (no login).

If GNU Make is available, the same workflow can use these shortcuts:

```bash
make up-build  # build images and start the stack
make down      # stop and remove the stack
make logs      # follow service logs
make test      # run backend tests
make help      # show all available commands
```

## Project structure

```text
ai-vuln-chat/
├── .env.example          Environment template
├── docker-compose.yml    Service definitions
├── Makefile              Common commands
├── README.md             Project guide
├── backend/              FastAPI app and tests
│   ├── app/              API, database, LLM, and tools
│   └── tests/            Backend test suite
├── frontend/             React app
│   └── src/              UI and components
└── data/                 SQLite database
```

## Tests

```bash
cd backend
PYTHONPATH=. pytest tests/test_api.py -v        # unit + seam (no docker needed)
LIVE=1 PYTHONPATH=. pytest tests/ -v            # incl. live compose + MailHog check
```

Using Make:

```bash
make test       # run backend tests
make test-live  # run live tests with MailHog
```

## CI & supply chain

GitHub Actions runs the backend tests, frontend build, Docker build, and
dependency security checks before changes can merge into `main`.

Run the security checks locally:

```bash
pip-audit -r backend/requirements.txt
npm audit --audit-level=high --prefix frontend
```

Dependabot checks for quarterly Python and JavaScript dependency updates.
Use `LOG_LEVEL=DEBUG` to enable backend debug logging.

## License

This project is licensed under the [MIT License](LICENSE).
