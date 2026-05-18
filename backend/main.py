from fastapi import FastAPI, Depends, HTTPException, Header, status, File, Form
from fastapi.datastructures import UploadFile
from datetime import datetime
from router import select_model
from ai_client import ask_ai, ask_ai_vision
from hermes_integration import hermes_integration
from multi_agent_coordinator import multi_agent_coordinator
from memory_manager import memory_manager
from dataclasses import asdict
from auth import router as auth_router
from auth import get_current_user, admin_required, trader_required
from system import router as system_router
from event_system.endpoints import router as event_router
from event_system.event_system_manager import event_system_manager
from pipeline.router import router as pipeline_router
from trading.router import router as trading_router

app = FastAPI()

# Include auth routes
app.include_router(auth_router, prefix="/auth")

# Include system routes
app.include_router(system_router, prefix="/system")

# Include event system routes
app.include_router(event_router, prefix="/event")

# Include pipeline routes
app.include_router(pipeline_router, prefix="/pipeline")

# Include trading routes
app.include_router(trading_router, prefix="/trading")

@app.get("/")
def root():
    return {
        "system": "ATSAWIN AI CORE",
        "status": "ONLINE",
        "time": str(datetime.now()),
        "services": {
            "hermes": "online",
            "postgres": "online",
            "redis": "online",
            "telegram": "online"
        },
        "features": {
            "autonomous_execution": "enabled",
            "hermes_integration": "enabled",
            "multi_agent": "enabled",
            "memory_system": "enabled",
            "authentication": "enabled",
            "system_resource_manager": "enabled",
            "event_system": "enabled",
            "autonomous_coding_pipeline": "enabled",
            "trading_ai": "enabled"
        },
    }

@app.get("/health")
def health():
    return {
        "health": "ok"
    }

@app.get("/models")
def models():
    return {
        "models": [
            "glm-4.5-air",
            "deepseek-chat-v3",
            "hunyuan",
            "owl-alpha"
        ]
    }


@app.get("/route/{task}")
def route_task(task: str):
    return select_model(task)

@app.get("/autonomous/{task}")
async def execute_autonomous_task(task: str):
    """Execute task autonomously using Hermes Agent"""
    result = await hermes_integration.execute_autonomous_task(task)
    return result

@app.get("/hermes/status")
async def get_hermes_status():
    """Get Hermes Agent integration status"""
    return await hermes_integration.get_system_status()

@app.get("/hermes/skills")
async def get_hermes_skills():
    """Get available Hermes skills"""
    return await hermes_integration.list_available_skills()

@app.post("/agent/task")
async def submit_agent_task(task: dict, current_user: dict = Depends(trader_required)):
    """Submit task to multi-agent system"""
    task_id = await multi_agent_coordinator.submit_task(
        task_description=task["description"],
        agent_type=task["agent_type"],
        priority=task.get("priority", 1)
    )
    return {"task_id": task_id}

@app.get("/agent/task/{task_id}")
async def get_agent_task_status(task_id: str, current_user: dict = Depends(get_current_user)):
    """Get status of a specific agent task"""
    return await multi_agent_coordinator.get_task_status(task_id)

@app.get("/agent/status")
async def get_agent_system_status(current_user: dict = Depends(get_current_user)):
    """Get multi-agent system status"""
    return await multi_agent_coordinator.get_system_status()

@app.post("/agent/coordinated-task")
async def execute_coordinated_task(task: dict, current_user: dict = Depends(trader_required)):
    """Execute a coordinated task with multiple sub-tasks"""
    return await multi_agent_coordinator.execute_coordinated_task(
        main_task=task["main_task"],
        sub_tasks=task["sub_tasks"]
    )

