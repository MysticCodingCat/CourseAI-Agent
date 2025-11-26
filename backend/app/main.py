from fastapi import FastAPI

app = FastAPI(title="CourseAI Backend", version="0.1.0")

@app.get("/")
def read_root():
    return {"message": "CourseAI Agent Backend is running on AMD MI300X!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
