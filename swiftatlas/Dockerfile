FROM python:3.12.3-slim

RUN apt update && apt install -y nano tcpdump && rm -rf /var/lib/apt /var/lib/cache/apt

COPY requirements.txt .
RUN pip install -r requirements.txt

WORKDIR /app

COPY . ./swiftatlas

CMD ["bash"]