#!/bin/bash

# Install MongoDB
curl -fsSL https://pgp.mongodb.com/server-8.0.asc | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/mongodb-server-8.0.gpg
echo "deb [ arch=amd64,arm64 signed-by=/etc/apt/trusted.gpg.d/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/debian bookworm/mongodb-org/8.0 main" | sudo tee /etc/apt/sources.list.d/mongodb-org-8.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org

# Create necessary directories and set permissions
sudo mkdir -p /data/db
sudo chown -R mongodb:mongodb /data/db
