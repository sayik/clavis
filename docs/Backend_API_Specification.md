# Clavis Frontend — Backend API Specification

**API Version:** `v1`  
**Base URL:**

```text
https://api.clavis.com/api/v1
```

This document defines the backend API required to support the current Clavis frontend.

The API follows conventional REST principles:

- Resources are represented as nouns.
- HTTP methods express the operation.
- Collection endpoints use plural nouns.
- Resource IDs identify individual resources.
- API versioning is handled through `/api/v1`.
- Search and filtering use query parameters rather than separate `/search` endpoints where practical.
- Long-running operations such as transcription and AI generation are asynchronous.
- Authentication is handled using access and refresh tokens.
- AI model selection/configuration is intentionally excluded from this specification.

---

# 1. API Design Principles

## 1.1 Base URL

All application endpoints should be under:

```text
/api/v1
```

For example:

```http
GET /api/v1/patients
```

rather than:

```http
GET /patients
```

---

## 1.2 HTTP Methods

| Method | Purpose |
|---|---|
| `GET` | Retrieve resources |
| `POST` | Create a resource or initiate an operation |
| `PATCH` | Partially update a resource |
| `PUT` | Replace a resource when full replacement is appropriate |
| `DELETE` | Delete a resource |

For most Clavis resources, `PATCH` should be preferred for updates because the frontend will generally modify only part of an object.

---

## 1.3 Resource Naming

Use plural resource names:

```text
/patients
/encounters
/notes
/documents
/notifications
/diagnoses
/medicines
```

Avoid action-oriented URLs such as:

```text
/getPatients
/createPatient
/searchPatients
/deletePatient
```

Instead:

```http
GET    /patients
POST   /patients
DELETE /patients/{patient_id}
```

---

# 2. Authentication

The existing Clavis backend already contains authentication functionality including signup, login, email verification, access tokens, and refresh tokens.

The existing authentication endpoints should be standardized under `/api/v1/auth`.

## Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/auth/register` | Create a doctor account |
| `POST` | `/auth/login` | Authenticate a doctor |
| `POST` | `/auth/refresh` | Obtain a new access token |
| `POST` | `/auth/logout` | Revoke the current session |
| `GET` | `/auth/me` | Return the authenticated user |
| `POST` | `/auth/verify-email` | Verify an email address |
| `POST` | `/auth/resend-verification` | Send another verification email |
| `POST` | `/auth/forgot-password` | Request a password reset |
| `POST` | `/auth/reset-password` | Reset a password |
| `POST` | `/auth/change-password` | Change the authenticated user's password |

### Example

```http
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

Response:

```json
{
  "id": "usr_01J...",
  "email": "doctor@example.com",
  "name": "Dr. Arjun Nair",
  "email_verified": true
}
```

---

# 3. Doctor Profile

The dashboard needs information about the currently authenticated doctor.

## Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/profile` | Retrieve current doctor's profile |
| `PATCH` | `/profile` | Update current doctor's profile |

### Example response

```json
{
  "id": "usr_01J...",
  "first_name": "Arjun",
  "last_name": "Nair",
  "email": "doctor@example.com",
  "specialty": "General Medicine",
  "avatar_url": "https://...",
  "clinic": {
    "id": "cln_01J...",
    "name": "Nair Family Clinic"
  }
}
```

---

# 4. Patients

Patients are a core resource in Clavis.

The frontend requires:

- Patient creation
- Patient listing
- Patient search
- Patient details
- Patient editing
- Patient history

## Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/patients` | List/search patients |
| `POST` | `/patients` | Create a patient |
| `GET` | `/patients/{patient_id}` | Retrieve patient |
| `PATCH` | `/patients/{patient_id}` | Update patient |
| `DELETE` | `/patients/{patient_id}` | Delete patient |
| `GET` | `/patients/{patient_id}/encounters` | Retrieve patient's encounters |
| `GET` | `/patients/{patient_id}/documents` | Retrieve patient's documents |
| `GET` | `/patients/{patient_id}/medications` | Retrieve patient's medications |
| `GET` | `/patients/{patient_id}/diagnoses` | Retrieve patient's diagnoses |
| `GET` | `/patients/{patient_id}/test-results` | Retrieve patient's test results |

