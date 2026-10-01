# Clavis Frontend — Backend API Specification

**Version:** `v1`  
**Base URL:** `https://api.clavis.com/api/v1`

This document defines the backend API required to support the Clavis medical scribe frontend.

The API follows REST-oriented conventions, uses resource-oriented URLs, and separates clinical resources such as patients, encounters, notes, documents, diagnoses, test orders, and test results.

> **Scope:** AI model selection/configuration endpoints are intentionally excluded.

---

# 1. API Design Principles

## Base URL

```text
https://api.clavis.com/api/v1
```

## URL conventions

Use plural resource names:

```text
GET    /patients
POST   /patients
GET    /patients/{patient_id}
PATCH  /patients/{patient_id}
DELETE /patients/{patient_id}
```

Avoid action-oriented URLs such as:

```text
GET /getPatients
POST /createPatient
POST /patients/search
```

For searches, prefer query parameters:

```text
GET /patients?q=rahul
GET /medicines?q=amoxicillin
GET /diagnoses?q=hypertension
```

## JSON conventions

Requests and responses use JSON unless otherwise specified.

Dates:

```text
2026-10-01
```

Timestamps:

```text
2026-10-01T10:30:00Z
```

IDs should be opaque identifiers, preferably UUIDs:

```text
"patient_id": "018f5e5e-7c5a-7b3a-9f8d-123456789abc"
```

---

# 2. Standard Response Structure

Successful single-resource responses should generally return the resource directly:

```json
{
  "id": "uuid",
  "name": "John Doe"
}
```

Collection responses should be paginated:

```json
{
  "items": [],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

## Pagination schema

```python
class Pagination(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
```

```python
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    pagination: Pagination
```

---

# 3. Standard Error Schema

Every API error should use a consistent structure.

```python
class ErrorDetail(BaseModel):
    code: str
    message: str
    field: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
```

Example:

```json
{
  "error": {
    "code": "PATIENT_NOT_FOUND",
    "message": "Patient was not found.",
    "field": null
  }
}
```

Validation error:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request.",
    "field": "date_of_birth"
  }
}
```

---

# 4. Authentication

## 4.1 Register

```http
POST /auth/register
```

### Request

```python
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
```

Example:

```json
{
  "email": "doctor@example.com",
  "password": "StrongPassword123!",
  "first_name": "John",
  "last_name": "Smith"
}
```

### Response

```python
class RegisterResponse(BaseModel):
    user_id: UUID
    email: EmailStr
    message: str
    verification_required: bool
```

```json
{
  "user_id": "uuid",
  "email": "doctor@example.com",
  "message": "Account created successfully.",
  "verification_required": true
}
```

---

# 5. Login

```http
POST /auth/login
```

### Request

```python
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
```

### Response

```python
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"]
    expires_in: int
```

Example:

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900
}
```

---

# 6. Refresh Token

```http
POST /auth/refresh
```

### Request

```python
class RefreshTokenRequest(BaseModel):
    refresh_token: str
```

### Response

```python
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"]
    expires_in: int
```

---

# 7. Logout

```http
POST /auth/logout
```

### Request

```python
class LogoutRequest(BaseModel):
    refresh_token: str
```

### Response

```python
class MessageResponse(BaseModel):
    message: str
```

```json
{
  "message": "Logged out successfully."
}
```

---

# 8. Current User

```http
GET /auth/me
```

### Response

```python
class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    role: str
    email_verified: bool
    created_at: datetime
```

---

# 9. Email Verification

```http
POST /auth/verify-email
```

### Request

```python
class VerifyEmailRequest(BaseModel):
    token: str
```

### Response

```python
class MessageResponse(BaseModel):
    message: str
```

---

# 10. Resend Verification Email

```http
POST /auth/resend-verification
```

### Request

```python
class ResendVerificationRequest(BaseModel):
    email: EmailStr
```

### Response

```python
class MessageResponse(BaseModel):
    message: str
```

---

# 11. Password Reset

## Request password reset

```http
POST /auth/forgot-password
```

### Request

```python
class ForgotPasswordRequest(BaseModel):
    email: EmailStr
```

### Response

```json
{
  "message": "If the account exists, a password reset email has been sent."
}
```

## Reset password

```http
POST /auth/reset-password
```

### Request

```python
class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
```

### Response

```python
class MessageResponse(BaseModel):
    message: str
