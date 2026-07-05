import logging
from logging.handlers import RotatingFileHandler
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from exceptions import DatabaseError
from routes import pipeline

load_dotenv()

LOG_DIR = os.getenv("LOG_DIR", "")
# Create custom logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create handlers and formatter
c_handler = logging.StreamHandler()
# max 5 mb file
f_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "app.log"), maxBytes=5242880, encoding="utf-8"
)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s\n")
c_handler.setFormatter(formatter)
f_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(c_handler)
logger.addHandler(f_handler)

# Entry point
app = FastAPI()
# Register routes
app.include_router(pipeline, prefix="/pipeline", tags=["Pipeline"])


# Exception handlers
@app.exception_handler(DatabaseError)
def database_error_handler(request: Request, exc: DatabaseError):
    logger.error(f"Database error encountered: {exc}")
    return JSONResponse(
        content="Internal Server Error",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
