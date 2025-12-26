from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from rag_system import rag 

app = FastAPI()

class QueryRequest(BaseModel):
    player_name: str
    question: str

print("🚀 MODEL SERVICE: Starting up... (The Brain is ON)")

@app.post("/generate")
def generate_response(request: QueryRequest):
    try:
        # The logic is all in rag_system.py now
        answer = rag.generate_answer(request.player_name, request.question)
        return {"answer": answer}
    except Exception as e:
        print(f"❌ MODEL ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)