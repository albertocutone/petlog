# petlog/main.py
import uvicorn
from api import app

def main():
    """Main function to run the FastAPI server."""
    print("Starting PetLog FastAPI server...")
    print("API Documentation available at: http://localhost:8000/docs")
    print("Alternative docs at: http://localhost:8000/redoc")
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
