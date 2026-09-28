# Healthcare Backend API

## Project Overview

A secure REST API for a healthcare application. Authenticated users can register and
log in with JWT, manage their own **patient** records, manage **doctor** records, and
assign doctors to patients (many-to-many through a mapping model).

Key rules:

* Passwords are hashed with Django's password hashers and never returned.
* A user can only see/modify **patients they created**; other users' patients respond
  with `404` so their existence is not exposed.
* A patient can have many doctors and a doctor many patients; duplicate pairs are rejected.
* All errors are clean JSON (`{"error": "..."}` or DRF field errors) with no stack traces.

## Tech Stack

* Python 3.10+
* Django
* Django REST Framework
* PostgreSQL (via `psycopg2`)
* JWT authentication (`djangorestframework-simplejwt`)
* `python-dotenv` for environment variables

## Project Structure

```text
healthcare-backend/
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── config/      # settings, root urls, wsgi/asgi
├── core/        # shared exception handler, validators, JSON 404/500 handlers, test helpers
├── accounts/    # custom User model (email login), register API, JWT login
├── patients/    # Patient model + CRUD (owner-scoped)
├── doctors/     # Doctor model + CRUD
└── mappings/    # PatientDoctorMapping model + assignment APIs
```

## Installation

```bash
git clone https://github.com/JinkalaPushparaju/healthcare-backend
cd healthcare-backend

python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env        # Windows: copy .env.example .env  (then edit values)

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The API is served at `http://127.0.0.1:8000/` and the admin at `/admin/`.

## PostgreSQL Setup

1. Install PostgreSQL and start the service.
2. Create the database:

   ```bash
   psql -U postgres -c "CREATE DATABASE healthcare_db;"
   ```

3. Put your credentials in `.env` (never commit this file):

   ```env
   SECRET_KEY=change-me-to-a-long-random-string
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1

   DB_NAME=healthcare_db
   DB_USER=postgres
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=5432
   ```

Generate a secret key with:
`python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"`

The database user needs permission to create databases so Django can create
`test_healthcare_db` when running tests.

## Authentication

1. Register via `POST /api/auth/register/`.
2. Log in via `POST /api/auth/login/` to receive `access` and `refresh` tokens.
3. Send the access token on every protected request:

```http
Authorization: Bearer <access_token>
```

Missing or invalid tokens return `401 Unauthorized`. The access token lasts 60 minutes;
get a new one with `POST /api/auth/token/refresh/` and body `{"refresh": "<refresh_token>"}`.

## API Documentation

Base URL: `http://127.0.0.1:8000`. "Auth" = requires `Authorization: Bearer <access_token>`.

### Auth

#### Register — `POST /api/auth/register/` (no auth)

```json
{ "name": "John Doe", "email": "john@example.com", "password": "StrongPassword123" }
```

`201 Created`

```json
{
  "message": "User registered successfully",
  "user": { "id": 1, "name": "John Doe", "email": "john@example.com" }
}
```

Errors: `400` e.g. `{"email": ["A user with this email already exists."]}`.

#### Login — `POST /api/auth/login/` (no auth)

```json
{ "email": "john@example.com", "password": "StrongPassword123" }
```

`200 OK`

```json
{ "access": "JWT_ACCESS_TOKEN", "refresh": "JWT_REFRESH_TOKEN" }
```

Errors: `401` `{"error": "No active account found with the given credentials"}`.

### Patients (Auth, owner-scoped)

| Method | URL | Description | Success |
|--------|-----|-------------|---------|
| POST | `/api/patients/` | Create patient (`created_by` set automatically) | `201` |
| GET | `/api/patients/` | List own patients | `200` |
| GET | `/api/patients/<id>/` | Get own patient | `200` |
| PUT | `/api/patients/<id>/` | Update own patient | `200` |
| DELETE | `/api/patients/<id>/` | Delete own patient | `204` |

Request body (POST / PUT):

```json
{
  "name": "John Doe",
  "age": 35,
  "gender": "Male",
  "phone": "9876543210",
  "address": "Hyderabad",
  "medical_history": "Diabetes"
}
```

Example response (`201` / `200`):

```json
{
  "id": 1, "name": "John Doe", "age": 35, "gender": "Male",
  "phone": "9876543210", "address": "Hyderabad", "medical_history": "Diabetes",
  "created_by": 1,
  "created_at": "2026-09-28T10:30:00Z", "updated_at": "2026-09-28T10:30:00Z"
}
```

Validation: `age` 0–150, `gender` in `Male|Female|Other`, `phone` 7–15 digits with optional `+`.
Other users' patients / unknown IDs → `404` `{"error": "No Patient matches the given query."}`.

### Doctors (Auth)

| Method | URL | Description | Success |
|--------|-----|-------------|---------|
| POST | `/api/doctors/` | Create doctor | `201` |
| GET | `/api/doctors/` | List all doctors | `200` |
| GET | `/api/doctors/<id>/` | Get doctor | `200` |
| PUT | `/api/doctors/<id>/` | Update doctor | `200` |
| DELETE | `/api/doctors/<id>/` | Delete doctor | `204` |

Request body:

```json
{
  "name": "Dr. Smith",
  "specialization": "Cardiologist",
  "phone": "9876543210",
  "email": "doctor@example.com",
  "address": "Hyderabad"
}
```

Doctor `email` is unique. Unknown ID → `404`.

### Mappings (Auth)

#### Assign doctor — `POST /api/mappings/`

```json
{ "patient": 1, "doctor": 2 }
```

`201 Created`

```json
{
  "message": "Doctor assigned to patient successfully",
  "mapping": { "id": 1, "patient": 1, "doctor": 2 }
}
```

Errors: `404 {"error": "Patient not found"}` (missing or not yours),
`404 {"error": "Doctor not found"}`, `400` for duplicates or missing fields.

#### List mappings — `GET /api/mappings/` → `200`

Only mappings for patients you own.

```json
[
  {
    "id": 1,
    "patient": { "id": 1, "name": "John Doe" },
    "doctor": { "id": 2, "name": "Dr. Smith", "specialization": "Cardiologist" },
    "assigned_at": "2026-09-28T10:30:00Z"
  }
]
```

#### Doctors of a patient — `GET /api/mappings/<patient_id>/` → `200`

```json
[
  { "id": 2, "name": "Dr. Smith", "specialization": "Cardiologist" },
  { "id": 5, "name": "Dr. Kumar", "specialization": "Neurologist" }
]
```

`404 {"error": "Patient not found"}` if the patient does not exist or is not yours.

#### Remove mapping — `DELETE /api/mappings/<id>/` → `204 No Content`

`<id>` is the **mapping** id. `404 {"error": "Mapping not found"}` if it does not exist or
belongs to another user's patient.

### Status codes

`200` OK · `201` Created · `204` No Content · `400` Validation error · `401` Missing/invalid
token · `403` Forbidden · `404` Not found · `500` Unexpected error (generic message only).

## Testing

```bash
python manage.py test
```

40 tests cover registration, login, invalid tokens, patients, doctors and mappings
(including ownership isolation and unauthenticated access). Django creates and destroys a
temporary `test_<DB_NAME>` PostgreSQL database automatically.

## Django Admin

`User`, `Patient`, `Doctor` and `PatientDoctorMapping` are registered at `/admin/` with
`list_display`, `search_fields` and `list_filter`.
