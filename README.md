# SwiftAtlas

SwiftAtlas is an application designed to manage and provide access to SWIFT/BIC (Bank Identifier Code) data. It parses data from a spreadsheet, stores it in a MongoDB database, and exposes it through a RESTful API.

## Project Goal

The primary goal of SwiftAtlas is to make SWIFT code information easily accessible for applications by:

1.  **Parsing Data:** Extracting and processing SWIFT code data from a source file, identifying headquarters vs. branches, and ensuring correct formatting (uppercase country codes/names).
2.  **Storing Data:** Persisting the parsed data in MongoDB for fast, low-latency querying. The structure allows efficient retrieval by individual SWIFT code or by country (ISO-2 code).
3.  **Exposing a REST API:** Providing standardized endpoints for accessing the SWIFT code data.

## Prerequisites

-   Visual Studio Code (VS Code) with the Dev Containers extension.
-   Docker Desktop (or Docker Engine).

## Getting Started

### 1. Open in Dev Container

**Option 1: Using VS Code Dev Container**

-   Open the project folder (`swiftatlas`) in Visual Studio Code.
-   If prompted, click **"Reopen in Container"**. If not, open the Command Palette (`Cmd+Shift+P` or `Ctrl+Shift+P`) and select **"Dev Containers: Rebuild and Reopen in Container"**.
-   This setup uses the `docker-compose.devcontainer.yml` file to build and run the necessary services (FastAPI app, MongoDB) in isolated containers. Your local code is mounted into the container, allowing seamless development within the dev environment.

### 2. Import Initial Data

-   Once the dev container is running, open a new terminal within VS Code (Terminal > New Terminal).
-   Run the import script:
    ```bash
    python -m swiftatlas.import_data --file-path swiftatlas/data/Interns_2025_SWIFT_CODES.xlsx    
    ```
    This command parses the Excel file and populates the MongoDB database.

### 3. Run the FastAPI Application

-   Start the Uvicorn server:
    ```bash
    uvicorn swiftatlas.main:app --host 0.0.0.0 --port 8080
    ```
-   The API will be accessible at `http://localhost:8080`.
-   Interactive API documentation (Swagger UI) is available at `http://localhost:8080/docs`.
-   Alternative API documentation (ReDoc) is available at `http://localhost:8080/redoc`.

### 4. Running Tests

-   To run the automated tests, execute the following command in the VS Code terminal:
    ```bash
    pytest swiftatlas
    ```

### Test Structure

Tests are located in the same directory as the functionality they cover, using the `_test.py` suffix.
Unit tests cover components like `clients`, `schemas`, and `repositories`, while integration tests focus on the API `routers`.

## API Endpoints

The following endpoints are available under the `/v1/swift-codes` prefix:

*   **`GET /{swift_code}`**: Retrieves details for a specific SWIFT code. If the code represents a headquarters (`XXX` suffix), it also returns associated branch codes.
*   **`GET /country/{country_iso2_code}`**: Retrieves all SWIFT codes (headquarters and branches) associated with a specific country.
*   **`POST /`**: Adds a new SWIFT code entry.
*   **`DELETE /{swift_code}`**: Deletes a specific SWIFT code entry.


## Architecture

-   **Framework:** FastAPI (Python)
-   **Database:** MongoDB
-   **Development Environment:** Docker & VS Code Dev Containers

## Additional Notes

-   Ensure Docker is running before attempting to open the project in the dev container.
-   If you encounter issues, check the Docker container logs and the terminal output within VS Code. Restarting the dev container (Rebuild and Reopen) can often resolve transient problems.