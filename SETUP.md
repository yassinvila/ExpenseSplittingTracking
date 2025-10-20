# Centsible Setup Guide

## Quick Start

### 1. Backend Setup

Navigate to the backend directory and set up the environment:

```bash
cd backend
pip install -r requirements.txt
```

Initialize the database:

```bash
python3 init_db.py
```

Start the Flask server:

```bash
python3 app.py
```

The backend will be running on `http://localhost:5000`

### 2. Frontend Setup

Navigate to the frontend directory and serve the files:

```bash
cd frontend
python3 -m http.server 8000
npx serve .
```

The frontend will be available at `http://localhost:8000`