## Searching patients

Do not create:

```http
GET /patients/search?q=Rahul
```

Prefer:

```http
GET /api/v1/patients?q=Rahul
```

Additional filters can be supported:

```http
GET /api/v1/patients?phone=9876543210
```

```http
GET /api/v1/patients?email=doctor@example.com
```

```http
GET /api/v1/patients?name=Rahul
```

Pagination should eventually be supported:

```http
GET /api/v1/patients?page=1&page_size=25
```

---

# 5. Encounters

An encounter represents a patient's consultation/visit.

This should become one of the central resources in the Clavis data model.

Conceptually:

```text
Patient
   │
   └── Encounter
          │
          ├── Conversation
          ├── Transcription
          ├── Clinical Note
          ├── Documents
          ├── Diagnoses
          └── Treatment Plan
```

## Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/encounters` | Create an encounter |
| `GET` | `/encounters/{encounter_id}` | Retrieve an encounter |
| `PATCH` | `/encounters/{encounter_id}` | Update an encounter |
| `DELETE` | `/encounters/{encounter_id}` | Delete an encounter |

Patient-specific listing:

```http
GET /api/v1/patients/{patient_id}/encounters
```

### Create encounter

```http
POST /api/v1/encounters
```

```json
{
  "patient_id": "pat_01J...",
  "type": "consultation",
  "started_at": "2026-10-01T10:30:00Z"
}
```

---

# 6. Clinical Notes

Clinical notes should be treated as first-class resources rather than generic user notes.

## Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/notes/{note_id}` | Retrieve a note |
| `PATCH` | `/notes/{note_id}` | Update a note |
| `DELETE` | `/notes/{note_id}` | Delete a note |
| `GET` | `/encounters/{encounter_id}/notes` | List encounter notes |
| `POST` | `/encounters/{encounter_id}/notes` | Create encounter note |

### Create note

```http
POST /api/v1/encounters/enc_01J.../notes
```

```json
{
  "title": "Consultation Note",
  "content": "...",
  "status": "draft"
}
```

Possible note statuses:

```text
draft
review
approved
signed
archived
```

---

# 7. Transcriptions

Clavis supports voice-based medical scribing.

Transcription should be asynchronous because audio processing can take time.

## Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/transcriptions` | Start transcription |
| `GET` | `/transcriptions/{transcription_id}` | Retrieve transcription status/result |

### Start transcription

```http
POST /api/v1/transcriptions
```

```json
{
  "encounter_id": "enc_01J...",
  "document_id": "doc_01J..."
}
```

Response:

```json
{
  "id": "trn_01J...",
  "status": "processing"
}
```

The frontend can poll:

```http
GET /api/v1/transcriptions/trn_01J...
```

Possible statuses:

```text
queued
processing
completed
failed
```

---

# 8. AI Clinical Assistance

AI model selection is intentionally excluded.

The API should expose the **clinical assistance capability**, not the underlying AI provider/model.

## Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/ai/assistance` | Generate clinical assistance |
| `GET` | `/ai/assistance/{assistance_id}` | Retrieve result/status |

### Request

```http
POST /api/v1/ai/assistance
```

```json
{
  "encounter_id": "enc_01J...",
  "input": "Patient has cough and low grade fever for three days..."
}
```

### Response

```json
{
  "id": "ast_01J...",
  "status": "completed",
  "type": "clinical_assistance",
  "suggestions": {
    "diagnoses": [],
    "assessment": "...",
    "treatment_plan": "..."
  }
}
```

For longer-running AI operations:

```text
queued
processing
completed
failed
```

The backend should not expose provider-specific details such as:

```text
OpenAI
Bedrock
Claude
Nova
GPT
```

to the frontend unless there is a specific product requirement.

---

# 9. Documents

The frontend needs document uploads for:

- Lab reports
- Medical images
- Patient documents
- Encounter attachments
- Other clinical files

The existing Clavis backend already uses S3 presigned URLs.

