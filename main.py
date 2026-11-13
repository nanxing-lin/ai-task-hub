from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, ConfigDict  # 引入新的 ConfigDict
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware

# ==========================================
# 1. 数据库配置 (新建一个 SQLite 文件)
# ==========================================
SQLALCHEMY_DATABASE_URL = "sqlite:///./tasks.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ==========================================
# 2. 定义数据库模型 (建表)
# ==========================================
class TaskDB(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    priority = Column(String, default="普通")
    is_done = Column(Boolean, default=False)


# 生成数据库表
Base.metadata.create_all(bind=engine)


# ==========================================
# 3. Pydantic 数据模型 (前后端交互格式)
# ==========================================
class TaskCreate(BaseModel):
    title: str
    priority: str = "普通"


class TaskResponse(TaskCreate):
    id: int
    is_done: bool
    # 修复警告：使用 Pydantic V2 的新写法
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 4. FastAPI 初始化 & 跨域设置
# ==========================================
app = FastAPI(title="AI Task Hub")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


# 依赖注入：每次请求时打开数据库，请求结束自动关闭
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==========================================
# 5. 接口路由 (CRUD)
# ==========================================
# 【查】GET: 获取所有任务
@app.get("/tasks", response_model=list[TaskResponse])
def get_tasks(db: Session = Depends(get_db)):
    tasks = db.query(TaskDB).all()
    return tasks


# 【增】POST: 添加新任务
@app.post("/tasks", response_model=TaskResponse)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    new_task = TaskDB(title=task.title, priority=task.priority)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


# 【改】PUT: 修改任务状态
@app.put("/tasks/{task_id}")
def update_task_status(task_id: int, is_done: bool, db: Session = Depends(get_db)):
    task = db.query(TaskDB).filter(TaskDB.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    task.is_done = is_done
    db.commit()
    return {"message": "状态更新成功", "task_id": task_id}


# 【删】DELETE: 删除任务
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(TaskDB).filter(TaskDB.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="你要删除的任务不存在")

    db.delete(task)
    db.commit()
    return {"message": f"成功删除了任务：{task.title}"}