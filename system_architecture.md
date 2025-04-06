# GenAI Road Safety Application - System Architecture

## Overview
The GenAI Road Safety Application consists of two main components:
1. **Road Hazard Reporter** - Uses Ollama Vision models to analyze road damage images
2. **Traffic Fine Analyzer (Salama AI Assistant)** - Uses DeepSeek V3 to analyze traffic fine history

The system is containerized using Docker Compose for easy deployment and scalability.

## Architecture Components

### 1. Frontend
- **Technology**: HTML, CSS, JavaScript, NodeJS
- **Features**:
  - Responsive design for mobile and desktop
  - Image upload for road damage reporting
  - Form for traffic fine history input
  - Results display for both components
  - Report generation for submission to authorities

### 2. Backend API
- **Technology**: Python, FastAPI
- **Features**:
  - RESTful API endpoints for both components
  - Image processing and validation
  - Data validation and sanitization
  - Authentication and rate limiting
  - Report generation

### 3. AI Models
- **Road Damage Analysis**:
  - Ollama with Llama 3.2 Vision (11B model)
  - Image classification for damage type
  - Severity assessment
  - Location extraction from image metadata
  
- **Traffic Fine Analysis**:
  - DeepSeek V3 model
  - Pattern recognition in fine history
  - Personalized advice generation
  - Statistical analysis of fine types and frequencies

### 4. Database
- **Technology**: SQLite (for simplicity in local deployment)
- **Data Stored**:
  - User submissions (images, reports)
  - Analysis results
  - Generated reports
  - Fine history (anonymized)

## Container Structure
1. **Frontend Container**:
   - Nginx web server
   - Static files for web interface

2. **Backend API Container**:
   - Python FastAPI application
   - Business logic for both components
   - Integration with AI models

3. **Ollama Container**:
   - Ollama server with Llama 3.2 Vision model
   - Exposed API for image analysis

4. **DeepSeek Container**:
   - DeepSeek V3 model server
   - Exposed API for text analysis

5. **Database Container**:
   - SQLite database
   - Volume for data persistence

## Data Flow
1. **Road Hazard Reporting**:
   - User uploads image via frontend
   - Backend validates and processes image
   - Image sent to Ollama container for analysis
   - Results returned to backend for processing
   - Structured report generated
   - Results displayed to user with option to submit to authorities

2. **Traffic Fine Analysis**:
   - User inputs fine history via frontend
   - Backend validates and processes input
   - Data sent to DeepSeek container for analysis
   - Personalized advice generated
   - Results displayed to user with statistics and recommendations

## API Endpoints
1. `/api/road-hazard/analyze` - POST endpoint for road damage image analysis
2. `/api/road-hazard/report` - POST endpoint for generating and submitting reports
3. `/api/traffic-fine/analyze` - POST endpoint for traffic fine history analysis
4. `/api/traffic-fine/advice` - GET endpoint for retrieving personalized advice

## Security Considerations
- Input validation for all user-submitted data
- Rate limiting to prevent abuse
- No personal data stored in the database
- Secure communication between containers
- HTTPS for production deployment

## Scalability
- Docker Compose allows for easy scaling of individual components
- Stateless design enables horizontal scaling
- Database can be replaced with more robust solutions for production
