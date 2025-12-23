# Bond APIs

CRUD APIs for the Bond Platform, built with FastAPI and MongoDB (Motor).

## Features

*   **Tenants**: Manage multi-tenancy configurations.
*   **Projects**: Organize resources under specific domains.
*   **Workflows**: Define step-by-step processes.
*   **Data Models**: Define schemas and fields.
*   **Relationships**: Map connections between data models.
*   **Policies**: Manage access and data handling rules.

## Tech Stack

*   **Framework**: FastAPI
*   **Database**: MongoDB (Async via Motor)
*   **Validation**: Pydantic v2
*   **Server**: Uvicorn

## Setup

### 1. Prerequisites
*   Python 3.11+
*   MongoDB instance running locally or in the cloud.

### 2. Installation

1.  Clone the repository.
2.  Create a virtual environment:
    ```bash
    python -m venv venv
    ```
3.  Activate the virtual environment:
    *   Windows: `venv\Scripts\activate`
    *   Mac/Linux: `source venv/bin/activate`
4.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### 3. Configuration

Create a `.env` file in the root directory:

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=bond_db
```

### 4. Running the Application

```bash
uvicorn src.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## Documentation

Interactive API documentation is available at:
*   Swagger UI: `http://127.0.0.1:8000/docs`
*   ReDoc: `http://127.0.0.1:8000/redoc`