## Recommended endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/uploads` | Create an upload session |
| `POST` | `/uploads/{upload_id}/complete` | Complete upload |
| `POST` | `/documents` | Create document metadata |
| `GET` | `/documents/{document_id}` | Retrieve document |
| `DELETE` | `/documents/{document_id}` | Delete document |

### Start upload

```http
POST /api/v1/uploads
```

```json
{
  "filename": "cbc-report.pdf",
  "content_type": "application/pdf",
  "size": 582341
}
```

Response:

```json
{
  "upload_id": "upl_01J...",
  "upload_url": "https://s3.amazonaws.com/...",
  "expires_at": "2026-10-01T11:00:00Z"
}
```

The frontend uploads directly to S3.

Then:

```http
POST /api/v1/uploads/upl_01J.../complete
```

This allows the backend to verify that the upload completed and create/associate the document.

---

# 10. Notifications

The frontend contains a notification center.

## Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/notifications` | List notifications |
| `GET` | `/notifications/{notification_id}` | Retrieve notification |
| `PATCH` | `/notifications/{notification_id}` | Update notification |

Example:

```http
GET /api/v1/notifications?read=false
```

Response:

```json
{
  "items": [
    {
      "id": "ntf_01J...",
      "type": "patient",
      "title": "Lab result available",
      "message": "Rahul Kumar's CBC results are ready.",
      "read": false,
      "created_at": "2026-10-01T09:30:00Z"
    }
  ],
  "total": 1
}
```

Mark as read:

```http
PATCH /api/v1/notifications/ntf_01J...
```

```json
{
  "read": true
}
```

---

# 11. Diagnoses

The frontend needs diagnosis search and common diagnoses.

The dashboard currently displays common diagnoses such as:

- Hypertension
- Type 2 Diabetes Mellitus
- Acute Upper Respiratory Infection
- Bronchitis
- Community Acquired Pneumonia
- Dengue Fever
- Typhoid Fever

The API should treat diagnoses as a searchable catalog.

## Endpoint

```http
GET /api/v1/diagnoses
```

Examples:

```http
GET /api/v1/diagnoses?q=hypertension
```

```http
GET /api/v1/diagnoses?common=true
```

```http
GET /api/v1/diagnoses?code=I10
```

Example response:

```json
{
  "items": [
    {
      "id": "diag_01J...",
      "code": "I10",
      "coding_system": "ICD-10",
      "name": "Essential hypertension"
    }
  ]
}
```

Using standardized clinical coding systems should be preferred where appropriate.

---

# 12. Medicines

The frontend provides:

> Search Medicines — Brand / Generic

## Endpoint

```http
GET /api/v1/medicines
```

Examples:

```http
GET /api/v1/medicines?q=amoxicillin
```

```http
GET /api/v1/medicines?q=amox&form=capsule
```

Example response:

```json
{
  "items": [
    {
      "id": "med_01J...",
      "generic_name": "Amoxicillin",
      "brand_name": "Example Brand",
      "strength": "500 mg",
      "form": "capsule"
    }
  ]
}
```

The medicine catalog should eventually use a standardized drug identifier where possible.

---

# 13. Tests and Investigations

The frontend has an:

> Order Tests — Lab / Imaging

workflow.

There are two distinct concepts:

```text
Test
│
└── A test that exists in the catalog

Test Order
│
└── A doctor ordering that test for a patient
```

These should not be merged.

## Test catalog

```http
GET /api/v1/tests
```

Examples:

```http
GET /api/v1/tests?q=cbc
```

```http
GET /api/v1/tests?q=chest+xray
```

Example:

```json
{
  "items": [
    {
      "id": "test_01J...",
      "name": "Complete Blood Count",
      "category": "laboratory"
    }
  ]
}
```

---

# 14. Test Orders

## Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/test-orders` | Create test order |
| `GET` | `/test-orders/{test_order_id}` | Retrieve order |
| `GET` | `/patients/{patient_id}/test-orders` | Patient's test orders |

### Create order

```http
POST /api/v1/test-orders
```