@app.on_event("startup")
async def startup_event():
    """Initialize memory manager and system manager on startup"""
    # Initialize memory manager
    await memory_manager.initialize()
    
    # Initialize event system
    await event_system_manager.initialize()
    
    # Initialize system manager components and start it
    from system import system_manager
    system_manager.register_component("multi_agent_coordinator", multi_agent_coordinator)
    system_manager.register_component("memory_manager", memory_manager)
    system_manager.register_component("hermes_integration", hermes_integration)
    system_manager.register_component("event_system_manager", event_system_manager)
    
    # Start system manager and event system (background tasks)
    import threading
    threading.Thread(target=system_manager.start, daemon=True).start()
    threading.Thread(target=event_system_manager.start, daemon=True).start()

@app.post("/memory/store")
async def store_memory(memory_data: dict, current_user: dict = Depends(get_current_user)):
    """Store a memory entry"""
    # Add user context to memory
    memory_data["user_id"] = current_user["id"]
    memory_data["username"] = current_user["username"]
    
    entry_id = await memory_manager.store_memory(
        key=memory_data["key"],
        value=memory_data["value"],
        memory_type=memory_data.get("memory_type", "general"),
        tags=memory_data.get("tags", []),
        metadata=memory_data.get("metadata", {}),
        ttl_seconds=memory_data.get("ttl_seconds")
    )
    return {"entry_id": entry_id}

@app.get("/memory/{key}")
async def get_memory(key: str, memory_type: str = None, current_user: dict = Depends(get_current_user)):
    """Retrieve a memory entry"""
    # Add user context to key
    user_key = f"user:{current_user['id']}:{key}"
    
    memory_entry = await memory_manager.retrieve_memory(user_key, memory_type)
    if memory_entry:
        return asdict(memory_entry)
    return {"error": "Memory not found"}

@app.get("/memory/search")
async def search_memories(q: str, memory_type: str = None, tags: str = None, limit: int = 10, current_user: dict = Depends(get_current_user)):
    """Search memories"""
    # Add user context to search
    tag_list = tags.split(",") if tags else None
    
    # Filter by user if not admin
    if current_user["role"] != "admin":
        if memory_type:
            memory_type = f"user:{current_user['id']}:{memory_type}"
        else:
            # Search only user's memories
            memories = await memory_manager.search_memories(
                query=f"user:{current_user['id']}:{q}",
                memory_type=memory_type,
                tags=tag_list,
                limit=limit
            )
            return [asdict(memory) for memory in memories]
    
    memories = await memory_manager.search_memories(
        query=q,
        memory_type=memory_type,
        tags=tag_list,
        limit=limit
    )
    return [asdict(memory) for memory in memories]

