FROM python:3.12-slim
WORKDIR /simulator
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "vehicle_simulator.py", "--vehicles", "1000", "--rate", "10"]
