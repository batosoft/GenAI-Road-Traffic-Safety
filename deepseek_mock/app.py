from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import json
import random

app = FastAPI(title="DeepSeek V3 Mock API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000

class ChatChoice(BaseModel):
    index: int
    message: Message
    finish_reason: str

class ChatResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[ChatChoice]
    usage: Dict[str, int]

@app.get("/")
async def root():
    return {"message": "DeepSeek V3 Mock API is running"}

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    """
    Mock endpoint for DeepSeek V3 chat completions API
    """
    # Extract the last user message
    last_message = request.messages[-1].content if request.messages else ""
    
    # Generate a response based on the content
    response_content = generate_mock_response(last_message)
    
    # Create a mock response
    response = ChatResponse(
        id=f"mock-{random.randint(1000, 9999)}",
        object="chat.completion",
        created=int(random.random() * 1000000000),
        model=request.model,
        choices=[
            ChatChoice(
                index=0,
                message=Message(
                    role="assistant",
                    content=response_content
                ),
                finish_reason="stop"
            )
        ],
        usage={
            "prompt_tokens": len(last_message.split()),
            "completion_tokens": len(response_content.split()),
            "total_tokens": len(last_message.split()) + len(response_content.split())
        }
    )
    
    return response

def generate_mock_response(prompt: str) -> str:
    """
    Generate a mock response based on the prompt content
    """
    # Check if the prompt contains traffic fine analysis request
    if "traffic fine" in prompt.lower() or "fine history" in prompt.lower():
        # Extract fine types if present
        fine_types = []
        if "Speeding" in prompt:
            fine_types.append("Speeding")
        if "Red Light" in prompt:
            fine_types.append("Red Light Violation")
        if "Parking" in prompt:
            fine_types.append("Illegal Parking")
        if "Seatbelt" in prompt:
            fine_types.append("Driving without Seatbelt")
        if "Phone" in prompt:
            fine_types.append("Using Phone while Driving")
        
        # Default to speeding if no specific types found
        if not fine_types:
            fine_types = ["Speeding"]
        
        # Generate a structured response
        return f"""## Pattern Analysis
Based on your traffic fine history, I've identified a pattern of {fine_types[0]} violations. This suggests you may be regularly exceeding speed limits, possibly due to time pressure or lack of attention to speed limit signs.

## Personalized Safety Tips
1. Use cruise control on highways to maintain a consistent legal speed
2. Leave 10 minutes earlier for your destinations to reduce time pressure
3. Pay special attention to speed limit changes, especially in construction zones
4. Consider using a GPS app that provides speed limit alerts
5. Be mindful of your speed in residential areas and school zones

## Educational Information
{fine_types[0]} is one of the most common traffic violations and also one of the leading causes of accidents. Exceeding the speed limit reduces your reaction time and increases the severity of crashes. For every 5 km/h over the limit, the risk of a crash doubles.

## Potential Financial Savings
By avoiding these violations, you could save approximately 3,000 AED per year in fines. Additionally, maintaining a clean driving record can lead to lower insurance premiums, potentially saving another 1,500 AED annually.

## Recommended Behavioral Changes
1. Develop a habit of regularly checking your speedometer
2. Practice mindful driving by eliminating distractions
3. Plan your routes in advance to avoid rushing
4. Set personal speed limits slightly below the legal limits
5. Consider taking a defensive driving course to improve overall driving habits
"""
    
    # Default response for other types of prompts
    return "I am the DeepSeek V3 mock API. This is a simulated response for development purposes."

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)
