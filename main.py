from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware
import requests

# ==========================================
# 1. 数据库配置
# ==========================================
SQLALCHEMY_DATABASE_URL = "sqlite:///./tasks.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ==========================================
# 2. 定义数据库模型
# ==========================================
class TaskDB(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    priority = Column(String, default="普通")
    is_done = Column(Boolean, default=False)


Base.metadata.create_all(bind=engine)


# ==========================================
# 3. Pydantic 数据模型
# ==========================================
class TaskCreate(BaseModel):
    title: str


class TaskResponse(TaskCreate):
    id: int
    priority: str
    is_done: bool
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 4. FastAPI 初始化 & 跨域
# ==========================================
app = FastAPI(title="AI Task Hub")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==========================================
# 5. AI 分析函数（升级版）
# ==========================================
# ⚠️ 记得替换成你自己的 API Key
API_KEY = "sk-37d06d9f65724e0ba7430f6e60d258a9"


def ask_ai_for_priority(task_title: str):
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    # 提示词规范了输出格式，去掉特殊符号干扰
    prompt = f"""
    你是一个任务优先级评估助手。请分析用户的任务描述。
    判断它是紧急/重要的事情（输出“高”），还是日常普通的事情（输出“普通”）。
    并且用一句话简短解释你的理由。

    请严格按照以下格式输出，不要加任何多余的废话：
    优先级：高
    理由：这里写你的理由

    用户任务：{task_title}
    """

    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        if response.status_code == 200:
            answer = response.json()["choices"][0]["message"]["content"]

            # 默认兜底值
            priority = "普通"
            reason = "AI 觉得这只是一件普通小事。"

            # 智能解析 AI 的回答
            if "优先级：高" in answer or "优先级:高" in answer:
                priority = "高"

            if "理由：" in answer:
                reason = answer.split("理由：")[1].strip()
            elif "理由:" in answer:
                reason = answer.split("理由:")[1].strip()

            return priority, reason

    except Exception as e:
        print(f"❌ AI 请求发生异常: {e}")

    return "普通", "AI 暂时无法分析，默认普通优先级。"


# ==========================================
# 6. 接口路由 (CRUD)
# ==========================================
@app.get("/tasks", response_model=list[TaskResponse])
def get_tasks(db: Session = Depends(get_db)):
    tasks = db.query(TaskDB).all()
    return tasks


@app.post("/tasks")
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    print(f"正在请求 AI 分析任务：{task.title}")

    # 获取 AI 的判定结果和理由
    ai_priority, ai_reason = ask_ai_for_priority(task.title)
    print(f"AI 判定的优先级：{ai_priority}，理由：{ai_reason}")

    # 存数据库
    new_task = TaskDB(title=task.title, priority=ai_priority)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    # 组装返回给前端的数据（核心：把 ai_reason 传给前端）
    return {
        "id": new_task.id,
        "title": new_task.title,
        "priority": new_task.priority,
        "is_done": new_task.is_done,
        "ai_message": ai_reason  # 前端通过这个字段展示 AI 理由
    }


@app.put("/tasks/{task_id}")
def update_task_status(task_id: int, is_done: bool, db: Session = Depends(get_db)):
    task = db.query(TaskDB).filter(TaskDB.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    task.is_done = is_done
    db.commit()
    return {"message": "状态更新成功", "task_id": task_id}


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(TaskDB).filter(TaskDB.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="你要删除的任务不存在")
    db.delete(task)
    db.commit()
    return {"message": f"成功删除了任务：{task.title}"}