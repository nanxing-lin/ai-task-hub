from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from fastapi.middleware.cors import CORSMiddleware  # 解决跨域的核心

app = FastAPI(title="AI Task Hub")

# ==========================================
# 核心配置：允许前端跨域访问（解决满屏红字）
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # 允许所有网址（包括你本地的 file:// 和 localhost）
    allow_credentials=True,
    allow_methods=["*"],      # 允许所有请求方法（GET, POST 等）
    allow_headers=["*"],      # 允许所有请求头
)

# ==========================================
# 数据模型定义
# ==========================================
class TaskCreate(BaseModel):
    title: str
    priority: str = "普通"

class TaskResponse(TaskCreate):
    id: int
    is_done: bool

# ==========================================
# 模拟数据库（存在内存里）
# ==========================================
tasks_db = [
    {"id": 1, "title": "学习FastAPI", "priority": "高", "is_done": False},
    {"id": 2, "title": "买咖啡豆", "priority": "普通", "is_done": True}
]

# ==========================================
# 接口路由
# ==========================================
# 1. GET 接口：获取所有任务
@app.get("/tasks", response_model=List[TaskResponse])
def get_tasks():
    return tasks_db

# 2. POST 接口：添加新任务
@app.post("/tasks")
def create_task(task: TaskCreate):
    new_id = len(tasks_db) + 1
    new_task = {
        "id": new_id,
        "title": task.title,
        "priority": task.priority,
        "is_done": False
    }
    tasks_db.append(new_task)
    return {"message": "添加成功！", "task": new_task}


# 3. PUT 接口：更新任务的完成状态
@app.put("/tasks/{task_id}")
def update_task_status(task_id: int, is_done: bool):
    # 遍历我们的临时数据库，找对应的任务 ID
    for task in tasks_db:
        if task["id"] == task_id:
            # 找到后，把完成状态改掉
            task["is_done"] = is_done
            return {"message": "状态更新成功", "task": task}

    # 如果循环跑完都没找到，返回错误提示
    return {"error": "没找到这个任务"}