@app.get("/memory/stats")
async def get_memory_stats(current_user: dict = Depends(get_current_user)):
    """Get memory system statistics"""
    if current_user["role"] == "admin":
        return await memory_manager.get_memory_stats()
    else:
        # Get user-specific stats
        user_memories = await memory_manager.search_memories(
            query=f"user:{current_user['id']}",
            limit=1000
        )
        return {
            "total_entries": len(user_memories),
            "by_type": {},
            "recent_entries": len([m for m in user_memories if m.created_at]),
            "total_size_bytes": sum(len(str(m.value)) for m in user_memories),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/memory/cleanup")
async def cleanup_expired_memories(current_user: dict = Depends(admin_required)):
    """Clean up expired memories (admin only)"""
    deleted_count = await memory_manager.cleanup_expired_memories()
    return {"deleted_count": deleted_count}


@app.get("/ask/{prompt}")
async def ask(prompt: str, current_user: dict = Depends(get_current_user)):
    """Ask AI with user context"""
    result = select_model(prompt)
    loop = __import__("asyncio").get_event_loop()
    response = await loop.run_in_executor(None, ask_ai, result["model"], prompt)
    
    return {
        "task": prompt,
        "model": result["model"],
        "response": response,
        "user": current_user["username"]
    }


@app.get("/api/ask/{prompt}")
async def api_ask(prompt: str, x_api_key: str = Header(None)):
    """Ask AI via API key (for bot/service accounts)"""
    import os
    from concurrent.futures import ThreadPoolExecutor
    valid_key = os.getenv("BOT_API_KEY", "atsawin-bot-secret-2026")
    if x_api_key != valid_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    result = select_model(prompt)
    
    # Run blocking call in thread pool to avoid blocking event loop
    loop = __import__("asyncio").get_event_loop()
    response = await loop.run_in_executor(None, ask_ai, result["model"], prompt)
    
    return {
        "task": prompt,
        "model": result["model"],
        "response": response,
        "user": "bot"
    }


# ==================== File Analysis Endpoints ====================

import base64
import io

# Text file extensions we can read directly
TEXT_EXTENSIONS = {
    ".txt", ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css",
    ".json", ".yaml", ".yml", ".xml", ".csv", ".md", ".sh", ".bash",
    ".sql", ".env", ".cfg", ".ini", ".toml", ".conf", ".log",
    ".java", ".c", ".cpp", ".h", ".hpp", ".go", ".rs", ".rb",
    ".php", ".swift", ".kt", ".scala", ".r", ".m", ".pl",
    ".dockerfile", ".gitignore", ".makefile", ".vue", ".svelte",
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
IMAGE_MIMES = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp"}

PDF_EXTENSIONS = {".pdf"}
PDF_MIMES = {"application/pdf"}


def _is_text_file(filename: str) -> bool:
    """Check if file is a readable text file."""
    if not filename:
        return False
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in TEXT_EXTENSIONS


def _is_image_file(filename: str, content_type: str) -> bool:
    """Check if file is an image."""
    if content_type and content_type.lower() in IMAGE_MIMES:
        return True
    if filename:
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        return ext in IMAGE_EXTENSIONS
    return False


def _is_pdf_file(filename: str, content_type: str) -> bool:
    """Check if file is a PDF."""
    if content_type and content_type.lower() in PDF_MIMES:
        return True
    if filename:
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        return ext in PDF_EXTENSIONS
    return False


def _extract_pdf_text(raw: bytes, max_chars: int = 8000) -> tuple:
    """Extract text from PDF bytes. Returns (text, page_count, truncated)."""
    import fitz  # pymupdf
    doc = fitz.open(stream=raw, filetype="pdf")
    page_count = len(doc)
    text_parts = []
    total_chars = 0
    truncated = False

    for i, page in enumerate(doc):
        page_text = page.get_text()
        text_parts.append(f"\n--- หน้า {i + 1} ---\n{page_text}")
        total_chars += len(page_text)
        if total_chars >= max_chars:
            truncated = True
            break

    doc.close()
    full_text = "\n".join(text_parts)[:max_chars]
    return full_text, page_count, truncated


@app.post("/api/file-analyze")
async def api_file_analyze(
    file: UploadFile = File(...),
    question: str = Form(""),
    x_api_key: str = Header(None),
):
    """Analyze uploaded file (text or image) via API key.
    
    - Text files: content is read and sent to AI for analysis
    - Images: sent to vision-capable AI model
    - Optional 'question' form field to ask specific questions about the file
    """
    import os
    valid_key = os.getenv("BOT_API_KEY", "atsawin-bot-secret-2026")
    if x_api_key != valid_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    filename = file.filename or "unknown"
    content_type = file.content_type or ""
    file_ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    # Read file content
    raw = await file.read()
    file_size = len(raw)

    # Max 10MB for text, 5MB for images
    if file_size > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")

    # --- Image file ---
    if _is_image_file(filename, content_type):
        mime = content_type or "image/jpeg"
        if file_ext == ".png" or mime == "image/png":
            mime = "image/png"
        elif file_ext == ".gif" or mime == "image/gif":
            mime = "image/gif"
        elif file_ext == ".webp" or mime == "image/webp":
            mime = "image/webp"

        image_b64 = base64.b64encode(raw).decode("utf-8")

        prompt = question if question else "อธิบายรูปภาพนี้ให้หน่อย / Describe this image"
        vision_model = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"

        loop = __import__("asyncio").get_event_loop()
        response = await loop.run_in_executor(
            None, ask_ai_vision, vision_model, prompt, image_b64, mime
        )

        return {
            "type": "image",
            "filename": filename,
            "size": file_size,
            "model": vision_model,
            "response": response,
        }

    # --- PDF file ---
    if _is_pdf_file(filename, content_type):
        try:
            pdf_text, page_count, truncated = _extract_pdf_text(raw, max_chars=8000)
        except Exception as e:
            return {
                "type": "pdf_error",
                "filename": filename,
                "size": file_size,
                "response": f"❌ ไม่สามารถอ่าน PDF ได้: {str(e)}",
            }

        if not pdf_text.strip():
            return {
                "type": "pdf",
                "filename": filename,
                "size": file_size,
                "pages": page_count,
                "response": "📄 PDF นี้ไม่มีข้อความที่อ่านได้ (อาจเป็นรูปภาพสแกน)",
            }

        default_question = "สรุปเนื้อหา PDF นี้ให้หน่อย สิ่งที่สำคัญคืออะไร"
        prompt = question if question else default_question

        full_prompt = (
            f"ไฟล์ PDF: {filename}\n"
            f"จำนวนหน้า: {page_count}\n"
            f"{'⚠️ เนื้อหาถูกตัดให้สั้น (เกิน 8000 ตัวอักษร)' if truncated else ''}\n\n"
            f"--- เนื้อหา PDF ---\n{pdf_text}\n--- จบเนื้อหา ---\n\n"
            f"คำถาม: {prompt}"
        )

        result = select_model(prompt)
        loop = __import__("asyncio").get_event_loop()
        response = await loop.run_in_executor(
            None, ask_ai, result["model"], full_prompt
        )

        return {
            "type": "pdf",
            "filename": filename,
            "size": file_size,
            "pages": page_count,
            "truncated": truncated,
            "model": result["model"],
            "response": response,
        }

    # --- Text file ---
    if _is_text_file(filename):
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = raw.decode("latin-1")
            except Exception:
                return {
                    "type": "binary",
                    "filename": filename,
                    "size": file_size,
                    "response": f"ไม่สามารถอ่านไฟล์ได้ (binary file) ขนาด: {file_size:,} bytes",
                }

        # Truncate very long files
        max_chars = 8000
        truncated = False
        if len(text) > max_chars:
            text = text[:max_chars]
            truncated = True

        default_question = (
            "วิเคราะห์ไฟล์นี้ให้หน่อย สรุปสิ่งที่สำคัญ จุดที่ดี จุดที่ควรปรับปรุง"
        )
        prompt = question if question else default_question

        full_prompt = (
            f"ไฟล์: {filename}\n"
            f"ประเภท: {file_ext}\n"
            f"{'⚠️ ไฟล์ถูกตัดให้สั้น (ยาวเกิน 8000 ตัวอักษร)' if truncated else ''}\n\n"
            f"--- เนื้อหาไฟล์ ---\n{text}\n--- จบไฟล์ ---\n\n"
            f"คำถาม: {prompt}"
        )

        result = select_model(prompt)
        loop = __import__("asyncio").get_event_loop()
        response = await loop.run_in_executor(
            None, ask_ai, result["model"], full_prompt
        )

        return {
            "type": "text",
            "filename": filename,
            "size": file_size,
            "truncated": truncated,
            "lines": text.count("\n") + 1,
            "model": result["model"],
            "response": response,
        }

    # --- Other binary files ---
    return {
        "type": "binary",
        "filename": filename,
        "size": file_size,
        "content_type": content_type,
        "response": (
            f"ไฟล์: {filename}\n"
            f"ขนาด: {file_size:,} bytes\n"
            f"ประเภท: {content_type or 'unknown'}\n\n"
            f"❌ ไม่รองรับไฟล์ประเภทนี้ ส่งไฟล์ .txt, .py, .js, .json, .csv, .md "
            f"หรือรูปภาพ (.jpg, .png) ได้"
        ),
    }