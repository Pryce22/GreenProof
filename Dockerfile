FROM hyperledger/besu:24.12.2

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
