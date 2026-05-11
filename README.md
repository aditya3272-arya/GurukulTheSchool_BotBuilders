# 🧠 Cortexia — AI-Powered School Helpdesk

> Built for **TECHVAGANZA: CV'26** by Grade 11 students

Cortexia is a high-performance, AI-driven digital assistant for the modern school ecosystem. It uses a microservices-inspired architecture to streamline communication between students, staff, and visitors.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🔁 **Triple-AI Failover** | Groq (Primary) → Cerebras (Secondary) → Gemini (Fallback) |
| ⚡ **Async Engine** | FastAPI + asyncio for fast, non-blocking responses |
| 🔐 **Role-Based Access (RBAC)** | Visitor / Student / Staff permission tiers |
| 🖥️ **Desktop UI** | CustomTkinter interface with AI-generated follow-up suggestions |
| ☁️ **Real-time Database** | Supabase (PostgreSQL) for records, attendance & fees |

---

## 🛠️ Tech Stack

- **Language:** Python 3.10+
- **Backend:** FastAPI, Uvicorn, Pydantic
- **Database:** Supabase (PostgreSQL)
- **AI Models:** LLaMA 3 (via Groq & Cerebras), Gemini
- **Frontend:** CustomTkinter, Pillow

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/aditya3272-arya/GurukulTheSchool_BotBuilders.git
cd GurukulTheSchool_BotBuilders
```

### 2. Set Up the Environment

```bash
# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory (use `.env.example` as a template):

```env
# ── App ────────────────────────────────────────
APP_ENV=dev
APP_BASE_URL=http://127.0.0.1:8000
SESSION_SECRET=your_session_secret_here
SESSION_MAX_AGE_SECONDS=86400

# ── School ─────────────────────────────────────
SCHOOL_ID=your-supabase-school-id
SCHOOL_NAME=your_school_name

# ── Supabase ───────────────────────────────────
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# ── AI Models ──────────────────────────────────
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL_INTENT=gemini-2.5-flash
GEMINI_MODEL_ANSWER=gemini-2.5-flash

GROQ_API_KEY=your_groq_api_key
GROQ_MODEL_INTENT=llama-3.1-8b-instant
GROQ_MODEL_ANSWER=llama-3.1-8b-instant

CEREBRAS_API_KEY=your_cerebras_api_key
CEREBRAS_MODEL_INTENT=llama3.1-8b
CEREBRAS_MODEL_ANSWER=llama-3.3-70b

# ── Forms ──────────────────────────────────────
FORMSPREE_ENDPOINT=https://formspree.io/f/your_form_id
FORMSPREE_QUERY_ENDPOINT=https://formspree.io/f/your_query_form_id
```

> ⚠️ Never commit real API keys. This file contains placeholders only.

---

## ▶️ Running the Application

Cortexia has three components. Run each in a separate terminal:

**Terminal 1 — Backend API**
```bash
cd backend
uvicorn app.main:app --reload
```

**Terminal 2 — Client Interface**
```bash
python -m client.main
```

**Terminal 3 — Admin Panel**
```bash
python -m admin_panel.main
```

---

## 🔄 System Workflow

```
User Query
    ↓
Access Validation  (RBAC + Keyword Filtering)
    ↓
AI Processing      (Groq → Cerebras → Gemini failover)
    ↓
Database Fetch     (Supabase)
    ↓
Structured Response + AI-generated Follow-up Suggestions
```

---

## 🛡️ Security

- ✅ Pydantic-based input validation
- 🔍 Keyword filtering for safe query handling
- 🔐 Credential management via environment variables
- 🧱 Role-based access enforcement across all endpoints

---

## 👥 Credits

| Name | Role |
|---|---|
| **Aaniya Sharma** | UI/UX Design & Frontend Development |
| **Aditya Arya** | Backend, AI Architecture, API Integration, Failover System |

---
## Demo & Submission

- 📂 **Code:** https://github.com/aditya3272-arya/GurukulTheSchool_BotBuilders
- 🎥 **Video & PPT:** https://drive.google.com/drive/folders/1koqG8Zq42JheBKkl3A2Mowpio-Zi5_N9?usp=drive_link
---

> **Note:** Sensitive credentials are excluded for security. API keys can be provided upon request for evaluation purposes.

---

> *Cortexia is not just a chatbot — it's a scalable AI-powered helpdesk system demonstrating how intelligent automation can modernize school infrastructure.*
