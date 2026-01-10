from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables FIRST before any other imports
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import warnings

# Import services AFTER loading .env
from services.auth_service import AuthService, get_current_user
from services.google_service import GoogleService
from services.scraper_service import ScraperService
from services.llm_service import LLMService
from services.run_service import RunService
from services.credit_service import CreditService

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize services
auth_service = AuthService(db)
google_service = GoogleService(db)
scraper_service = ScraperService()
llm_service = LLMService()
run_service = RunService(db, google_service, scraper_service, llm_service)
credit_service = CreditService(db)


# ============= MODELS =============

class UserSignup(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class ProjectCreate(BaseModel):
    name: str
    spreadsheet_id: str
    sheet_name: str
    header_row: int = 1
    row_range: Optional[str] = None
    start_row: Optional[int] = 2
    end_row: Optional[int] = 100

class FieldMappingCreate(BaseModel):
    website_col: str
    first_name_col: str
    company_col: str
    email_col: Optional[str] = None
    title_col: Optional[str] = None
    description_col: Optional[str] = None
    output_mode: str = "same_sheet"  # same_sheet or new_sheet
    output_sheet_name: Optional[str] = None

class PromptConfigCreate(BaseModel):
    summary_preset: str = "logistics"  # logistics, industrial, custom
    summary_prompt: Optional[str] = None
    icebreaker_prompt: str
    model: str = "gpt-4o"

class RunCreate(BaseModel):
    project_id: str
    mode: str = "preview"  # preview or full
    max_rows: Optional[int] = None

class RunResponse(BaseModel):
    id: str
    project_id: str
    status: str
    total_rows: int
    processed_rows: int
    success_rows: int
    failed_rows: int
    created_at: str

class ApiKeyCreate(BaseModel):
    provider: str = "openai"
    key: str
    nickname: Optional[str] = None


# ============= AUTH ROUTES =============

@api_router.post("/auth/signup", response_model=TokenResponse)
async def signup(user_data: UserSignup):
    try:
        result = await auth_service.signup(user_data.email, user_data.password, user_data.name)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    try:
        result = await auth_service.login(user_data.email, user_data.password)
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@api_router.get("/auth/me")
async def get_me(current_user: Dict = Depends(get_current_user)):
    return current_user


# ============= GOOGLE OAUTH ROUTES =============

@api_router.get("/oauth/google/start")
async def google_oauth_start(user_id: str):
    try:
        auth_url = await google_service.start_oauth(user_id)
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/oauth/google/callback")
async def google_oauth_callback(code: str, state: str):
    try:
        user_id = await google_service.handle_callback(code, state)
        frontend_url = os.environ.get('REACT_APP_BACKEND_URL', '').replace('/api', '')
        return RedirectResponse(url=f"{frontend_url}/dashboard")
    except Exception as e:
        logging.error(f"OAuth callback error: {str(e)}")
        frontend_url = os.environ.get('REACT_APP_BACKEND_URL', '').replace('/api', '')
        return RedirectResponse(url=f"{frontend_url}/error?message={str(e)}")

@api_router.get("/oauth/google/status")
async def google_oauth_status(current_user: Dict = Depends(get_current_user)):
    user_id = current_user['id']
    is_connected = await google_service.is_connected(user_id)
    return {"connected": is_connected}

@api_router.delete("/oauth/google/disconnect")
async def google_oauth_disconnect(current_user: Dict = Depends(get_current_user)):
    user_id = current_user['id']
    await google_service.disconnect(user_id)
    return {"success": True}


# ============= SHEETS ROUTES =============

@api_router.get("/sheets/spreadsheets")
async def list_spreadsheets(current_user: Dict = Depends(get_current_user)):
    try:
        user_id = current_user['id']
        spreadsheets = await google_service.list_spreadsheets(user_id)
        return {"spreadsheets": spreadsheets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/sheets/{spreadsheet_id}/tabs")
async def get_sheet_tabs(spreadsheet_id: str, current_user: Dict = Depends(get_current_user)):
    try:
        user_id = current_user['id']
        tabs = await google_service.get_sheet_tabs(user_id, spreadsheet_id)
        return {"tabs": tabs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/sheets/{spreadsheet_id}/values")
async def get_sheet_values(
    spreadsheet_id: str,
    sheet_name: str,
    range_notation: str = "A1:Z1000",
    current_user: Dict = Depends(get_current_user)
):
    try:
        user_id = current_user['id']
        values = await google_service.get_sheet_values(user_id, spreadsheet_id, sheet_name, range_notation)
        return {"values": values}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= PROJECT ROUTES =============

@api_router.post("/projects")
async def create_project(
    project: ProjectCreate,
    field_mapping: FieldMappingCreate,
    prompt_config: PromptConfigCreate,
    current_user: Dict = Depends(get_current_user)
):
    try:
        user_id = current_user['id']
        
        # Create project
        project_id = str(uuid.uuid4())
        project_doc = {
            "id": project_id,
            "user_id": user_id,
            "name": project.name,
            "spreadsheet_id": project.spreadsheet_id,
            "sheet_name": project.sheet_name,
            "header_row": project.header_row,
            "row_range": project.row_range,
            "start_row": project.start_row,
            "end_row": project.end_row,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.projects.insert_one(project_doc)
        
        # Create field mapping
        mapping_doc = {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            **field_mapping.model_dump(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.field_mappings.insert_one(mapping_doc)
        
        # Create prompt config
        config_doc = {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            **prompt_config.model_dump(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.prompt_configs.insert_one(config_doc)
        
        return {"project_id": project_id, "success": True}
    except Exception as e:
        logging.error(f"Error creating project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/projects")
async def list_projects(current_user: Dict = Depends(get_current_user)):
    user_id = current_user['id']
    projects = await db.projects.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"projects": projects}

@api_router.get("/projects/{project_id}")
async def get_project(project_id: str, current_user: Dict = Depends(get_current_user)):
    user_id = current_user['id']
    project = await db.projects.find_one({"id": project_id, "user_id": user_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get related data
    field_mapping = await db.field_mappings.find_one({"project_id": project_id}, {"_id": 0})
    prompt_config = await db.prompt_configs.find_one({"project_id": project_id}, {"_id": 0})
    
    return {
        "project": project,
        "field_mapping": field_mapping,
        "prompt_config": prompt_config
    }


# ============= RUN ROUTES =============

@api_router.post("/runs")
async def create_run(
    run_data: RunCreate,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    try:
        user_id = current_user['id']
        run_id = await run_service.create_run(user_id, run_data.project_id, run_data.mode, run_data.max_rows)
        
        # Start background processing
        background_tasks.add_task(run_service.process_run, run_id)
        
        return {"run_id": run_id, "success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error creating run: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/runs/{run_id}")
async def get_run(run_id: str, current_user: Dict = Depends(get_current_user)):
    run = await db.runs.find_one({"id": run_id}, {"_id": 0})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Get run items
    items = await db.run_items.find({"run_id": run_id}, {"_id": 0}).to_list(1000)
    
    return {"run": run, "items": items}

@api_router.get("/runs")
async def list_runs(
    project_id: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    user_id = current_user['id']
    query = {"user_id": user_id}
    if project_id:
        query["project_id"] = project_id
    
    runs = await db.runs.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"runs": runs}

@api_router.post("/runs/{run_id}/retry")
async def retry_failed(
    run_id: str,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    try:
        await run_service.retry_failed(run_id)
        background_tasks.add_task(run_service.process_run, run_id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= CREDIT ROUTES =============

@api_router.get("/credits/balance")
async def get_credit_balance(current_user: Dict = Depends(get_current_user)):
    user_id = current_user['id']
    balance = await credit_service.get_balance(user_id)
    return {"balance": balance}

@api_router.get("/credits/history")
async def get_credit_history(current_user: Dict = Depends(get_current_user)):
    user_id = current_user['id']
    history = await db.credit_ledger.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"history": history}


# ============= API KEY ROUTES =============

@api_router.post("/settings/api-keys")
async def save_api_key(
    key_data: ApiKeyCreate,
    current_user: Dict = Depends(get_current_user)
):
    try:
        user_id = current_user['id']
        
        # Delete existing key for this provider
        await db.api_keys.delete_many({"user_id": user_id, "provider": key_data.provider})
        
        # Save new key (encrypted in production)
        key_doc = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "provider": key_data.provider,
            "key_encrypted": key_data.key,  # TODO: Encrypt in production
            "nickname": key_data.nickname,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.api_keys.insert_one(key_doc)
        
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/settings/api-keys")
async def get_api_keys(current_user: Dict = Depends(get_current_user)):
    user_id = current_user['id']
    keys = await db.api_keys.find({"user_id": user_id}, {"_id": 0, "key_encrypted": 0}).to_list(100)
    return {"keys": keys}

@api_router.delete("/settings/api-keys/{key_id}")
async def delete_api_key(key_id: str, current_user: Dict = Depends(get_current_user)):
    user_id = current_user['id']
    result = await db.api_keys.delete_one({"id": key_id, "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"success": True}


# ============= HEALTH CHECK =============

@api_router.get("/")
async def root():
    return {"message": "Sheet Personalizer API", "version": "1.0.0"}

@api_router.get("/health")
async def health():
    return {"status": "healthy"}


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
