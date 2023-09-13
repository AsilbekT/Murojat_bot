# Django App Deployment with Docker and Docker Compose

This guide will walk you through the process of deploying your Django application using Docker and Docker Compose. By containerizing your app, you can ensure consistent and reproducible deployments across different environments.

## Prerequisites

Before you begin, ensure you have the following installed:

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Step 1: Clone Your Repository

Clone your Django project repository to your deployment environment:

```bash
git clone https://github.com/AsilbekT/murojat_bot.git
cd murojat_bot


Step 2: Configure Environment Variables
Create a .env file in the project root to store your application's environment variables. Sample content:

# Database settings
DJANGO_DB_HOST=db
DJANGO_DB_PORT=5432
DJANGO_DB_NAME=mydatabase
DJANGO_DB_USER=myuser
DJANGO_DB_PASSWORD=mypassword


Step 3: Build and Start Containers:

Build and start your Docker containers using Docker Compose:

docker-compose up --build