# Clavis

Clavis is a FastAPI-based note management API that allows authenticated users to create, update, retrieve, and delete notes. Notes can contain text content and optional file attachments. Files are stored in Amazon S3 using presigned URLs, while note metadata is stored in a relational database using SQLAlchemy.

## Features

* User registration
* Authentication-protected endpoints
* Create text notes
* Attach files to notes
* Retrieve all notes belonging to a user
* Retrieve a specific note
* Update note content and attached files
* Delete individual notes
* Bulk delete multiple notes
* User data isolation (users can only access their own notes)
* Amazon S3 integration using presigned URLs
* Async SQLAlchemy database access
* Dockerized deployment
* Automated test suite

## Technology Stack

* FastAPI
* SQLAlchemy (Async)
* Pydantic
* PostgreSQL / SQL Database
* Amazon S3
* Docker
* UV Package Manager
* Uvicorn

## API Endpoints

### Health Check

```http
GET /health
```

Returns server status.

### Authentication

```http
POST /signup
```

Creates a new user account.

### Notes

```http
GET /notes
```

Returns all notes belonging to the authenticated user.

```http
GET /notes/{note_id}
```

Returns a specific note.

```http
POST /notes
```

Creates a note with optional file attachment.

```http
PATCH /notes/{note_id}
```

Updates an existing note and optionally uploads a new file.

```http
DELETE /notes/{note_id}
```

Deletes a single note.

```http
DELETE /notes
```

Bulk delete multiple notes.

### File Downloads

```http
GET /notes/files/{file_name}
```

Generates a presigned S3 download URL.

## Project Structure

```text
.
├── auth/
├── db/
├── schemas/
├── utils/
├── tests/
├── main.py
├── pyproject.toml
├── uv.lock
└── Dockerfile
```

## Running Locally

### Requirements

* Python 3.13+
* UV
* PostgreSQL
* AWS S3 Bucket

Install dependencies:

```bash
uv sync
```

Start the application:

```bash
uv run uvicorn main:app --reload
```

Application will be available at:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

## Running with Docker

Build the image:

```bash
docker build -t clavis .
```

Run the container:

```bash
docker run -p 8000:80 clavis
```

The API will be available at:

```text
http://localhost:8000
```

## Environment Variables

The application requires configuration for:

```env
DATABASE_URL=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=
AWS_BUCKET_NAME=
SECRET_KEY=
```

## Security

* Passwords are stored as hashes.
* All note operations require authentication.
* Users can only access their own notes.
* File downloads are performed through time-limited presigned URLs.

## Future Improvements

* File size validation
* Frontend client
* Logging
* Pre-commit hooks
* CI/CD pipeline
* Additional authentication features
* Improved file upload workflow
* API rate limiting

## License

MIT License
