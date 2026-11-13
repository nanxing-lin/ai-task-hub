from fastapi import FastAPI

app = FastAPI(title="AI Task Hub")


@app.get("/tasks")
def get_tasks():
    return {
        "code": 200,
        "data": ["学习Python", "学习RAG"]
    }