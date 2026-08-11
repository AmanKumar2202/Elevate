# Elevate — Performance Feedback Tool

Multi-tenant monthly feedback app built with FastAPI, PostgreSQL, React, and TypeScript.

## Run

```bash
git clone https://github.com/AmanKumar2202/Elevate.git
cd performance-feedback
docker compose up --build
```

- App: `http://localhost:5173`
- API docs: `http://localhost:8000/api/docs`

Migrations and seed data run automatically.

## Demo login

All accounts use `password123`.

| User | Email | Use case |
| --- | --- | --- |
| Priya Sharma | `priya@ashoka.com` | Gives feedback to 6 reports and receives feedback from Rohan. |
| Kavita Iyer | `kavita@ashoka.com` | Ashoka HR pending dashboard. |
| Aditya Verma | `aditya@ashoka.com` | Feedback history and parameter trends. |
| Arjun Kapoor | `arjun@brightpath.com` | Founder with 8 direct reports. |
| Lakshmi Nair | `hr@brightpath.com` | Bright Path HR dashboard. |

## Key decisions

- One `User` table with self-referencing `manager_id` supports both deep and flat organisations.
- `role` is separate from hierarchy, so HR has company-wide visibility and a manager can also receive feedback.
- All company data is isolated using server-resolved `company_id` and database constraints.
- Reviews have five fixed parameters. A submitted review needs all five scores; comments are optional. Drafts can be saved with only the scores entered so far.
- Scores are stored as separate rows, making per-parameter history simple.
- HR pending status comes from manager/report relationships, so even a manager with zero submissions is shown.

## Local development

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

cd ../frontend
npm install
npm run dev
```

## Verify

```bash
cd backend && pytest tests -v
cd frontend && npm run build
```

## Out of scope

Reorganisation history, notifications, company administration, and custom company parameters.
