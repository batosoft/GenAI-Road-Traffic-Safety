# Salama AI Assistant

## Overview
Salama AI Assistant is a Flask-based AI module for the Dubai RTA traffic management application that analyzes user traffic fine history and provides personalized safety tips. The module integrates into the existing fines payment page and is activated via a "Salama AI Assistant" button.

## Core Functionality
1. Analyzes historical traffic fine data to identify patterns and trends
2. Generates personalized safety insights based on violation types and frequency
3. Provides educational tips specific to the user's driving behavior
4. Presents statistical summaries of fine history with visualizations
5. Integrates seamlessly with the existing Laravel application interface

## Technical Architecture

### Backend (Python/Flask)
- RESTful API endpoints for data retrieval and analysis
- Data processing logic to analyze fine history
- Integration with machine learning model for pattern recognition
- Caching for performance optimization
- Multilingual support (English/Arabic)
- Laravel Backoffice interface for managing fines data

### Frontend Integration
- Responsive UI components matching RTA design language
- Interactive charts for data visualization
- Accessibility compliance
- Support for both desktop and mobile interfaces

### Database Integration
- Connection to Laravel MySQL database for fine history retrieval
- Data models for storing analysis results
- Data sanitization and validation

### AI/ML Components
- Fine pattern analysis algorithms
- Recommendation engine for safety tips
- Personalization logic based on user history
- GenAI for generating natural language insights using Ollama models

## API Endpoints

1. `/api/fines/history` - Retrieve user's fine history
   - Method: POST
   - Parameters: user_id
   - Returns: JSON object with fine history

2. `/api/fines/analysis` - Generate analysis of fine patterns
   - Method: POST
   - Parameters: user_id
   - Returns: JSON object with analysis results, insights, and safety tips

3. `/api/safety/tips` - Generate personalized safety recommendations
   - Method: POST
   - Parameters: user_id
   - Returns: JSON object with safety tips

4. `/api/stats/summary` - Generate statistical summary of fine history
   - Method: POST
   - Parameters: user_id
   - Returns: JSON object with statistical summary

## Admin Interface

1. `/admin` - Admin dashboard
   - Displays summary statistics of fines and users

2. `/admin/fines` - Manage fines
   - View, edit, and delete traffic fines

3. `/admin/fines/add` - Add new fine
   - Form to add a new traffic fine to the database

4. `/admin/fines/edit/<fine_id>` - Edit fine
   - Form to edit an existing traffic fine

## Setup Instructions

### Prerequisites
- Python 3.9+
- MySQL database
- Docker (optional, for containerized deployment)

### Local Development Setup

1. Clone the repository:
   ```
   git clone <repository-url>
   cd rta_ai_ops/genai_apps/salama_ai_ssistant
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   - Create a `.env` file with the following variables:
     ```
     DB_HOST=127.0.0.1
     DB_PORT=3306
     DB_DATABASE=rta_ai_ops
     DB_USERNAME=root
     DB_PASSWORD=
     OLLAMA_API_URL=http://100.69.25.25:11434/api/generate
     OLLAMA_MODEL=llama3.1:latest
     ```

4. Run the application:
   ```
   python app.py
   ```

5. Access the application:
   - Main interface: http://localhost:5002
   - Admin interface: http://localhost:5002/admin

### Docker Deployment

1. Build the Docker image:
   ```
   docker build -t salama-ai-assistant .
   ```

2. Run the container:
   ```
   docker run -p 5002:5002 -e DB_HOST=host.docker.internal -e DB_PORT=3306 -e DB_DATABASE=rta_ai_ops -e DB_USERNAME=root -e DB_PASSWORD= salama-ai-assistant
   ```

3. Access the application:
   - Main interface: http://localhost:5002
   - Admin interface: http://localhost:5002/admin

## Integration with Laravel

To integrate the Salama AI Assistant with the existing Laravel application:

1. Add the following iframe to the Laravel view at `/genai/salama-ai-ssistant`:
   ```html
   <iframe src="http://localhost:5002" width="100%" height="800px" frameborder="0"></iframe>
   ```

2. Ensure the Laravel application can communicate with the Flask API endpoints.

## Database Schema

The application uses the following database table:

```sql
CREATE TABLE traffic_fines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    vehicle_info VARCHAR(255) NOT NULL,
    issue_date DATETIME NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    source VARCHAR(100) NOT NULL,
    black_points INT DEFAULT 0,
    location VARCHAR(255) NOT NULL,
    violation_details TEXT NOT NULL,
    fine_number VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_issue_date (issue_date)
);
```

## License

This project is proprietary and confidential. Unauthorized copying, transfer, or reproduction of the contents of this project is strictly prohibited.