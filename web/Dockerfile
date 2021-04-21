FROM python:3
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip3 --no-cache-dir -r requirements.txt
COPY . .
CMD ["python3", "app.py"]