```json
{
  "patient_id": "pat_01J...",
  "encounter_id": "enc_01J...",
  "tests": [
    {
      "test_id": "test_01J..."
    }
  ]
}
```

Possible statuses:

```text
ordered
collected
processing
completed
cancelled
```

---

# 15. Test Results

Test results should eventually be separate from test orders.

```http
GET /api/v1/patients/{patient_id}/test-results
```

Individual result:

```http
GET /api/v1/test-results/{test_result_id}
```

This creates a clean relationship:

```text
Test
  ↓
Test Order
  ↓
Test Result
```

---

# 16. Treatment Templates

The frontend contains a Treatment Templates section.

## Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/treatment-templates` | List templates |
| `POST` | `/treatment-templates` | Create template |
| `GET` | `/treatment-templates/{template_id}` | Retrieve template |
| `PATCH` | `/treatment-templates/{template_id}` | Update template |
| `DELETE` | `/treatment-templates/{template_id}` | Delete template |

Example:

```json
{
  "title": "Upper Respiratory Infection",
  "description": "Standard treatment template",
  "type": "treatment",
  "content": "...",
  "updated_at": "2026-10-01T09:00:00Z"
}
```

Templates may eventually belong to:

```text
Doctor
Clinic
Organization
```

For a multi-doctor deployment, clinic/organization ownership should be considered early.

---

# 17. Statistics

The frontend currently requires an overview statistics endpoint.

## Endpoint

```http
GET /api/v1/statistics/overview
```

Possible response:

```json
{
  "patients": {
    "total": 1248,
    "new_this_month": 47
  },
  "encounters": {
    "total": 5321,
    "this_month": 184
  },
  "notes": {
    "total": 5210
  },
  "pending_tasks": 12
}
```

Additional statistics endpoints can be introduced later if the UI requires them:

```http
GET /api/v1/statistics/encounters
GET /api/v1/statistics/patients
GET /api/v1/statistics/revenue
```

Do not build these until they are actually needed.

---

# 18. Billing

The frontend contains a payment/billing page.

Billing should be implemented through server-side Stripe integration.

## Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/billing/plans` | List available plans |
| `GET` | `/billing/subscription` | Current subscription |
| `POST` | `/billing/checkout-sessions` | Create Stripe Checkout session |
| `POST` | `/billing/portal-sessions` | Create Stripe customer portal session |

## Stripe webhook

```http
POST /api/v1/webhooks/stripe
```

The browser should **not** directly manipulate subscription state.

The flow should be:

```text
Nuxt frontend
      │
      │ POST /billing/checkout-sessions
      ▼
Clavis API
      │
      │ Stripe API
      ▼
Stripe Checkout
      │
      │ webhook
      ▼
Clavis API
      │
      ▼
Database
```

Stripe webhooks should be the authoritative source for subscription lifecycle events.

---

# 19. Global Search

The dashboard contains a global search interface:

```text
Search patients, notes, diagnosis, medications...
```

A unified search endpoint can eventually support this.

## Endpoint

```http
GET /api/v1/search?q=rahul
```

Example response:

```json
{
  "patients": [],
  "notes": [],
  "diagnoses": [],
  "medicines": []
}
```

This is optional for the initial backend implementation.

Resource-specific searches should still use their own collections:

```http
GET /api/v1/patients?q=rahul
GET /api/v1/diagnoses?q=hypertension
GET /api/v1/medicines?q=amoxicillin
GET /api/v1/tests?q=cbc
```

---

# 20. Health Check

The API should expose a public or infrastructure-level health endpoint.

```http
GET /api/v1/health
```

Example:

```json
{
  "status": "ok"
}
```

For production infrastructure, it is useful to distinguish:

```http
GET /health/live
GET /health/ready
```

where:

- `live` checks whether the application process is alive.
- `ready` checks whether the application can serve traffic, including required dependencies.

These can remain outside `/api/v1` because they are infrastructure endpoints rather than application resources.

---

# 21. Recommended Final API Structure

The complete application API becomes:

