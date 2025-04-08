# GenAI Road Safety Application

This application enhances road safety through two AI-powered components:

1. **Road Hazard Reporter**: Uses Ollama Vision models to analyze road damage images and generate reports for authorities.
2. **Traffic Fine Analyzer (Salama AI Assistant)**: Uses DeepSeek V3 to analyze traffic fine history and provide personalized safety advice.

## System Requirements

- Docker and Docker Compose
- At least 8GB RAM for running Ollama Vision models
- Internet connection for initial model downloads

## Quick Start

1. Clone this repository
2. Run the application:
   ```bash
   docker-compose up
   ```
3. Access the application at http://localhost

**Note**: The first run will take some time as it downloads the Ollama image and models.

## Components

### Frontend
- Web-based interface with responsive design
- Dashboard for accessing both components
- Built with HTML, CSS, JavaScript, and Bootstrap

### Road Hazard Reporter
- Upload images of road damage
- AI analysis of damage type and severity
- Structured report generation
- Submission to authorities

### Traffic Fine Analyzer (Salama AI Assistant)
- Input traffic fine history
- Pattern analysis of violations
- Personalized safety tips
- Educational information and behavioral recommendations

## Architecture

The application is containerized using Docker Compose with the following services:

- **Frontend**: Nginx web server serving the main interface
- **Road Hazard API**: FastAPI service for road damage analysis
- **Traffic Fine API**: FastAPI service for traffic fine analysis
- **Ollama**: Service running Llama 3.2 Vision models
- **DeepSeek Mock**: Service simulating DeepSeek V3 API for local development

## Development

### Project Structure
```
.
├── docker-compose.yml
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── static/
│       └── index.html
├── road_hazard_reporter/
│   ├── Dockerfile
│   ├── app.py
│   ├── main.py
│   ├── requirements.txt
│   └── static/
│       └── index.html
├── traffic_fine_analyzer/
│   ├── Dockerfile
│   ├── app.py
│   ├── main.py
│   ├── requirements.txt
│   └── static/
│       └── index.html
└── deepseek_mock/
    ├── Dockerfile
    └── app.py
```

### API Endpoints

#### Road Hazard Reporter
- `POST /api/road-hazard/analyze`: Analyze road damage image
- `POST /api/road-hazard/generate-report`: Generate structured report

#### Traffic Fine Analyzer
- `POST /api/traffic-fine/analyze`: Analyze traffic fine history

## Production Deployment

For production deployment, consider the following modifications:

1. Replace the DeepSeek mock service with the actual DeepSeek API
2. Set up proper authentication for API endpoints
3. Configure HTTPS for secure communication
4. Implement a proper database for storing reports and user data
5. Set up monitoring and logging

## License

This project is developed for the GenAI application challenge.

## Author

Basem Torky
