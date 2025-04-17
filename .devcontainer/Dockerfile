FROM python:3.12.3-slim

# Set environment variables
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PATH=/root/.pyenv/shims:/root/.pyenv/bin:$PATH

# Install required packages and dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    wget \
    sudo \
    git \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libncurses5-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libffi-dev \
    liblzma-dev \
    python3-openssl \
    openssh-client \
    apt-transport-https \
    ca-certificates \
    libcurl4-openssl-dev \
    libgnutls30 \
    make \
    gcc \
    g++ \
    libxmlsec1-dev \
    pkg-config \
    gnupg2 \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Add the MongoDB GPG key (server 7.0) and jammy repo
RUN curl -fsSL https://pgp.mongodb.com/server-7.0.asc \
    | gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" \
    | tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Install MongoDB tools and mongosh
RUN apt-get update && \
    apt-get install -y --no-install-recommends mongodb-mongosh && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Verify mongosh installation
RUN mongosh --version

CMD ["/bin/bash"]