```text
/api/v1
│
├── auth
│   ├── POST   /register
│   ├── POST   /login
│   ├── POST   /refresh
│   ├── POST   /logout
│   ├── GET    /me
│   ├── POST   /verify-email
│   ├── POST   /resend-verification
│   ├── POST   /forgot-password
│   ├── POST   /reset-password
│   └── POST   /change-password
│
├── profile
│   ├── GET    /
│   └── PATCH  /
│
├── patients
│   ├── GET    /
│   ├── POST   /
│   ├── GET    /{patient_id}
│   ├── PATCH  /{patient_id}
│   ├── DELETE /{patient_id}
│   ├── GET    /{patient_id}/encounters
│   ├── GET    /{patient_id}/documents
│   ├── GET    /{patient_id}/medications
│   ├── GET    /{patient_id}/diagnoses
│   └── GET    /{patient_id}/test-results
│
├── encounters
│   ├── POST   /
│   ├── GET    /{encounter_id}
│   ├── PATCH  /{encounter_id}
│   ├── DELETE /{encounter_id}
│   └──
│
├── encounters/{encounter_id}/notes
│   ├── GET    /
│   └── POST   /
│
├── notes
│   ├── GET    /{note_id}
│   ├── PATCH  /{note_id}
│   └── DELETE /{note_id}
│
├── transcriptions
│   ├── POST   /
│   └── GET    /{transcription_id}
│
├── ai
│   ├── POST   /assistance
│   └── GET    /assistance/{assistance_id}
│
├── uploads
│   ├── POST   /
│   └── POST   /{upload_id}/complete
│
├── documents
│   ├── POST   /
│   ├── GET    /{document_id}
│   ├── DELETE /{document_id}
│   └── POST   /{document_id}/complete
│
├── notifications
│   ├── GET    /
│   ├── GET    /{notification_id}
│   └── PATCH  /{notification_id}
│
├── diagnoses
│   └── GET    /
│
├── medicines
│   └── GET    /
│
├── tests
│   └── GET    /
│
├── test-orders
│   ├── POST   /
│   ├── GET    /{test_order_id}
│   └──
│
├── test-results
│   └── GET    /{test_result_id}
│
├── treatment-templates
│   ├── GET    /
│   ├── POST   /
│   ├── GET    /{template_id}
│   ├── PATCH  /{template_id}
│   └── DELETE /{template_id}
│
├── statistics
│   └── GET    /overview
│
├── billing
│   ├── GET    /plans
│   ├── GET    /subscription
│   ├── POST   /checkout-sessions
│   └── POST   /portal-sessions
│
└── webhooks
    └── POST   /stripe
```

---

# 22. Recommended Implementation Order

Do not implement all endpoints simultaneously.

Build the backend in layers.

## Phase 1 — Authentication

```text
/auth/register
/auth/login
/auth/refresh
/auth/logout
/auth/me
/auth/verify-email
/auth/forgot-password
/auth/reset-password
```

Then:

```text
/profile
```

This gives the frontend a working authenticated session.

---

## Phase 2 — Patient Management

```text
/patients
/patients/{patient_id}
/patients/{patient_id}/encounters
```

At this point the dashboard can display real patients.

---

## Phase 3 — Consultation Workflow

```text
/encounters
/encounters/{encounter_id}
/encounters/{encounter_id}/notes
/notes/{note_id}
```

This establishes the core clinical workflow.

---

## Phase 4 — Documents and Scribe

```text
/uploads
/documents
/transcriptions
```

Then connect:

```text
Audio
  ↓
Upload
  ↓
Transcription
  ↓
Encounter
  ↓
Clinical Note
```

---

## Phase 5 — AI Assistance

```text
/ai/assistance
```

Connect the AI layer to the encounter and clinical-note workflow.

The important architectural principle is:

```text
AI output
   ↓
Doctor review
   ↓
Doctor approval
   ↓
Clinical record
```

AI-generated content should not automatically become the final clinical record.

---

## Phase 6 — Clinical Reference Data

Implement:

```text
/diagnoses
/medicines
/tests
/test-orders
/test-results
/treatment-templates
```

These power the clinical tools shown throughout the dashboard.

---