```

---

# 12. Change Password

```http
POST /auth/change-password
```

### Request

```python
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
```

### Response

```json
{
  "message": "Password changed successfully."
}
```

---

# 13. Doctor Profile

## Get profile

```http
GET /profile
```

### Response

```python
class ProfileResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None
    specialization: str | None
    license_number: str | None
    profile_image_url: str | None
```

## Update profile

```http
PATCH /profile
```

### Request

```python
class ProfileUpdateRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    specialization: str | None = None
    license_number: str | None = None
```

### Response

```python
ProfileResponse
```

---

# 14. Patients

Patients are one of the core resources in Clavis.

## List patients

```http
GET /patients
```

### Query parameters

```text
?q=john
&page=1
&page_size=20
```

### Response

```python
class PatientSummary(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    date_of_birth: date | None
    gender: str | None
    phone: str | None
    last_visit_at: datetime | None
```

```python
class PatientListResponse(BaseModel):
    items: list[PatientSummary]
    pagination: Pagination
```

---

# 15. Create Patient

```http
POST /patients
```

### Request

```python
class PatientCreateRequest(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date | None = None
    gender: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    notes: str | None = None
```

### Response

```python
class PatientResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    date_of_birth: date | None
    gender: str | None
    phone: str | None
    email: EmailStr | None
    address: str | None
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
```

---

# 16. Get Patient

```http
GET /patients/{patient_id}
```

### Response

```python
PatientResponse
```

---

# 17. Update Patient

```http
PATCH /patients/{patient_id}
```

### Request

```python
class PatientUpdateRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    notes: str | None = None
```

### Response

```python
PatientResponse
```

---

# 18. Delete Patient

```http
DELETE /patients/{patient_id}
```

### Response

```json
{
  "message": "Patient deleted successfully."
}
```

For a medical application, this should generally be implemented as a controlled/soft deletion rather than immediately destroying clinical records.

---

# 19. Patient Encounters

```http
GET /patients/{patient_id}/encounters
```

### Query parameters

```text
?page=1
&page_size=20
&from=2026-01-01
&to=2026-10-01
```

### Response

```python
class EncounterSummary(BaseModel):
    id: UUID
    patient_id: UUID
    doctor_id: UUID
    started_at: datetime
    ended_at: datetime | None
    status: str
    chief_complaint: str | None
```

```python
class EncounterListResponse(BaseModel):
    items: list[EncounterSummary]
    pagination: Pagination
```

---

# 20. Create Encounter

```http
POST /encounters
```

### Request

```python
class EncounterCreateRequest(BaseModel):
    patient_id: UUID
    chief_complaint: str | None = None
    started_at: datetime | None = None
```

### Response

```python
class EncounterResponse(BaseModel):
    id: UUID
    patient_id: UUID
    doctor_id: UUID
    chief_complaint: str | None
    started_at: datetime
    ended_at: datetime | None
    status: str
    created_at: datetime
    updated_at: datetime
```

---

# 21. Get Encounter

```http
GET /encounters/{encounter_id}
```

### Response

```python
EncounterResponse
```

---

# 22. Update Encounter

```http
PATCH /encounters/{encounter_id}
```

### Request

```python
class EncounterUpdateRequest(BaseModel):
    chief_complaint: str | None = None
    ended_at: datetime | None = None
    status: str | None = None
```

### Response

```python
EncounterResponse
```

---

# 23. Delete Encounter

```http
DELETE /encounters/{encounter_id}
```

### Response

```json
{
  "message": "Encounter deleted successfully."
}
```

---

# 24. Clinical Notes

Notes belong to encounters.

## List encounter notes

```http
GET /encounters/{encounter_id}/notes
```

### Response

```python
class NoteSummary(BaseModel):
    id: UUID
    encounter_id: UUID
    title: str | None
    status: str
    created_at: datetime
    updated_at: datetime
```

```python
class NoteListResponse(BaseModel):
    items: list[NoteSummary]
    pagination: Pagination
```

---

# 25. Create Note

```http
POST /encounters/{encounter_id}/notes
```

### Request

```python
class NoteCreateRequest(BaseModel):
    title: str | None = None
    content: str
    note_type: str = "clinical"
```

### Response

```python
class NoteResponse(BaseModel):
    id: UUID
    encounter_id: UUID
    patient_id: UUID
    title: str | None
    content: str
    note_type: str
    status: str
    created_at: datetime
    updated_at: datetime
```

---

# 26. Get Note

```http
GET /notes/{note_id}
```

### Response

```python
NoteResponse
```

---

# 27. Update Note

```http
PATCH /notes/{note_id}
```

### Request

```python
class NoteUpdateRequest(BaseModel):
    title: str | None = None
    content: str | None = None
    status: str | None = None
```

### Response

```python
NoteResponse
```

---

# 28. Delete Note

```http
DELETE /notes/{note_id}
```

### Response

```json
{
  "message": "Note deleted successfully."
}
```

Your existing `deleted_at` / recycle-bin implementation can continue to support this endpoint.

---

# 29. Transcriptions

A transcription represents the raw output of a recorded consultation.

## Create transcription

```http
POST /transcriptions
```

### Request

```python
class TranscriptionCreateRequest(BaseModel):
    encounter_id: UUID
    text: str
    language: str | None = None
    duration_seconds: int | None = None
```

### Response

```python
class TranscriptionResponse(BaseModel):
    id: UUID
    encounter_id: UUID
    text: str
    language: str | None
    duration_seconds: int | None
    status: str
    created_at: datetime
```

---

# 30. Get Transcription

```http
GET /transcriptions/{transcription_id}
```

### Response

```python
TranscriptionResponse
```

---

# 31. AI Assistance

AI assistance should produce a **draft or recommendation** that the doctor can review.

It should not silently become part of the patient's final medical record.

## Create AI assistance

```http
POST /ai/assistance
```

### Request

```python
class AIAssistanceRequest(BaseModel):
    encounter_id: UUID
    input_text: str
    assistance_type: Literal[
        "clinical_note",
        "summary",
        "diagnosis",
        "treatment_plan",
        "patient_instructions"
    ]
    context: dict[str, Any] | None = None
```

### Response

```python
class AIAssistanceResponse(BaseModel):
    id: UUID
    encounter_id: UUID
    assistance_type: str
    content: str
    status: Literal["draft", "accepted", "rejected"]
    created_at: datetime
```

---

# 32. Get AI Assistance

```http
GET /ai/assistance/{assistance_id}
```

### Response

```python
AIAssistanceResponse
```

---

# 33. Documents

Documents may include medical reports, prescriptions, scans, referrals, and other uploaded files.

Because Clavis already uses S3 presigned URLs, the upload flow should remain separate from the application API.

## Request upload

```http
POST /uploads
```

### Request

```python
class UploadCreateRequest(BaseModel):
    filename: str
    content_type: str
    size_bytes: int
    patient_id: UUID | None = None
    encounter_id: UUID | None = None
```

### Response

```python
class UploadResponse(BaseModel):
    upload_id: UUID
    object_key: str
    upload_url: str
    expires_in: int
```

The frontend uploads directly to S3 using `upload_url`.

---

# 34. Complete Upload

```http
POST /uploads/{upload_id}/complete
```

### Request

```python
class UploadCompleteRequest(BaseModel):
    checksum: str | None = None
```

### Response

```python
class UploadCompleteResponse(BaseModel):
    upload_id: UUID
    status: Literal["completed"]
```

---

# 35. Create Document

```http
POST /documents
```

### Request

```python
class DocumentCreateRequest(BaseModel):
    upload_id: UUID
    patient_id: UUID
    encounter_id: UUID | None = None
    document_type: str
    title: str | None = None
```

### Response

```python
class DocumentResponse(BaseModel):
    id: UUID
    patient_id: UUID
    encounter_id: UUID | None
    filename: str
    document_type: str
    title: str | None
    status: str
    created_at: datetime
```

---

# 36. Get Document

```http
GET /documents/{document_id}
```

### Response

```python
class DocumentResponse(BaseModel):
    id: UUID
    patient_id: UUID
    encounter_id: UUID | None
    filename: str
    document_type: str
    title: str | None
    download_url: str | None
    status: str
    created_at: datetime
```

The `download_url` should be a short-lived S3 presigned URL.

---

# 37. Delete Document

```http
DELETE /documents/{document_id}
```

### Response

```json
{
  "message": "Document deleted successfully."
}
```

---

# 38. Patient Documents

```http
GET /patients/{patient_id}/documents
```

### Query parameters

```text
?page=1
&page_size=20
&type=lab_report
```

### Response

```python
class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    pagination: Pagination
```

---

# 39. Diagnoses

The diagnosis endpoint should support both searching and common diagnoses.

Instead of:

```text
GET /diagnoses/search
```

use:

```text
GET /diagnoses?q=hypertension
```

## Search diagnoses

```http
GET /diagnoses?q=hypertension
```

### Query parameters

```text
q
code
common
page
page_size
```

### Response

```python
class DiagnosisResponse(BaseModel):
    id: UUID
    name: str
    code: str | None
    coding_system: str | None
```

```python
class DiagnosisListResponse(BaseModel):
    items: list[DiagnosisResponse]
    pagination: Pagination
```

---

# 40. Medicines

```http
GET /medicines?q=amoxicillin
```

### Query parameters

```text
q
page
page_size
```

### Response

```python
class MedicineResponse(BaseModel):
    id: UUID
    name: str
    generic_name: str | None
    brand_name: str | None
    strength: str | None
    dosage_form: str | None
```

```python
class MedicineListResponse(BaseModel):
    items: list[MedicineResponse]
    pagination: Pagination
```

---

# 41. Tests

Tests represent available laboratory/diagnostic tests.

```http
GET /tests?q=cbc
```

### Response

```python
class TestResponse(BaseModel):
    id: UUID
    name: str
    code: str | None
    category: str | None
    description: str | None
```

```python
class TestListResponse(BaseModel):
    items: list[TestResponse]
    pagination: Pagination
```

---

# 42. Test Orders

A **test** is what can be ordered.

A **test order** is a doctor's request for that test for a particular patient.

## Create test order

```http
POST /test-orders
```

### Request

```python
class TestOrderCreateRequest(BaseModel):
    patient_id: UUID
    encounter_id: UUID | None = None
    test_id: UUID
    priority: Literal["routine", "urgent"] = "routine"
    clinical_notes: str | None = None
```

### Response

```python
class TestOrderResponse(BaseModel):
    id: UUID
    patient_id: UUID
    encounter_id: UUID | None
    test_id: UUID
    test_name: str
    priority: str
    status: str
    clinical_notes: str | None
    ordered_at: datetime
```

---

# 43. Get Test Order

```http
GET /test-orders/{test_order_id}
```

### Response

```python
TestOrderResponse
```

---

# 44. Patient Test Orders

```http
GET /patients/{patient_id}/test-orders
```

### Query parameters

```text
?page=1
&page_size=20
&status=pending
```

### Response

```python
class TestOrderListResponse(BaseModel):
    items: list[TestOrderResponse]
    pagination: Pagination
```

---

# 45. Test Results

Test results are separate from test orders.

## Get test result

```http
GET /test-results/{test_result_id}
```

### Response

```python
class TestResultResponse(BaseModel):
    id: UUID
    test_order_id: UUID
    patient_id: UUID
    test_id: UUID
    test_name: str
    result: str
    unit: str | None
    reference_range: str | None
    status: str
    performed_at: datetime | None
    verified_at: datetime | None
```

---

# 46. Patient Test Results

```http
GET /patients/{patient_id}/test-results
```

### Query parameters

```text
?page=1
&page_size=20
&from=2026-01-01
&to=2026-10-01
```

### Response

```python
class TestResultListResponse(BaseModel):
    items: list[TestResultResponse]
    pagination: Pagination
```

---

# 47. Patient Diagnoses

```http
GET /patients/{patient_id}/diagnoses
```

### Response

```python
class PatientDiagnosisResponse(BaseModel):
    id: UUID
    diagnosis: DiagnosisResponse
    encounter_id: UUID | None
    diagnosed_at: datetime
    status: str
```

```python
class PatientDiagnosisListResponse(BaseModel):
    items: list[PatientDiagnosisResponse]
    pagination: Pagination
```

---

# 48. Patient Medications

```http
GET /patients/{patient_id}/medications
```

### Response

```python
class PatientMedicationResponse(BaseModel):
    id: UUID
    medicine: MedicineResponse
    dosage: str | None
    frequency: str | None
    route: str | None
    duration: str | None
    instructions: str | None
    started_at: date | None
    ended_at: date | None
    active: bool
```

```python
class PatientMedicationListResponse(BaseModel):
    items: list[PatientMedicationResponse]
    pagination: Pagination
```

---

# 49. Treatment Templates

Treatment templates allow doctors to reuse common treatment plans.

## List templates

```http
GET /treatment-templates
```

### Query parameters

```text
?q=diabetes
&page=1
&page_size=20
```

### Response

```python
class TreatmentTemplateSummary(BaseModel):
    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
```

```python
class TreatmentTemplateListResponse(BaseModel):
    items: list[TreatmentTemplateSummary]
    pagination: Pagination
```

---

# 50. Create Treatment Template

```http
POST /treatment-templates
```

### Request

```python
class TreatmentTemplateCreateRequest(BaseModel):
    name: str
    description: str | None = None
    content: str
```

### Response

```python
class TreatmentTemplateResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    content: str
    created_at: datetime
    updated_at: datetime
```

---

# 51. Get Treatment Template

```http
GET /treatment-templates/{template_id}
```

### Response

```python
TreatmentTemplateResponse
```

---

# 52. Update Treatment Template

```http
PATCH /treatment-templates/{template_id}
```

### Request

```python
class TreatmentTemplateUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    content: str | None = None
```

### Response

```python
TreatmentTemplateResponse
```

---

# 53. Delete Treatment Template

```http
DELETE /treatment-templates/{template_id}
```

### Response

```json
{
  "message": "Treatment template deleted successfully."
}
```

---

# 54. Notifications

## List notifications

```http
GET /notifications
```

### Query parameters

```text
?page=1
&page_size=20
&unread=true
```

### Response

```python
class NotificationResponse(BaseModel):
    id: UUID
    type: str
    title: str
    message: str
    read: bool
    created_at: datetime
```

```python
class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    pagination: Pagination
```

---

# 55. Get Notification

```http
GET /notifications/{notification_id}
```

### Response

```python
NotificationResponse
```

---

# 56. Mark Notification as Read

```http
PATCH /notifications/{notification_id}
```

### Request

```python
class NotificationUpdateRequest(BaseModel):
    read: bool
```

### Response

```python
NotificationResponse
```

---

# 57. Statistics

The dashboard needs aggregated statistics.

```http
GET /statistics/overview
```

### Query parameters

```text
?from=2026-09-01
&to=2026-10-01
```

### Response

```python
class StatisticsOverviewResponse(BaseModel):
    total_patients: int
    new_patients: int
    total_encounters: int
    total_notes: int
    total_transcriptions: int
    total_documents: int
    pending_test_orders: int
```

Example:

```json
{
  "total_patients": 482,
  "new_patients": 37,
  "total_encounters": 613,
  "total_notes": 598,
  "total_transcriptions": 411,
  "total_documents": 932,
  "pending_test_orders": 14
}
```

---

# 58. Billing

Billing should remain separate from clinical resources.

## Plans

```http
GET /billing/plans
```

### Response

```python
class BillingPlanResponse(BaseModel):
    id: str
    name: str
    description: str | None
    price: int
    currency: str
    interval: Literal["month", "year"]
    features: list[str]
```

```python
class BillingPlanListResponse(BaseModel):
    items: list[BillingPlanResponse]
```

---

# 59. Current Subscription

```http
GET /billing/subscription
```

### Response

```python
class SubscriptionResponse(BaseModel):
    id: str | None
    plan_id: str | None
    status: str
    current_period_start: datetime | None
    current_period_end: datetime | None
    cancel_at_period_end: bool
```

---

# 60. Create Checkout Session

```http
POST /billing/checkout-sessions
```

### Request

```python
class CheckoutSessionRequest(BaseModel):
    plan_id: str
```

### Response

```python
class CheckoutSessionResponse(BaseModel):
    session_id: str
    checkout_url: str
```

The frontend redirects the user to the Stripe checkout URL.

---

# 61. Billing Portal

```http
POST /billing/portal-sessions
```

### Response

```python
class BillingPortalResponse(BaseModel):
    portal_url: str
```

---

# 62. Stripe Webhook

This endpoint is called by Stripe rather than the frontend.

```http
POST /webhooks/stripe
```

### Request

Raw Stripe webhook payload.

```text
Content-Type: application/json
```

### Response

```json
{
  "received": true
}
```

This endpoint must verify the Stripe webhook signature before processing the event.

---

# 63. Global Search

A global search endpoint can simplify the frontend search experience.

```http
GET /search?q=john
```

### Query parameters

```text
q
types=patients,documents,notes
page
page_size
```

### Response

```python
class SearchResult(BaseModel):
    type: str
    id: UUID
    title: str
    subtitle: str | None
    url: str | None
```

```python
class SearchResponse(BaseModel):
    items: list[SearchResult]
    pagination: Pagination
```

Example:

```json
{
  "items": [
    {
      "type": "patient",
      "id": "uuid",
      "title": "John Smith",
      "subtitle": "Male · 42 years",
      "url": "/patients/uuid"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 1,
    "total_pages": 1
  }
}
```

---

# 64. Health Checks

For infrastructure/load balancers:

```http
GET /health/live
```

Response:

```json
{
  "status": "ok"
}
```

Readiness:

```http
GET /health/ready
```

Response:

```json
{
  "status": "ok",
  "database": "ok",
  "storage": "ok"
}
```

The readiness endpoint should verify dependencies such as PostgreSQL and S3 where appropriate.

---

# 65. Complete Endpoint Summary

## Authentication

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/auth/register` | Register doctor |
| POST | `/auth/login` | Login |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Logout |
| GET | `/auth/me` | Current user |
| POST | `/auth/verify-email` | Verify email |
| POST | `/auth/resend-verification` | Resend verification |
| POST | `/auth/forgot-password` | Request password reset |
| POST | `/auth/reset-password` | Reset password |
| POST | `/auth/change-password` | Change password |

## Profile

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/profile` | Get doctor profile |
| PATCH | `/profile` | Update doctor profile |

## Patients

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/patients` | List/search patients |
| POST | `/patients` | Create patient |
| GET | `/patients/{id}` | Get patient |
| PATCH | `/patients/{id}` | Update patient |
| DELETE | `/patients/{id}` | Delete patient |
| GET | `/patients/{id}/encounters` | Patient encounters |
| GET | `/patients/{id}/documents` | Patient documents |
| GET | `/patients/{id}/diagnoses` | Patient diagnoses |
| GET | `/patients/{id}/medications` | Patient medications |
| GET | `/patients/{id}/test-orders` | Patient test orders |
| GET | `/patients/{id}/test-results` | Patient test results |

## Encounters

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/encounters` | Create encounter |
| GET | `/encounters/{id}` | Get encounter |
| PATCH | `/encounters/{id}` | Update encounter |
| DELETE | `/encounters/{id}` | Delete encounter |

## Notes

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/encounters/{id}/notes` | List encounter notes |
| POST | `/encounters/{id}/notes` | Create note |
| GET | `/notes/{id}` | Get note |
| PATCH | `/notes/{id}` | Update note |
| DELETE | `/notes/{id}` | Delete note |

## Transcriptions

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/transcriptions` | Create transcription |
| GET | `/transcriptions/{id}` | Get transcription |

## AI Assistance

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/ai/assistance` | Generate AI assistance |
| GET | `/ai/assistance/{id}` | Retrieve AI assistance |

## Documents

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/uploads` | Create upload |
| POST | `/uploads/{id}/complete` | Complete upload |
| POST | `/documents` | Create document |
| GET | `/documents/{id}` | Get document |
| DELETE | `/documents/{id}` | Delete document |

## Clinical Reference Data

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/diagnoses` | Search diagnoses |
| GET | `/medicines` | Search medicines |
| GET | `/tests` | Search tests |

## Tests

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/test-orders` | Create test order |
| GET | `/test-orders/{id}` | Get test order |
| GET | `/patients/{id}/test-orders` | Patient test orders |
| GET | `/test-results/{id}` | Get result |
| GET | `/patients/{id}/test-results` | Patient results |

## Treatment Templates

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/treatment-templates` | List templates |
| POST | `/treatment-templates` | Create template |
| GET | `/treatment-templates/{id}` | Get template |
| PATCH | `/treatment-templates/{id}` | Update template |
| DELETE | `/treatment-templates/{id}` | Delete template |

## Notifications

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/notifications` | List notifications |
| GET | `/notifications/{id}` | Get notification |
| PATCH | `/notifications/{id}` | Mark notification read/unread |

## Dashboard

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/statistics/overview` | Dashboard statistics |
| GET | `/search` | Global search |

## Billing

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/billing/plans` | Available plans |
| GET | `/billing/subscription` | Current subscription |
| POST | `/billing/checkout-sessions` | Create Stripe checkout |
| POST | `/billing/portal-sessions` | Stripe customer portal |
| POST | `/webhooks/stripe` | Stripe webhook |

## Infrastructure

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health/live` | Liveness |
| GET | `/health/ready` | Readiness |

---

# 66. Suggested FastAPI Structure

The API should be organized by domain rather than putting everything into one router.

```text
app/
├── api/
│   └── v1/
│       ├── router.py
│       │
│       ├── auth.py
│       ├── profile.py
│       ├── patients.py
│       ├── encounters.py
│       ├── notes.py
│       ├── transcriptions.py
│       ├── ai.py
│       ├── uploads.py
│       ├── documents.py
│       ├── diagnoses.py
│       ├── medicines.py
│       ├── tests.py
│       ├── test_orders.py
│       ├── test_results.py
│       ├── treatment_templates.py
│       ├── notifications.py
│       ├── statistics.py
│       ├── billing.py
│       ├── search.py
│       └── health.py
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
│   ├── billing/
│   └── notifications/
│
├── application/
│   ├── services/
│   └── use_cases/
│
├── infrastructure/
│   ├── database/
│   ├── storage/
│   ├── email/
│   └── payments/
│
└── schemas/
    ├── auth.py
    ├── patients.py
    ├── encounters.py
    ├── notes.py
    ├── documents.py
    └── ...
```

---

# 67. Recommended Schema Naming Convention

Keep request and response models explicitly separated.

For example:

```python
PatientCreateRequest
PatientUpdateRequest
PatientResponse
PatientSummary
PatientListResponse
```

Avoid one giant schema such as:

```python
PatientSchema
```

being used for every operation.

This makes API contracts clearer and prevents accidental exposure of fields.

For example:

```python
class PatientCreateRequest(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date | None = None
```

while the response can contain server-generated fields:

```python
class PatientResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    date_of_birth: date | None
    created_at: datetime
    updated_at: datetime
```

---

# 68. HTTP Status Codes

Use conventional HTTP status codes.

| Status | Meaning |
|---|---|
| `200` | Successful request |
| `201` | Resource created |
| `202` | Accepted for asynchronous processing |
| `204` | Successful request with no response body |
| `400` | Invalid request |
| `401` | Authentication required/failed |
| `403` | Authenticated but not authorized |
| `404` | Resource not found |
| `409` | Resource conflict |
| `422` | Validation error |
| `429` | Rate limit exceeded |
| `500` | Internal server error |
| `503` | Service unavailable |

For example:

```http
POST /patients
```

should return:

```http
201 Created
```

while:

```http
GET /patients/123
```

returns:

```http
200 OK
```

and a missing patient:

```http
404 Not Found
```

---

# 69. Authentication Header

Authenticated requests should use:

```http
Authorization: Bearer <access_token>
```

Example:

```http
GET /api/v1/patients
Authorization: Bearer eyJ...
```

---

# 70. Core Clavis Domain Model

The most important relationship in the application is:

```text
Doctor
   │
   ├── Patients
   │      │
   │      ├── Encounters
   │      │      │
   │      │      ├── Transcriptions
   │      │      ├── Clinical Notes
   │      │      ├── Documents
   │      │      ├── Diagnoses
   │      │      ├── Test Orders
   │      │      └── Treatment
   │      │
   │      ├── Medications
   │      ├── Diagnoses
   │      ├── Test Results
   │      └── Documents
   │
   └── Treatment Templates
```

This should be reflected in the database and service layer.

---

# 71. Clinical Workflow

The frontend's primary workflow should look approximately like this:

```text
Doctor Login
     │
     ▼
Dashboard
     │
     ▼
Select/Create Patient
     │
     ▼
Create Encounter
     │
     ├───────────────┐
     ▼               ▼
Start Recording   Upload Document
     │               │
     ▼               ▼
Transcription     Document
     │
     ▼
AI Assistance
     │
     ▼
Doctor Reviews
     │
     ├───────────────┬───────────────┐
     ▼               ▼               ▼
Clinical Note     Diagnosis       Treatment
     │
     ├───────────────┐
     ▼               ▼
Test Order       Prescription/
                 Medication
     │
     ▼
Complete Encounter
```

The critical principle is:

> **AI generates drafts and recommendations; the doctor remains the final author of the clinical record.**

---

# 72. Implementation Order

Do not implement all endpoints simultaneously.

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
/profile
```

## Phase 2 — Patients

```text
/patients
/patients/{id}
```

## Phase 3 — Encounters & Notes

```text
/encounters
/encounters/{id}
/encounters/{id}/notes
/notes/{id}
```

## Phase 4 — Documents & Transcriptions

```text
/uploads
/documents
/transcriptions
```

## Phase 5 — AI

```text
/ai/assistance
```

## Phase 6 — Clinical Resources

```text
/diagnoses
/medicines
/tests
/test-orders
/test-results
/treatment-templates
```

## Phase 7 — Dashboard

```text
/notifications
/statistics/overview
/search
```

## Phase 8 — Billing

```text
/billing/plans
/billing/subscription
/billing/checkout-sessions
/billing/portal-sessions
/webhooks/stripe
```

---

# 73. MVP Backend Checklist

### Authentication

- [ ] Registration
- [ ] Login
- [ ] JWT access tokens
- [ ] Refresh tokens
- [ ] Logout
- [ ] Email verification
- [ ] Password reset
- [ ] Profile

### Patients

- [ ] Create patient
- [ ] List/search patients
- [ ] Retrieve patient
- [ ] Update patient
- [ ] Soft delete patient

### Encounters

- [ ] Create encounter
- [ ] Retrieve encounter
- [ ] Update encounter
- [ ] Delete/archive encounter

### Notes

- [ ] Create note
- [ ] Retrieve note
- [ ] Update note
- [ ] Delete/archive note
- [ ] Recycle bin

### Audio / AI

- [ ] Create transcription
- [ ] Retrieve transcription
- [ ] AI assistance
- [ ] AI-generated draft
- [ ] Doctor approval workflow

### Documents

- [ ] S3 presigned upload
- [ ] Upload completion
- [ ] Document metadata
- [ ] Presigned download
- [ ] Document deletion

### Clinical data

- [ ] Diagnosis search
- [ ] Medicine search
- [ ] Test search
- [ ] Test orders
- [ ] Test results
- [ ] Treatment templates

### Dashboard

- [ ] Notifications
- [ ] Statistics
- [ ] Global search

### Billing

- [ ] Plans
- [ ] Subscription
- [ ] Stripe checkout
- [ ] Stripe portal
- [ ] Stripe webhook

### Infrastructure

- [ ] Liveness endpoint
- [ ] Readiness endpoint
- [ ] Rate limiting
- [ ] Structured logging
- [ ] API documentation
- [ ] CORS configuration
- [ ] Authentication/authorization middleware

---

# 74. Final Architecture

The Clavis backend should ultimately follow this separation:

```text
                    ┌───────────────────┐
                    │   Clavis Frontend │
                    │      Nuxt/Vue     │
                    └─────────┬─────────┘
                              │
                         HTTPS / JSON
                              │
                              ▼
                    ┌───────────────────┐
                    │    FastAPI API    │
                    │      /api/v1      │
                    └─────────┬─────────┘
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
        PostgreSQL           S3           External APIs
             │                │                │
             │                │          ┌─────┴─────┐
             │                │          │   Stripe  │
             │                │          │ AI/Email  │
             │                │          └───────────┘
             │                │
             └────────────────┘
```

The backend should therefore expose a **stable REST API contract**, while the internal implementation can evolve independently.

The frontend should depend only on the `/api/v1` contract and should not need to know whether Clavis internally uses SQLAlchemy, PostgreSQL, S3, Redis, Celery, or another implementation.

---

# 75. Important Existing Clavis Backend Compatibility

The current Clavis backend already has several pieces that should be evolved rather than rebuilt:

```text
/auth/signup
/auth/login
/auth/refresh
/auth/me
/auth/verify-email

/notes
/notes/{note_id}

/S3 presigned URLs
/refresh-token storage
/soft deletion
```

These should be migrated toward the standardized API contract above rather than creating a second, unrelated authentication or note system.

For example:

```text
Current:
POST /auth/signup

Target:
POST /api/v1/auth/register
```

and:

```text
Current:
GET /notes/

Target:
GET /api/v1/encounters/{encounter_id}/notes
GET /api/v1/notes/{note_id}
```

The existing implementation can remain underneath the new API layer while the application is progressively refactored.

---

# 76. API Contract Principle

The most important rule for the Clavis backend is:

```text
Frontend
   ↓
Stable API Contract
   ↓
Application / Use Cases
   ↓
Domain Logic
   ↓
Infrastructure
   ↓
PostgreSQL / S3 / Redis / External Services
```

Do not allow frontend requirements to leak directly into database models.

Instead:

```text
Request Schema
      ↓
API Router
      ↓
Application Service
      ↓
Domain
      ↓
Repository
      ↓
Database
```

and:

```text
Database
      ↓
Repository
      ↓
Domain/Application
      ↓
Response Schema
      ↓
Frontend
```

This will make the Clavis backend substantially easier to evolve as the application grows from an individual-doctor MVP into a multi-doctor platform.