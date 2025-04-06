import os
import json
import requests
from fastapi import FastAPI, HTTPException, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn

app = FastAPI(title="Traffic Fine Analyzer API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DeepSeek API configuration
DEEPSEEK_API_URL = os.environ.get("DEEPSEEK_API_URL", "http://deepseek:8080/v1/chat/completions")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")  # Will be set in docker-compose

class FineEntry(BaseModel):
    date: str
    type: str
    amount: float
    location: Optional[str] = None
    description: Optional[str] = None

class FineHistory(BaseModel):
    fines: List[FineEntry]
    user_info: Optional[Dict[str, Any]] = None

@app.get("/")
async def root():
    return {"message": "Traffic Fine Analyzer API is running"}

@app.post("/analyze")
async def analyze_fines(fine_history: FineHistory):
    """
    Analyze traffic fine history using DeepSeek V3 model.
    
    Parameters:
    - fine_history: JSON object containing fine history data
    
    Returns:
    - JSON response with analysis results
    """
    try:
        # Prepare the data for analysis
        fines = fine_history.fines
        
        if not fines:
            raise HTTPException(status_code=400, detail="No fine history provided")
        
        # Calculate basic statistics
        total_fines = len(fines)
        total_amount = sum(fine.amount for fine in fines)
        fine_types = {}
        
        for fine in fines:
            if fine.type in fine_types:
                fine_types[fine.type] += 1
            else:
                fine_types[fine.type] = 1
        
        # Sort fine types by frequency
        sorted_fine_types = sorted(fine_types.items(), key=lambda x: x[1], reverse=True)
        most_common_fine = sorted_fine_types[0][0] if sorted_fine_types else "None"
        
        # Prepare prompt for DeepSeek V3
        fine_history_text = "Fine History:\n"
        for i, fine in enumerate(fines, 1):
            fine_history_text += f"{i}. Date: {fine.date}, Type: {fine.type}, Amount: {fine.amount}"
            if fine.location:
                fine_history_text += f", Location: {fine.location}"
            if fine.description:
                fine_history_text += f", Description: {fine.description}"
            fine_history_text += "\n"
        
        prompt = f"""As the Salama AI Assistant, analyze the following traffic fine history and provide personalized safety advice:

{fine_history_text}

Statistics:
- Total number of fines: {total_fines}
- Total amount paid: {total_amount}
- Most common fine type: {most_common_fine}

Based on this history, please provide:
1. A pattern analysis of the user's traffic violations
2. Personalized safety tips to avoid future fines
3. Educational information about the most common violation
4. Potential financial savings if these behaviors are corrected
5. Specific behavioral changes recommended

Format your response in clear sections with headings.
"""
        
        # Prepare request to DeepSeek API
        headers = {
            "Content-Type": "application/json"
        }
        
        if DEEPSEEK_API_KEY:
            headers["Authorization"] = f"Bearer {DEEPSEEK_API_KEY}"
        
        payload = {
            "model": "deepseek-chat",  # DeepSeek V3 model
            "messages": [
                {"role": "system", "content": "You are Salama AI Assistant, a helpful traffic safety advisor that analyzes fine history and provides personalized advice to improve driving behavior and reduce fines."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        # Call DeepSeek API
        try:
            response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            # Fallback to local analysis if API is unavailable
            return generate_fallback_analysis(fines, total_fines, total_amount, most_common_fine)
        
        # Process the response
        result = response.json()
        analysis_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        if not analysis_text:
            # Fallback if no valid response
            return generate_fallback_analysis(fines, total_fines, total_amount, most_common_fine)
        
        # Extract sections from analysis text
        pattern_analysis = extract_section(analysis_text, "Pattern Analysis", "Personalized Safety Tips")
        safety_tips = extract_section(analysis_text, "Personalized Safety Tips", "Educational Information")
        educational_info = extract_section(analysis_text, "Educational Information", "Potential Financial Savings")
        financial_savings = extract_section(analysis_text, "Potential Financial Savings", "Recommended Behavioral Changes")
        behavioral_changes = extract_section(analysis_text, "Recommended Behavioral Changes", None)
        
        # Prepare the response
        result = {
            "statistics": {
                "total_fines": total_fines,
                "total_amount": total_amount,
                "fine_types": dict(sorted_fine_types),
                "most_common_fine": most_common_fine
            },
            "analysis": {
                "pattern_analysis": pattern_analysis,
                "safety_tips": safety_tips,
                "educational_info": educational_info,
                "financial_savings": financial_savings,
                "behavioral_changes": behavioral_changes
            },
            "full_analysis": analysis_text
        }
        
        return JSONResponse(content=result)
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

def extract_section(text, start_marker, end_marker):
    """Extract a section from the analysis text"""
    try:
        # Try to find the section with heading format (## Section Name)
        start_pattern = f"## {start_marker}"
        if start_pattern not in text:
            # Try alternative formats
            start_pattern = f"**{start_marker}**"
            if start_pattern not in text:
                start_pattern = start_marker
        
        start_idx = text.find(start_pattern)
        if start_idx == -1:
            return None
        
        # Move past the heading
        start_idx = text.find("\n", start_idx)
        if start_idx == -1:
            return None
        start_idx += 1
        
        if end_marker:
            # Try to find the end marker with heading format
            end_pattern = f"## {end_marker}"
            if end_pattern not in text[start_idx:]:
                # Try alternative formats
                end_pattern = f"**{end_marker}**"
                if end_pattern not in text[start_idx:]:
                    end_pattern = end_marker
            
            end_idx = text.find(end_pattern, start_idx)
            if end_idx == -1:
                return text[start_idx:].strip()
            return text[start_idx:end_idx].strip()
        else:
            return text[start_idx:].strip()
    except:
        return None

def generate_fallback_analysis(fines, total_fines, total_amount, most_common_fine):
    """Generate a fallback analysis when the API is unavailable"""
    # Create a simple analysis based on the statistics
    pattern_analysis = f"Based on your {total_fines} traffic fines, your most common violation is '{most_common_fine}'."
    
    # Generic safety tips based on common fine types
    safety_tips = """
    1. Always obey speed limits and traffic signs
    2. Maintain a safe distance from other vehicles
    3. Use turn signals when changing lanes
    4. Avoid using mobile phones while driving
    5. Always wear your seatbelt
    """
    
    # Generic educational information
    educational_info = f"Traffic violations like '{most_common_fine}' not only result in fines but also increase the risk of accidents and may affect your insurance premiums."
    
    # Financial calculation
    financial_savings = f"By avoiding these violations, you could save approximately {total_amount} per year in fines."
    
    # Generic behavioral recommendations
    behavioral_changes = """
    1. Plan your trips with extra time to avoid rushing
    2. Set reminders about traffic rules
    3. Use navigation apps that alert you to speed limits
    4. Practice defensive driving techniques
    5. Consider taking a defensive driving course
    """
    
    # Combine into full analysis
    full_analysis = f"""## Pattern Analysis
    {pattern_analysis}
    
    ## Personalized Safety Tips
    {safety_tips}
    
    ## Educational Information
    {educational_info}
    
    ## Potential Financial Savings
    {financial_savings}
    
    ## Recommended Behavioral Changes
    {behavioral_changes}
    """
    
    # Prepare the response
    result = {
        "statistics": {
            "total_fines": total_fines,
            "total_amount": total_amount,
            "most_common_fine": most_common_fine
        },
        "analysis": {
            "pattern_analysis": pattern_analysis,
            "safety_tips": safety_tips,
            "educational_info": educational_info,
            "financial_savings": financial_savings,
            "behavioral_changes": behavioral_changes
        },
        "full_analysis": full_analysis,
        "note": "This is a fallback analysis generated locally as the DeepSeek API was unavailable."
    }
    
    return JSONResponse(content=result)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
