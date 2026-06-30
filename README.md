# Clavis

**Clavis** is an intelligent personal knowledge and productivity management platform that combines secure cloud storage, note management, and AI-assisted organization into a single backend system.

Designed for individuals who manage ideas, documents, tasks, and events across multiple devices, Clavis acts as a private digital workspace where information can be captured, stored, retrieved, and transformed into actionable plans.

Unlike traditional note-taking applications, Clavis is being built as a foundation for AI-powered personal organization. Users can store notes and files securely in the cloud while leveraging intelligent features that help organize information, surface relevant content, and manage upcoming events, deadlines, and daily activities.

## Core Capabilities

* Secure user authentication and data isolation
* Personal cloud storage for notes and files
* Fast retrieval of documents and knowledge assets
* Amazon S3-backed file storage with presigned URLs
* Async architecture for scalable performance
* Bulk note management operations
* Dockerized deployment
* Automated testing and validation

## AI-Powered Productivity (In Development)

Clavis is evolving beyond note storage into an AI-assisted personal operating system capable of:

* Intelligent event and schedule management
* Deadline and reminder organization
* AI-generated task planning
* Context-aware note retrieval
* Knowledge extraction from stored content
* Semantic search across notes and documents
* Personalized daily planning assistance
* Natural language interaction with stored information

## Architecture

The platform follows a modern cloud-native architecture:

* **FastAPI** for high-performance API services
* **Async SQLAlchemy** for database operations
* **PostgreSQL** for persistent metadata storage
* **Amazon S3** for scalable object storage
* **Docker** for deployment and portability
* **Pydantic** for data validation
* **UV** for dependency and environment management

## Vision

Clavis aims to become a personal knowledge cloud where notes, files, schedules, and AI assistance converge into a single system. Rather than functioning as a simple note repository, it serves as an intelligent workspace that helps users capture information, organize their digital assets, and transform ideas into actions.

# Running the Project with Docker

## Prerequisites

Install Docker on your machine before continuing.

Verify that Docker is installed:

```bash
docker --version
```

## Clone the Repository

```bash
git clone <https://github.com/sayik/clavis>
cd <clavis>
```

## Build the Docker Image

From the project root directory, run:

```bash
docker build -t super_notes-api .
```

Docker will download the required dependencies and build an image named `super_notes-api`.

## Run the Application

Start the container:

```bash
docker run -p 8000:80 super_notes-api
```

The API will be available at:

```text
http://localhost:8000
```

Swagger documentation:

```text
http://localhost:8000/docs
```

ReDoc documentation:

```text
http://localhost:8000/redoc
```

## Stop the Application

Press `Ctrl+C` in the terminal where the container is running.

Alternatively:

```bash
docker ps
docker stop <container-id>
```

## Notes

This project currently uses SQLite as its database. The database file is packaged inside the container. Data persistence across container recreation is not currently configured.


## Status

Clavis is being developed at a rapid pace, with new features added regularly. A public online release is planned soon, bringing AI-assisted productivity tools, personal knowledge management, and secure cloud storage into a unified platform.
