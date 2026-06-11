# React SaaS UI

This is the production-oriented SaaS interface for the AI Governance & Compliance Intelligence Platform.

It runs beside the Streamlit demo UI and consumes the same FastAPI backend.

## Run

```bash
cd frontend/react_app
npm install
npm run dev
```

Environment variables:

- `VITE_API_BASE_URL`: backend URL, defaults to `http://127.0.0.1:8000`
- `VITE_PLATFORM_API_KEY`: optional when `AUTH_MODE=api_key`
- `VITE_PLATFORM_USER`: UI actor name
- `VITE_PLATFORM_USER_ROLE`: role header, usually `admin` or `compliance_reviewer`
- `VITE_PLATFORM_TENANT_ID`: workspace/tenant id
