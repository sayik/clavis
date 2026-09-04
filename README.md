# Clavis

**Clavis** is a structured medical documentation platform that captures medical notes and supporting documents, with AI-assisted summarization and treatment-plan drafting.

The platform is designed to help organize clinical information into a secure, reviewable workflow. Medical notes and related documents can be stored together, processed asynchronously, and transformed into AI-generated outputs that remain available for human review rather than being treated as final clinical decisions.

## Core Capabilities

* Secure user authentication and data isolation
* Structured medical note management
* Supporting document and file storage
* Amazon S3-backed secure document storage using presigned URLs
* Asynchronous document processing
* AI-assisted medical note summarization
* AI-assisted treatment-plan drafting
* Reviewable AI-generated outputs
* Bulk document and note management operations
* Dockerized deployment
* Automated testing and validation

## AI-Assisted Clinical Documentation

Clavis is being developed around a workflow where AI assists with documentation rather than replacing clinical judgment.

Planned and in-development capabilities include:

* Summarizing medical notes and supporting documents
* Extracting relevant information from uploaded medical documents
* Generating structured summaries from unstructured clinical notes
* Drafting treatment plans based on documented information
* Connecting information across related medical records
* Providing reviewable AI-generated outputs
* Supporting clinicians in turning documented information into structured actions

AI-generated content is intended to remain **reviewable and editable by the responsible user** before being used in a clinical workflow.

## Architecture

The platform follows a modern cloud-native backend architecture:

* **FastAPI** for high-performance API services
* **Async SQLAlchemy** for asynchronous database operations
* **PostgreSQL** for persistent structured medical metadata
* **Amazon S3** for secure and scalable document storage
* **Docker** for deployment and portability
* **Pydantic** for data validation and schema management
* **UV** for dependency and environment management

The architecture separates structured medical metadata from supporting documents. Metadata is stored in PostgreSQL, while larger documents and files are stored in Amazon S3. Presigned URLs allow clients to interact with stored files without exposing long-lived storage credentials.

Asynchronous processing provides a foundation for handling operations such as document ingestion, extraction, summarization, and other AI-assisted workflows without blocking API requests.

## Documentation Workflow

A typical Clavis workflow looks like:

```text
Medical Note / Document
        │
        ▼
   Secure Upload
        │
        ├──────────────► PostgreSQL
        │                 Structured metadata
        │
        └──────────────► Amazon S3
                          Supporting documents
                                │
                                ▼
                     Asynchronous Processing
                                │
                                ▼
                         AI-assisted Analysis
                                │
                  ┌─────────────┴─────────────┐
                  ▼                               ▼
             Summarization              Treatment Plan
                  │                                │
                  └─────────────┬─────────────┘
                                ▼
                         Human Review


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
