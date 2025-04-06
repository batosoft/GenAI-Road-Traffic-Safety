import os
import json
import requests
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import base64
from PIL import Image
from io import BytesIO
import uvicorn

app = FastAPI(title="Road Hazard Reporter API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ollama API endpoint
OLLAMA_API_URL = os.environ.get("OLLAMA_API_URL", "http://ollama:11434/api/chat")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2-vision")

@app.get("/")
async def root():
    return {"message": "Road Hazard Reporter API is running"}

@app.post("/analyze")
async def analyze_road_damage(
    file: UploadFile = File(...),
    location: str = Form(None),
    description: str = Form(None)
):
    """
    Analyze road damage from an uploaded image using Ollama Vision model.
    
    Parameters:
    - file: The image file to analyze
    - location: Optional location information
    - description: Optional description of the damage
    
    Returns:
    - JSON response with analysis results
    """
    try:
        # Read and validate the image
        contents = await file.read()
        try:
            img = Image.open(BytesIO(contents))
            img_format = img.format.lower()
            if img_format not in ["jpeg", "jpg", "png"]:
                raise HTTPException(status_code=400, detail="Only JPEG and PNG images are supported")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")
        
        # Convert image to base64
        base64_image = base64.b64encode(contents).decode("utf-8")
        
        # Prepare prompt for the model
        prompt = "Analyze this road damage image and provide the following information:\n"
        prompt += "1. Type of damage (pothole, crack, broken sign, etc.)\n"
        prompt += "2. Severity level (low, medium, high)\n"
        prompt += "3. Potential safety impact\n"
        prompt += "4. Recommended action\n"
        
        if description:
            prompt += f"\nUser description: {description}\n"
        
        if location:
            prompt += f"\nLocation information: {location}\n"
        
        # Prepare request to Ollama API
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [base64_image]
                }
            ]
        }
        
        # Call Ollama API
        response = requests.post(OLLAMA_API_URL, json=payload)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=500, 
                detail=f"Error from Ollama API: {response.text}"
            )
        
        # Process the response
        result = response.json()
        analysis_text = result.get("message", {}).get("content", "")
        
        # Extract structured information from the analysis text
        # This is a simple extraction, could be improved with regex or more sophisticated parsing
        damage_type = extract_info(analysis_text, "Type of damage", "Severity level")
        severity = extract_info(analysis_text, "Severity level", "Potential safety impact")
        safety_impact = extract_info(analysis_text, "Potential safety impact", "Recommended action")
        recommended_action = extract_info(analysis_text, "Recommended action", None)
        
        # Prepare the response
        result = {
            "damage_type": damage_type.strip() if damage_type else "Unknown",
            "severity": severity.strip() if severity else "Unknown",
            "safety_impact": safety_impact.strip() if safety_impact else "Unknown",
            "recommended_action": recommended_action.strip() if recommended_action else "Unknown",
            "full_analysis": analysis_text,
            "location": location,
            "description": description
        }
        
        return JSONResponse(content=result)
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

def extract_info(text, start_marker, end_marker):
    """Extract information between markers from text"""
    try:
        start_idx = text.find(start_marker)
        if start_idx == -1:
            return None
        
        start_idx += len(start_marker)
        
        if end_marker:
            end_idx = text.find(end_marker, start_idx)
            if end_idx == -1:
                return text[start_idx:].strip()
            return text[start_idx:end_idx].strip()
        else:
            return text[start_idx:].strip()
    except:
        return None

@app.post("/generate-report")
async def generate_report(data: dict):
    """
    Generate a structured report for submission to authorities
    
    Parameters:
    - data: JSON data containing analysis results and additional information
    
    Returns:
    - JSON response with the generated report
    """
    try:
        # Extract data
        damage_type = data.get("damage_type", "Unknown")
        severity = data.get("severity", "Unknown")
        safety_impact = data.get("safety_impact", "Unknown")
        recommended_action = data.get("recommended_action", "Unknown")
        location = data.get("location", "Unknown location")
        description = data.get("description", "")
        full_analysis = data.get("full_analysis", "")
        
        # Generate report ID (in a real app, this would be stored in a database)
        import uuid
        report_id = str(uuid.uuid4())[:8].upper()
        
        # Create report
        report = {
            "report_id": report_id,
            "timestamp": str(datetime.datetime.now()),
            "location": location,
            "damage_details": {
                "type": damage_type,
                "severity": severity,
                "safety_impact": safety_impact,
                "recommended_action": recommended_action
            },
            "description": description,
            "ai_analysis": full_analysis,
            "status": "pending_submission"
        }
        
        return JSONResponse(content={"report": report, "message": "Report generated successfully"})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

if __name__ == "__main__":
    import datetime
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
