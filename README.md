# 📄 LawLens

> A full-stack application for analyzing legal documents using AI-powered tools. LawLens provides risk assessment, regulatory simulation, reputation analysis, and impact comparison workflows with JWT-based authentication.

---

## 🚀 Overview

| Layer          | Technology                         |
|----------------|------------------------------------|
| Frontend       | React + Vite + TypeScript          |
| Backend        | FastAPI                            |
| Authentication | JWT (stored in `localStorage`)     |
| API Structure  | All endpoints prefixed with `/api` |

**Standard API Response Format:**

```json
{
  "success": true,
  "data": {},
  "error": null,
  "timestamp": "2026-02-28T10:00:00Z"
}
```

LawLens allows users to register and log in, upload legal documents, view uploaded documents, and run AI-driven analysis across four analysis workflows.

---

## 🛠 Tech Stack

**Frontend**
- React, Vite, TypeScript
- Axios
- React Router DOM

**Backend**
- FastAPI
- Uvicorn
- JWT Authentication

---

## ✨ Features

### 🔐 Authentication
- User registration and login
- Token validation on app load
- Automatic logout and redirect on `401` responses
- Protected routes via `AuthContext`

### 📄 Document Management
- Upload documents via `multipart/form-data`
- Fetch and display document list
- Display upload timestamp per document

### 🧠 AI Analysis Tools

| Tool                  | Endpoint                                      |
|-----------------------|-----------------------------------------------|
| Risk Assessment       | `POST /api/risk/assess/{document_id}`         |
| Regulatory Simulation | `POST /api/regulatory/simulate/{document_id}` |
| Reputation Analysis   | `POST /api/reputation/analyze/{document_id}`  |
| Impact Analysis       | `POST /api/impact/analyze/{document_id}`      |

---

## 📂 Project Structure (Frontend)

```
src/
├── api/
│   └── api.ts                 # Axios instance, interceptors, all API calls
│
├── context/
│   └── AuthContext.tsx        # Auth state, token hydration, login/logout
│
├── pages/
│   ├── Login.tsx
│   ├── Register.tsx
│   └── Dashboard.tsx
│
├── components/
│   ├── DocumentCard.tsx
│   ├── AnalysisResult.tsx
│   └── UploadForm.tsx
│
├── types/                     # Shared TypeScript interfaces
├── App.tsx
└── main.tsx
```

---

## 🔧 Environment Variables

Create a `.env` file in the frontend root directory:

```env
VITE_API_BASE_URL=http://localhost:8000
```

> All `VITE_` prefixed variables are bundled into the client at build time. Do not store secrets here.

The backend must be running at `http://localhost:8000`.

---

## 🖥 Installation & Setup

### 1️⃣ Frontend Setup

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install axios react-router-dom
```

Start the development server:

```bash
npm run dev
```

Frontend runs on: `http://localhost:5173`

---

### 2️⃣ Backend Setup (FastAPI)

From the `backend/` directory:

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload --port 8000
```

Swagger docs available at: `http://localhost:8000/docs`

---

## 🔐 Authentication Flow

1. User submits credentials — `POST /api/auth/login`
2. Backend returns JWT token in the `data` field
3. Token is stored in `localStorage`
4. Axios request interceptor attaches the token to all subsequent requests:
   ```
   Authorization: Bearer <token>
   ```
5. On a `401` response, the interceptor clears the token from `localStorage` and redirects to `/login`
6. On page refresh, `AuthContext` reads the token from `localStorage` and restores authentication state

> **Security note:** `localStorage` is accessible to JavaScript and susceptible to XSS. Sanitize all user input and evaluate this tradeoff against your threat model before production deployment.

---

## 📡 API Integration Notes

- All API calls are centralized in `api.ts` through a configured Axios instance
- A `skipAuth` flag prevents the token from being attached to public endpoints:
  - `POST /api/auth/login`
  - `POST /api/auth/register`
- File uploads use the `FormData` API — do **not** manually set `Content-Type: multipart/form-data`. The browser must set it automatically to include the correct `boundary` string
- All responses follow the standard envelope — always check `success` before consuming `data`

---

## ⚠️ Common Issues & Troubleshooting

**❌ `ERR_CONNECTION_REFUSED`**
The backend is not running. Start uvicorn on port `8000` before using the frontend.

**❌ Infinite loading on Dashboard**
Ensure `isLoading` is set to `false` after `AuthContext` finishes hydrating from `localStorage`. The dashboard must not render protected content until auth state is fully resolved.

**❌ `422 Unprocessable Entity`**
The request body does not match the backend schema. Check `/docs` for the exact expected shape, verify enum values, and remove any extra fields not declared in the model.

**❌ CORS Error**
FastAPI must have CORS middleware configured to allow `http://localhost:5173`. Verify the `allow_origins` list in your FastAPI middleware setup.

**❌ Upload fails silently**
Do not manually set `Content-Type` on `FormData` requests. Remove any explicit `Content-Type: multipart/form-data` header and allow the browser to handle the boundary automatically.

**❌ `VITE_API_BASE_URL` is `undefined` at runtime**
Confirm the variable exists in `.env` and restart the Vite dev server — changes to `.env` are not hot-reloaded.

---

## 🔮 Future Improvements

- Token refresh mechanism to extend sessions without re-login
- Role-based access control (admin vs. standard user)
- Document version comparison
- Advanced dashboard analytics
- File size and type validation with user-facing feedback
- Improved error reporting and notification system
- Deployment configuration documentation

---

## 📜 License

LawLens is a prototype built for educational and development purposes. Add a proper license (e.g., [MIT](https://opensource.org/licenses/MIT)) before any public distribution.
