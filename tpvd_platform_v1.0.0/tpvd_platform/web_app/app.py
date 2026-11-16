# -*- coding: utf-8 -*-
"""
app.py
TPV-D 实训综合评价与人机协同复核系统 Web 应用主程序
基于 FastAPI + Jinja2 Templates 构建
"""

import os
import sys

# 将父目录加入 sys.path 便于模块导入
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional

from tpvd_platform.platform_core.database import PlatformDatabase
from tpvd_platform.scripts.automated_evaluator import evaluate_submission

app = FastAPI(title="TPV-D Educational Assessment Platform", version="2.0.0")

# 挂载模板目录
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

# 初始化数据库
db = PlatformDatabase()

class ReviewVerdictRequest(BaseModel):
    review_status: str
    variant_task_assigned: bool
    retest_passed: Optional[bool] = None

@app.get("/", response_class=RedirectResponse)
async def root():
    return RedirectResponse(url="/dashboard")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_view(request: Request):
    metrics = db.get_platform_metrics()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "active_page": "dashboard",
        "metrics": metrics,
        "clos": db.clos
    })

@app.get("/teacher", response_class=HTMLResponse)
async def teacher_view(request: Request):
    review_queue = db.get_review_queue()
    return templates.TemplateResponse("teacher.html", {
        "request": request,
        "active_page": "teacher",
        "review_queue": review_queue,
        "students": db.students
    })

@app.get("/student/{student_id}", response_class=HTMLResponse)
async def student_view(request: Request, student_id: str):
    student = db.get_student(student_id)
    record = db.get_record(student_id)
    if not student or not record:
        raise HTTPException(status_code=404, detail="未找到该学生记录")
        
    return templates.TemplateResponse("student.html", {
        "request": request,
        "active_page": "student",
        "student": student,
        "record": record,
        "clos": db.clos
    })

@app.get("/review/{student_id}", response_class=HTMLResponse)
async def review_view(request: Request, student_id: str):
    student = db.get_student(student_id)
    record = db.get_record(student_id)
    if not student or not record:
        raise HTTPException(status_code=404, detail="未找到该学生记录")
        
    return templates.TemplateResponse("review.html", {
        "request": request,
        "active_page": "teacher",
        "student": student,
        "record": record,
        "clos": db.clos
    })

# ----------------------------------------------------
# REST APIs
# ----------------------------------------------------
@app.get("/api/metrics")
async def get_metrics():
    metrics = db.get_platform_metrics()
    return JSONResponse(content=metrics.__dict__)

@app.get("/api/students")
async def get_students():
    records = db.get_all_records()
    data = []
    for r in records:
        s = db.get_student(r.student_id)
        item = r.__dict__.copy()
        item["name"] = s.name if s else ""
        item["group_id"] = s.group_id if s else ""
        item["role_name"] = s.role_name if s else ""
        data.append(item)
    return JSONResponse(content=data)

@app.post("/api/review/{student_id}")
async def submit_review(student_id: str, payload: ReviewVerdictRequest):
    success = db.update_review_decision(
        student_id=student_id,
        status=payload.review_status,
        assign_variant=payload.variant_task_assigned,
        retest_passed=payload.retest_passed
    )
    if not success:
        raise HTTPException(status_code=404, detail="更新失败，未找到该记录")
    return {"status": "success", "student_id": student_id}

@app.post("/api/evaluate/{student_id}")
async def run_evaluation_for_student(student_id: str):
    """
    针对特定学生调用自动化测试套件评估 T 维度得分并刷新数据库
    """
    eval_res = evaluate_submission()
    record = db.get_record(student_id)
    if record:
        record.t_score = float(eval_res["total_t_score"])
        record.calculate_discrepancy()
        db.save_to_json()
    return JSONResponse(content=eval_res)

if __name__ == "__main__":
    import uvicorn
    print("启动 TPV-D 实训达成评价与复核辅助系统 Web 服务...")
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