## Phase 7 — Notifications and Statistics

```text
/notifications
/statistics/overview
```

These support the dashboard and operational workflow.

---

## Phase 8 — Billing

Finally:

```text
/billing/plans
/billing/subscription
/billing/checkout-sessions
/billing/portal-sessions
/webhooks/stripe
```

---

# 23. Recommended Domain Structure in FastAPI

Given the current Clavis backend, I would organize the application approximately like this:

```text
app/
├── api/
│   └── v1/
│       ├── router.py
│       ├── auth.py
│       ├── profile.py
│       ├── patients.py
│       ├── encounters.py
│       ├── notes.py
│       ├── documents.py
│       ├── uploads.py
│       ├── transcriptions.py
│       ├── ai.py
│       ├── diagnoses.py
│       ├── medicines.py
│       ├── tests.py
│       ├── test_orders.py
│       ├── treatment_templates.py
│       ├── notifications.py
│       ├── statistics.py
│       ├── billing.py
│       └── webhooks.py
│
├── domain/
│   ├── users/
│   ├── patients/
│   ├── encounters/
│   ├── notes/
│   ├── documents/
│   ├── transcriptions/
│   ├── diagnoses/
│   ├── medicines/
│   ├── tests/
│   ├── notifications/
│   └── billing/
│
├── models/
├── schemas/
├── services/
├── repositories/
├── auth/
└── core/
```

The exact directory structure can differ, but the important separation is:

```text
HTTP/API layer
      ↓
Application/service layer
      ↓
Domain logic
      ↓
Repository/data-access layer
      ↓
PostgreSQL / S3 / external services
```

---

# 24. Important API Design Rules for Clavis

## Do not expose database implementation details

Bad:

```json
{
  "postgres_id": 42,
  "s3_object_key": "users/12/...",
  "password_hash": "..."
}
```

Good:

```json
{
  "id": "pat_01J...",
  "document_url": "https://..."
}
```

---

## Do not expose AI provider implementation

The frontend should not care whether Clavis uses:

```text
AWS Bedrock
OpenAI
Anthropic
Google
local models
```

The frontend talks to:

```http
POST /api/v1/ai/assistance
```

The backend owns the implementation.

---

## Use stable resource IDs

Prefer IDs such as:

```text
pat_01J...
enc_01J...
note_01J...
doc_01J...
trn_01J...
```

rather than exposing sequential database IDs where possible.

---

## Use ISO 8601 timestamps

Example:

```text
2026-10-01T10:30:00Z
```

Do not return ambiguous strings such as:

```text
01/10/2026 10:30 AM
```

The frontend should handle localization.

---

## Use pagination

Large collections should not return everything.

For example:

```http
GET /api/v1/patients?page=1&page_size=25
```

A response can use:

```json
{
  "items": [],
  "page": 1,
  "page_size": 25,
  "total": 248
}
```

Cursor pagination can be introduced later where needed.

---

# 25. Error Response Format

Use a consistent error structure throughout the API.

For example:

```json
{
  "error": {
    "code": "patient_not_found",
    "message": "Patient was not found.",
    "details": null
  }
}
```

