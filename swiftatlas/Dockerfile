FROM python:3.12.3-slim

RUN apt update && apt install -y nano tcpdump && rm -rf /var/lib/apt /var/lib/cache/apt

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY setup.sh .
RUN ./setup.sh

RUN adduser --disabled-password --gecos "" lta
RUN mkdir /imports && chown lta /imports

WORKDIR /swiftatlas

COPY . .

CMD ["bash"]