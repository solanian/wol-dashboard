FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 10001
CMD ["streamlit", "run", "app.py", "--server.port=10001", "--server.address=0.0.0.0"]
