# Automated Answer Sheet Evaluation System

An end-to-end system for automated evaluation of answer sheets using OCR and NLP.

## Features

- 📄 Multi-format input (PDF, Images, Text)
- 🔍 OCR-based text extraction (Tesseract)
- ✅ Automatic evaluation for objective & short answers
- 👨‍🏫 Teacher review interface for subjective answers
- 📊 Report generation and analytics
- 🔐 Role-based access (Student, Teacher, Admin)

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: React + Vite
- **Database**: PostgreSQL
- **OCR**: Tesseract
- **NLP**: spaCy, NLTK

## Project Structure

```
automated/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models/
│   │   ├── routers/
│   │   ├── services/
│   │   ├── schemas/
│   │   └── utils/
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   └── (React app)
└── docker-compose.yml
```

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## API Documentation

After starting the backend, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT License - Free for academic use
