# Import data from Excel
```bash
{
 python -m swiftatlas.import_data swiftatlas/Interns_2025_SWIFT_CODES.xlsx
}
```
# Run the FastAPI Server
```bash
uvicorn swiftatlas.main:app --host 0.0.0.0 --port 8080
```