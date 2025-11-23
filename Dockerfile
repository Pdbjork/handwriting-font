FROM python:3.12-slim AS backend
WORKDIR /code
COPY backend/requirements.txt .
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    potrace \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*
RUN pip install -r requirements.txt
COPY backend ./backend

FROM node:20-alpine AS frontend
WORKDIR /app
COPY frontend ./
RUN npm install && npm run build

FROM backend
COPY --from=frontend /app/dist /static
CMD ["uvicorn","backend.app.main:app","--host","0.0.0.0","--port","8000"]
