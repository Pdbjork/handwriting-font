FROM python:3.12-slim AS backend
WORKDIR /code
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend ./backend

FROM node:20-alpine AS frontend
WORKDIR /app
COPY frontend ./
RUN npm ci && npm run build

FROM python:3.12-slim
COPY --from=backend /code /code
COPY --from=frontend /app/dist /static
CMD ["uvicorn","backend.app.main:app","--host","0.0.0.0","--port","8000"]
