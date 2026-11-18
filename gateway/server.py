from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from litellm import completion
import os

app = FastAPI()

GATEWAY_KEY = os.environ.get("DEV_GATEWAY_KEY")

class ChatRequest(BaseModel):
    model: str
    prompt: str


@app.post("/chat")
def chat(request: ChatRequest, authorization: str = Header(None)):

    if not GATEWAY_KEY:
        raise HTTPException(status_code=500, detail="Gateway key not configured")

    if authorization != f"Bearer {GATEWAY_KEY}":
        raise HTTPException(status_code=401, detail="Invalid API KEY")


    try:
        response = completion(
                model=request.model, 
                messages=[
                    {
                        "role": "user", 
                        "content": request.prompt, 
                    }
                ],
        )

        return {
                "response": response.choices[0].message.content

        }
    except Exception as e:
        raise HTTPException(
                status_code=500,
                detail=str(e)
            )

