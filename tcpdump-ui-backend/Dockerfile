FROM python:3.11-slim
WORKDIR /app
COPY main.py .
RUN pip install fastapi uvicorn kubernetes 'uvicorn[standard]'
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
