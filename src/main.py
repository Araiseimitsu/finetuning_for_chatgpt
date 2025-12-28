"""
OpenAI ファインチューニング管理 - 統合Webアプリケーション

FastAPI + HTMX + Jinja2 + TailwindCSS
"""

import os
import json
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from openai import OpenAI

# FastAPI アプリケーション
app = FastAPI(title="OpenAI Fine-tuning Manager")

# 静的ファイルとテンプレート設定
app.mount("/static", StaticFiles(directory="src/static"), name="static")
templates = Jinja2Templates(directory="src/templates")


def get_openai_client() -> Optional[OpenAI]:
    """OpenAI クライアントを取得"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def format_bytes(size_bytes: int) -> str:
    """バイト単位を人間が読みやすい形式に変換"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def format_timestamp(timestamp: int) -> str:
    """Unixタイムスタンプを読みやすい日時形式に変換"""
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def validate_jsonl(content: str) -> tuple[bool, str, int]:
    """
    JSONLコンテンツのバリデーション

    Returns:
        (is_valid, message, line_count)
    """
    lines = content.strip().split('\n')
    line_count = 0
    format_type = None

    for line_num, line in enumerate(lines, 1):
        if not line.strip():
            continue
        line_count += 1
        try:
            data = json.loads(line)

            if format_type is None:
                if 'messages' in data:
                    format_type = 'chat'
                elif 'prompt' in data and 'completion' in data:
                    format_type = 'legacy'

            if format_type == 'chat':
                if 'messages' not in data:
                    return False, f"行{line_num}: 'messages'キーがありません", 0
                messages = data['messages']
                if not isinstance(messages, list) or len(messages) == 0:
                    return False, f"行{line_num}: 'messages'が無効です", 0
                for msg in messages:
                    if 'role' not in msg or 'content' not in msg:
                        return False, f"行{line_num}: メッセージ形式が不正です", 0

            elif format_type == 'legacy':
                if 'prompt' not in data or 'completion' not in data:
                    return False, f"行{line_num}: 'prompt'または'completion'がありません", 0

        except json.JSONDecodeError as e:
            return False, f"行{line_num}: JSON形式エラー - {e}", 0

    format_label = "チャット形式" if format_type == 'chat' else "レガシー形式"
    return True, f"{format_label}: {line_count}サンプル", line_count


# ===============================
# ページルート
# ===============================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """ダッシュボード"""
    client = get_openai_client()
    api_connected = client is not None

    stats = {
        "files": 0,
        "jobs": 0,
        "models": 0,
        "api_connected": api_connected
    }

    if client:
        try:
            files = client.files.list()
            stats["files"] = len([f for f in files.data if f.purpose == 'fine-tune'])

            jobs = client.fine_tuning.jobs.list(limit=100)
            stats["jobs"] = len(jobs.data)
            stats["models"] = len([j for j in jobs.data if j.status == 'succeeded'])
        except Exception:
            pass

    return templates.TemplateResponse("index.html", {
        "request": request,
        "stats": stats,
        "page": "dashboard"
    })


@app.get("/files", response_class=HTMLResponse)
async def files_page(request: Request):
    """ファイル管理ページ"""
    client = get_openai_client()
    files = []
    stats = {"api_connected": client is not None}

    if client:
        try:
            result = client.files.list()
            files = [
                {
                    "id": f.id,
                    "filename": f.filename,
                    "purpose": f.purpose,
                    "bytes": format_bytes(f.bytes),
                    "created_at": format_timestamp(f.created_at),
                    "status": f.status
                }
                for f in result.data if f.purpose == 'fine-tune'
            ]
        except Exception:
            pass

    return templates.TemplateResponse("files.html", {
        "request": request,
        "files": files,
        "stats": stats,
        "page": "files"
    })


@app.get("/jobs", response_class=HTMLResponse)
async def jobs_page(request: Request):
    """ジョブ管理ページ"""
    client = get_openai_client()
    jobs = []
    files = []
    stats = {"api_connected": client is not None}

    if client:
        try:
            result = client.fine_tuning.jobs.list(limit=50)
            jobs = [
                {
                    "id": j.id,
                    "model": j.model,
                    "fine_tuned_model": j.fine_tuned_model,
                    "status": j.status,
                    "created_at": format_timestamp(j.created_at),
                    "finished_at": format_timestamp(j.finished_at) if j.finished_at else None
                }
                for j in result.data
            ]

            files_result = client.files.list()
            files = [
                {"id": f.id, "filename": f.filename}
                for f in files_result.data if f.purpose == 'fine-tune' and f.status == 'processed'
            ]
        except Exception:
            pass

    return templates.TemplateResponse("jobs.html", {
        "request": request,
        "jobs": jobs,
        "files": files,
        "stats": stats,
        "page": "jobs"
    })


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    """チャットページ"""
    client = get_openai_client()
    models = []
    stats = {"api_connected": client is not None}

    if client:
        try:
            jobs = client.fine_tuning.jobs.list(limit=50)
            models = [
                {"id": j.fine_tuned_model, "name": j.fine_tuned_model.split(":")[-1]}
                for j in jobs.data if j.status == 'succeeded' and j.fine_tuned_model
            ]
        except Exception:
            pass

    return templates.TemplateResponse("chat.html", {
        "request": request,
        "models": models,
        "stats": stats,
        "page": "chat"
    })


# ===============================
# API エンドポイント
# ===============================