For validation:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed.",
    "details": {
      "email": [
        "Invalid email address."
      ]
    }
  }
}
```

This makes frontend error handling significantly easier.

---

# 26. HTTP Status Codes

Use conventional HTTP status codes.

| Status | Usage |
|---|---|
| `200` | Successful retrieval/update |
| `201` | Resource successfully created |
| `202` | Asynchronous operation accepted |
| `204` | Successful operation with no response body |
| `400` | Invalid request |
| `401` | Authentication required/invalid |
| `403` | Authenticated but not authorized |
| `404` | Resource not found |
| `409` | Resource conflict |
| `422` | Validation failure |
| `429` | Rate limit exceeded |
| `500` | Unexpected server error |

For example, an asynchronous AI request should preferably return:

```http
202 Accepted
```

rather than pretending the operation completed synchronously.

---

# 27. MVP Endpoint Checklist

The minimum backend required to make the current Clavis frontend substantially functional is:

### Authentication

```text
[ ] POST /auth/register
[ ] POST /auth/login
[ ] POST /auth/refresh
[ ] POST /auth/logout
[ ] GET  /auth/me
[ ] POST /auth/verify-email
[ ] POST /auth/forgot-password
[ ] POST /auth/reset-password
```

### Profile

```text
[ ] GET   /profile
[ ] PATCH /profile
```

### Patients

```text
[ ] GET   /patients
[ ] POST  /patients
[ ] GET   /patients/{patient_id}
[ ] PATCH /patients/{patient_id}
[ ] DELETE /patients/{patient_id}
```

### Encounters

```text
[ ] POST  /encounters
[ ] GET   /encounters/{encounter_id}
[ ] PATCH /encounters/{encounter_id}
[ ] GET   /patients/{patient_id}/encounters
```

### Notes

```text
[ ] GET   /notes/{note_id}
[ ] POST  /encounters/{encounter_id}/notes
[ ] PATCH /notes/{note_id}
[ ] DELETE /notes/{note_id}
```

### Documents

```text
[ ] POST /uploads
[ ] POST /uploads/{upload_id}/complete
[ ] POST /documents
[ ] GET  /documents/{document_id}
[ ] DELETE /documents/{document_id}
```

### Scribe

```text
[ ] POST /transcriptions
[ ] GET  /transcriptions/{transcription_id}
```

### AI

```text
[ ] POST /ai/assistance
[ ] GET  /ai/assistance/{assistance_id}
```

### Clinical catalogs

```text
[ ] GET /diagnoses
[ ] GET /medicines
[ ] GET /tests
```

### Clinical workflow

```text
[ ] POST /test-orders
[ ] GET  /test-orders/{test_order_id}
[ ] GET  /patients/{patient_id}/test-orders
[ ] GET  /patients/{patient_id}/test-results
```

### Templates

```text
[ ] GET    /treatment-templates
[ ] POST   /treatment-templates
[ ] GET    /treatment-templates/{template_id}
[ ] PATCH  /treatment-templates/{template_id}
[ ] DELETE /treatment-templates/{template_id}
```

### Dashboard

```text
[ ] GET /notifications
[ ] GET /statistics/overview
```

### Billing

```text
[ ] GET  /billing/plans
[ ] GET  /billing/subscription
[ ] POST /billing/checkout-sessions
[ ] POST /billing/portal-sessions
[ ] POST /webhooks/stripe
```

---

# 28. Final Architecture

The resulting Clavis architecture should look roughly like this:

```text
                         ┌─────────────────────┐
                         │    Nuxt Frontend    │
                         │                     │
                         │  Doctor Workspace   │
                         └──────────┬──────────┘
                                    │
                                    │ HTTPS
                                    ▼
                         ┌─────────────────────┐
                         │     Clavis API      │
                         │     FastAPI         │
                         │                     │
                         │      /api/v1        │
                         └──────────┬──────────┘
                                    │
             ┌──────────────────────┼──────────────────────┐
             │                      │                      │
             ▼                      ▼                      ▼
       ┌───────────┐          ┌───────────┐         ┌─────────────┐
       │ PostgreSQL│          │    S3     │         │ AI Services │
       │           │          │           │         │             │
       │ Patients  │          │ Documents │         │ Scribe      │
       │ Encounters│          │ Audio     │         │ Assistance  │
       │ Notes     │          │ Reports   │         │             │
       └───────────┘          └───────────┘         └─────────────┘
                                   
                         ┌─────────────────────┐
                         │ External Services   │
                         │                     │
                         │ Stripe              │
                         │ Email               │
                         │ Clinical catalogs   │
                         └─────────────────────┘
```

The core relationship should ultimately be:

```text
Doctor
  │
  └── Patient
        │
        └── Encounter
              │
              ├── Transcription
              ├── Conversation
              ├── Clinical Note
              ├── Documents
              ├── Diagnoses
              ├── Test Orders
              ├── Test Results
              └── Treatment Plan
```

This gives Clavis a proper clinical-domain foundation instead of treating it as a generic note-taking application with AI features bolted on.