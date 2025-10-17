from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
from api.api import api_router  # Correct absolute import from project root
import time

# Configure logging with explicit handlers
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
    force=True  # Force reconfiguration to override uvicorn's logging
)

app = FastAPI(title="Stir Recipe API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware to log all requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"🌐 REQUEST: {request.method} {request.url.path}")
    logging.info(f"🌐 REQUEST: {request.method} {request.url.path}")

    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    print(f"✅ RESPONSE: Status {response.status_code} - Took {process_time:.2f}s")
    logging.info(f"✅ RESPONSE: Status {response.status_code} - Took {process_time:.2f}s")

    return response

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Stir Recipe API"}

@app.on_event("startup")
async def startup_event():
    logging.info("🚀 Application starting up - Logging is configured!")
    print("🔥 PRINT TEST: If you see this, print statements work!")
    logging.info("✅ LOGGING TEST: If you see this, logging works!")