@app.post("/api/files/upload")
async def upload_file(file: UploadFile = File(...)):
    """ファイルアップロード"""
    client = get_openai_client()
    if not client:
        raise HTTPException(status_code=500, detail="API キーが設定されていません")

    content = await file.read()
    content_str = content.decode('utf-8')

    is_valid, message, line_count = validate_jsonl(content_str)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)

    try:
        uploaded = client.files.create(
            file=(file.filename, content),
            purpose='fine-tune'
        )
        return {
            "success": True,
            "file_id": uploaded.id,
            "filename": uploaded.filename,
            "message": f"アップロード成功: {message}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/files/{file_id}")
async def delete_file(file_id: str):
    """ファイル削除"""
    client = get_openai_client()
    if not client:
        raise HTTPException(status_code=500, detail="API キーが設定されていません")

    try:
        client.files.delete(file_id)
        return {"success": True, "message": "ファイルを削除しました"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/jobs/create")
async def create_job(
    training_file_id: str = Form(...),
    model: str = Form("gpt-4o-mini-2024-07-18"),
    suffix: str = Form(None),
    epochs: int = Form(3)
):
    """ファインチューニングジョブ作成"""
    client = get_openai_client()
    if not client:
        raise HTTPException(status_code=500, detail="API キーが設定されていません")

    try:
        job = client.fine_tuning.jobs.create(
            training_file=training_file_id,
            model=model,
            hyperparameters={"n_epochs": epochs},
            suffix=suffix if suffix else None
        )
        return {
            "success": True,
            "job_id": job.id,
            "status": job.status,
            "message": "ジョブを作成しました"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """ジョブステータス取得"""
    client = get_openai_client()
    if not client:
        raise HTTPException(status_code=500, detail="API キーが設定されていません")

    try:
        job = client.fine_tuning.jobs.retrieve(job_id)
        events = client.fine_tuning.jobs.list_events(fine_tuning_job_id=job_id, limit=5)

        return {
            "id": job.id,
            "status": job.status,
            "model": job.model,
            "fine_tuned_model": job.fine_tuned_model,
            "created_at": format_timestamp(job.created_at),
            "finished_at": format_timestamp(job.finished_at) if job.finished_at else None,
            "events": [
                {"time": format_timestamp(e.created_at), "message": e.message}
                for e in reversed(events.data)
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    """ジョブキャンセル"""
    client = get_openai_client()
    if not client:
        raise HTTPException(status_code=500, detail="API キーが設定されていません")

    try:
        client.fine_tuning.jobs.cancel(job_id)
        return {"success": True, "message": "ジョブをキャンセルしました"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/models/{model_id:path}")
async def delete_model(model_id: str):
    """モデル削除"""
    client = get_openai_client()
    if not client:
        raise HTTPException(status_code=500, detail="API キーが設定されていません")

    try:
        client.models.delete(model_id)
        return {"success": True, "message": "モデルを削除しました"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat_api(request: Request):
    """チャットAPI"""
    client = get_openai_client()
    if not client:
        raise HTTPException(status_code=500, detail="API キーが設定されていません")

    data = await request.json()
    model_id = data.get("model")
    message = data.get("message", "").strip()
    system_prompt = data.get("system_prompt", "")

    if not model_id or not message:
        raise HTTPException(status_code=400, detail="モデルとメッセージは必須です")

    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})

        response = client.chat.completions.create(
            model=model_id,
            messages=messages,
            max_tokens=1000
        )
        return {"response": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===============================
# HTMXパーシャル
# ===============================

@app.get("/htmx/files-list", response_class=HTMLResponse)
async def htmx_files_list(request: Request):
    """ファイル一覧パーシャル"""
    client = get_openai_client()
    files = []

    if client:
        try:
            result = client.files.list()
            files = [
                {
                    "id": f.id,
                    "filename": f.filename,
                    "purpose": f.purpose,
                    "bytes": format_bytes(f.bytes),
                    "created_at": format_timestamp(f.created_at),
                    "status": f.status
                }
                for f in result.data if f.purpose == 'fine-tune'
            ]
        except Exception:
            pass

    return templates.TemplateResponse("partials/files_list.html", {
        "request": request,
        "files": files
    })


@app.get("/htmx/jobs-list", response_class=HTMLResponse)
async def htmx_jobs_list(request: Request):
    """ジョブ一覧パーシャル"""
    client = get_openai_client()
    jobs = []

    if client:
        try:
            result = client.fine_tuning.jobs.list(limit=50)
            jobs = [
                {
                    "id": j.id,
                    "model": j.model,
                    "fine_tuned_model": j.fine_tuned_model,
                    "status": j.status,
                    "created_at": format_timestamp(j.created_at),
                    "finished_at": format_timestamp(j.finished_at) if j.finished_at else None
                }
                for j in result.data
            ]
        except Exception:
            pass

    return templates.TemplateResponse("partials/jobs_list.html", {
        "request": request,
        "jobs": jobs
    })


@app.get("/htmx/job-status/{job_id}", response_class=HTMLResponse)
async def htmx_job_status(request: Request, job_id: str):
    """ジョブステータスパーシャル"""
    client = get_openai_client()
    job_data = None

    if client:
        try:
            job = client.fine_tuning.jobs.retrieve(job_id)
            events = client.fine_tuning.jobs.list_events(fine_tuning_job_id=job_id, limit=10)
            job_data = {
                "id": job.id,
                "status": job.status,
                "model": job.model,
                "fine_tuned_model": job.fine_tuned_model,
                "created_at": format_timestamp(job.created_at),
                "finished_at": format_timestamp(job.finished_at) if job.finished_at else None,
                "events": [
                    {"time": format_timestamp(e.created_at), "message": e.message}
                    for e in reversed(events.data)
                ]
            }
        except Exception:
            pass

    return templates.TemplateResponse("partials/job_status.html", {
        "request": request,
        "job": job_data
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
