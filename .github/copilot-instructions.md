# Copilot Instructions for ExpenseSplittingTracking

## Project Overview
- **Centsible** is a web app for group expense splitting, built with a Flask backend and a static HTML/JS/CSS frontend.
- Backend (`backend/`): Handles API, authentication, database, OCR, and file uploads.
- Frontend (`frontend/`): Pure HTML/CSS/JS, no framework; communicates with backend via REST API.

## Architecture & Data Flow
- **Backend**: Flask app (`app.py`) exposes REST endpoints defined in `routes.py` and uses models from `models.py`.
  - Database: SQLite (`test.db`), schema in `schema.sql`, initialized by `init_db.py`.
  - Expense logic in `splitting.py`, CRUD in `crud.py`.
  - OCR for receipts via EasyOCR, image handling with Pillow, PDF conversion with pdf2image.
  - Uploaded files stored in `backend/uploads/expenses/<expense_id>/`.
- **Frontend**: Static files served via Python's `http.server`.
  - JS files in `frontend/js/` handle API calls and UI logic.
  - Animations via GSAP, PDF export via jsPDF, 3D logo with Google Model Viewer.

## Developer Workflows
- **Backend setup**:
  - `cd backend && pip3 install -r requirements.txt`
  - `python3 init_db.py` (creates/updates `test.db`)
  - `python3 app.py` (starts server at `localhost:5000`)
- **Frontend setup**:
  - `cd frontend && python3 -m http.server 8000` (serves static files)
- **Database reset**: Delete `backend/test.db` and rerun `init_db.py`.
- **Testing**: Run backend tests with `python3 test_crud.py`, `python3 test_new_endpoints.py`, or `python3 test_receipt_ocr.py`.

## Conventions & Patterns
- **API**: All endpoints are defined in `routes.py`. Use JSON for requests/responses.
- **Auth**: JWT via PyJWT, password hashing with bcrypt.
- **Expense logic**: Centralized in `splitting.py`.
- **Uploads**: Store files under `backend/uploads/expenses/<expense_id>/`.
- **Frontend**: No build step; update HTML/JS/CSS directly.
- **Error handling**: Return JSON error messages from backend.

## Integration Points
- **OCR**: EasyOCR for receipts, triggered via backend endpoints.
- **PDF/Image**: pdf2image and Pillow for processing uploads.
- **Frontend-backend**: Communicate via fetch/XHR to Flask API.

## Key Files & Directories
- `backend/app.py`, `backend/routes.py`, `backend/models.py`, `backend/splitting.py`, `backend/crud.py`
- `backend/init_db.py`, `backend/schema.sql`, `backend/uploads/`
- `frontend/index.html`, `frontend/js/`, `frontend/styles.css`

## Example Workflow
1. Add a new expense: Frontend sends POST to backend API, backend updates DB and stores any uploads.
2. Run tests: `python3 test_crud.py` (unit tests for CRUD logic).
3. Reset DB: Delete `test.db`, rerun `init_db.py`.

---

If any conventions or workflows are unclear, please ask for clarification or provide feedback to improve these instructions.