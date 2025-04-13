import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import hashlib
import time
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
from functools import lru_cache
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
CORS(app)

# Database connection pool configuration
db_config = {
    'host': os.environ.get('DB_HOST', 'db'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', 'example'),
    'database': os.environ.get('DB_NAME', 'traffic_safety'),
    'port': int(os.environ.get('DB_PORT', 3306))
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'salama-ai-assistant-secret-key')
app.config['DEBUG'] = True

# Ollama API configuration
OLLAMA_API_URL = os.environ.get('OLLAMA_API_URL', "http://100.69.25.25:11434/api/generate")
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', "llama3.1:latest")


# Cache configuration
CACHE_TIMEOUT = 3600  # 1 hour

# Helper function to get user's fine history
def get_user_fine_history(user_id):
    connection = get_db_connection()
    if not connection:
        # Return mock data when database is unavailable
        print("Database unavailable, returning mock fine history data")
        return get_mock_fine_history(user_id)
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
        SELECT * FROM traffic_fines 
        WHERE user_id = %s 
        ORDER BY issue_date DESC
        """
        cursor.execute(query, (user_id,))
        fine_history = cursor.fetchall()
        return fine_history
    except Error as e:
        print(f"Error retrieving fine history: {e}")
        # Return mock data on error
        return get_mock_fine_history(user_id)
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            
# Function to generate mock fine history data for testing
def get_mock_fine_history(user_id):
    from datetime import datetime, timedelta
    import random
    
    # Sample violation types
    violation_types = [
        "Exceeding maximum speed limit",
        "Parking violation",
        "Using phone while driving",
        "Not wearing seatbelt",
        "Running a red light"
    ]
    
    # Sample locations
    locations = [
        "Sheikh Mohammad Bin Zayed Road",
        "Sheikh Zayed Road",
        "Al Khail Road",
        "Emirates Road",
        "Dubai-Al Ain Road"
    ]
    
    # Generate 5-10 random fines
    num_fines = random.randint(5, 10)
    mock_fines = []
    
    for i in range(num_fines):
        # Random date within the last year
        days_ago = random.randint(1, 365)
        fine_date = datetime.now() - timedelta(days=days_ago)
        
        # Random fine amount between 100 and 1000
        amount = random.randint(10, 100) * 10
        
        mock_fines.append({
            'id': i + 1,
            'user_id': user_id,
            'violation_details': random.choice(violation_types),
            'location': random.choice(locations),
            'amount': amount,
            'issue_date': fine_date,
            'status': 'Unpaid' if random.random() > 0.3 else 'Paid'
        })
    
    # Sort by date (newest first)
    mock_fines.sort(key=lambda x: x['issue_date'], reverse=True)
    return mock_fines

# Function to identify time patterns in fine data
def identify_time_patterns(df):
    if df.empty or 'hour' not in df.columns:
        return None
    
    # Group by hour and count occurrences
    hour_counts = df['hour'].value_counts()
    
    if hour_counts.empty:
        return None
    
    peak_hour = hour_counts.idxmax()
    peak_count = hour_counts.max()
    
    # Check if there's a significant pattern
    if peak_count >= 2 and peak_count / len(df) >= 0.3:  # At least 30% of fines
        return {
            'peak_hour': peak_hour,
            'peak_count': int(peak_count),
            'percentage': round(peak_count / len(df) * 100, 1)
        }
    
    return None

# Function to identify location patterns in fine data
def identify_location_patterns(df):
    if df.empty or 'location' not in df.columns:
        return None
    
    # Group by location and count occurrences
    location_counts = df['location'].value_counts()
    
    if location_counts.empty:
        return None
    
    common_location = location_counts.idxmax()
    location_count = location_counts.max()
    
    # Check if there's a significant pattern
    if location_count >= 2 and location_count / len(df) >= 0.3:  # At least 30% of fines
        return {
            'common_location': common_location,
            'location_count': int(location_count),
            'percentage': round(location_count / len(df) * 100, 1)
        }
    
    return None

# Function to analyze severity trend in fine data
def analyze_severity_trend(df):
    if df.empty or 'amount' not in df.columns or 'issue_date' not in df.columns:
        return None
    
    # Sort by date
    df = df.sort_values('issue_date')
    
    # Check if there are enough fines to analyze trend
    if len(df) < 2:
        return None
    
    # Calculate trend
    amounts = df['amount'].tolist()
    first_half_avg = sum(amounts[:len(amounts)//2]) / (len(amounts)//2) if len(amounts)//2 > 0 else 0
    second_half_avg = sum(amounts[len(amounts)//2:]) / (len(amounts) - len(amounts)//2) if (len(amounts) - len(amounts)//2) > 0 else 0
    
    if second_half_avg > first_half_avg * 1.2:  # 20% increase
        return 'increasing'
    elif first_half_avg > second_half_avg * 1.2:  # 20% decrease
        return 'decreasing'
    else:
        return 'stable'

# Function to convert numpy types to Python native types
def convert_numpy_types(obj):
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(i) for i in obj]
    else:
        return obj

# Function to analyze fine patterns
def analyze_fine_patterns(fine_history):
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(fine_history)
    
    if df.empty:
        return {
            'total_fines': 0,
            'total_amount': 0,
            'most_common_violation': None,
            'time_pattern': None,
            'location_pattern': None,
            'severity_trend': None
        }
    
    # Identify common violation types
    violation_counts = df['violation_details'].value_counts() if 'violation_details' in df.columns else pd.Series()
    most_common = violation_counts.index[0] if len(violation_counts) > 0 else None
    
    # Analyze time patterns
    if 'issue_date' in df.columns:
        df['issue_date'] = pd.to_datetime(df['issue_date'])
        df['hour'] = df['issue_date'].dt.hour
        time_pattern = identify_time_patterns(df)
    else:
        time_pattern = None
    
    # Analyze location patterns
    location_pattern = identify_location_patterns(df)
    
    # Analyze severity trend
    severity_trend = analyze_severity_trend(df)
    
    # Get common violations (top 3)
    common_violations = []
    if len(violation_counts) > 0:
        for violation, count in violation_counts.items():
            if len(common_violations) < 3:  # Limit to top 3
                common_violations.append({
                    'violation': violation,
                    'count': int(count),
                    'percentage': round(count / len(df) * 100, 1)
                })
    
    return {
        'total_fines': len(df),
        'total_amount': float(df['amount'].sum()) if 'amount' in df.columns else 0,
        'most_common_violation': most_common,
        'common_violations': common_violations,
        'time_pattern': time_pattern,
        'location_pattern': location_pattern,
        'severity_trend': severity_trend
    }

# Function to get location-specific advice
def get_location_specific_advice(location):
    # Map of common locations to specific advice
    location_advice = {
        'Sheikh Mohammad Bin Zayed Road': 'This road has multiple speed cameras and varying speed limits. Consider using cruise control to maintain a consistent speed, especially in the sections near interchanges where speed limits may change.',
        'Sheikh Zayed Road': 'This is one of Dubai\'s busiest roads. Maintain safe distance from vehicles ahead and be cautious of sudden lane changes by other drivers.',
        'Al Khail Road': 'This road has several construction zones. Pay attention to temporary speed limit signs and lane closures.',
        'Emirates Road': 'This highway has a high rate of accidents. Maintain the speed limit and avoid distractions while driving.',
        'Dubai-Al Ain Road': 'This road experiences heavy truck traffic. Be cautious when changing lanes and maintain extra distance when following trucks.',
        'Hessa Street': 'This road has multiple school zones. Be extra cautious during school hours and watch for reduced speed limits.',
        'Jumeirah Beach Road': 'This road has heavy pedestrian traffic. Drive slowly and be vigilant for pedestrians crossing.',
        'Business Bay Crossing': 'This area experiences heavy congestion during peak hours. Plan your journey to avoid rush hours if possible.'
    }
    
    # Return specific advice if available, otherwise generic advice
    return location_advice.get(location, f"Pay extra attention when driving on {location} as you've received multiple fines in this area.")

# Function to get time-specific advice
def get_time_specific_advice(hour):
    # Map of hours to specific advice
    time_advice = {
        # Morning rush hour
        7: 'This is morning rush hour. Leave earlier to avoid the temptation to speed due to time pressure.',
        8: 'This is peak morning commute time. Plan for traffic delays to reduce stress and avoid speeding.',
        9: 'Late morning rush can still be busy. Allow extra time for your journey.',
        # Midday
        12: 'Lunchtime traffic can be unpredictable. Be cautious of pedestrians and delivery vehicles.',
        13: 'Early afternoon is often when people rush back to work after lunch. Take your time and avoid the rush.',
        14: 'School pickup times begin around this hour. Be extra vigilant near schools and residential areas.',
        # Evening rush hour
        17: 'This is peak evening rush hour. Consider adjusting your schedule to travel outside this busy period.',
        18: 'Evening commute is still heavy at this hour. Practice patience and maintain safe distances.',
        19: 'Late evening commute can lead to fatigue. Ensure you are alert and take breaks if needed.',
        # Late night
        23: 'Late night driving requires extra vigilance. Watch for reduced visibility and be aware of fatigue.',
        0: 'Midnight driving poses risks from fatigue and reduced visibility. Consider if your journey is necessary.',
        1: 'Early morning hours have higher risks of encountering impaired drivers. Stay extra alert.'
    }
    
    # Return specific advice if available, otherwise generic advice based on time period
    if hour in time_advice:
        return time_advice[hour]
    elif 5 <= hour <= 9:
        return 'Morning commute times require extra attention. Plan your journey to allow for traffic delays.'
    elif 16 <= hour <= 19:
        return 'Evening rush hour requires patience and attention. Consider adjusting your schedule to avoid peak traffic times.'
    elif 22 <= hour or hour <= 4:
        return 'Night driving requires extra caution due to reduced visibility and potential fatigue. Ensure you are well-rested.'
    else:
        return 'Consider adjusting your schedule to allow for extra travel time during this hour to avoid the temptation to speed.'

# Function to generate safety tips based on analysis
def generate_safety_tips(analysis_result, user_profile=None):
    tips = []
    
    # Generate tips based on most common violations
    if analysis_result['most_common_violation'] == 'Exceeding maximum speed limit':
        tips.append({
            'title': 'Speed Management',
            'description': 'Consider using cruise control on highways to maintain consistent speed. Remember that the displayed speed limit already includes the 20 km/h buffer in Dubai, so exceeding it will result in immediate fines.',
            'category': 'speeding'
        })
    elif analysis_result['most_common_violation'] == 'Parking violation':
        tips.append({
            'title': 'Parking Guidelines',
            'description': 'Use the RTA parking app to pay for parking and set reminders before your parking time expires. Look for clear signage indicating parking restrictions before leaving your vehicle.',
            'category': 'parking'
        })
    elif analysis_result['most_common_violation'] == 'Using phone while driving':
        tips.append({
            'title': 'Distraction Prevention',
            'description': 'Put your phone in Do Not Disturb mode while driving or use a phone mount if you need navigation. Remember that even checking your phone at a red light is considered a violation in Dubai.',
            'category': 'distraction'
        })
    
    # Generate location-specific tips
    if analysis_result['location_pattern']:
        location = analysis_result['location_pattern']['common_location']
        tips.append({
            'title': f'Safety on {location}',
            'description': get_location_specific_advice(location),
            'category': 'location'
        })
    
    # Generate time-specific tips
    if analysis_result['time_pattern']:
        peak_hour = analysis_result['time_pattern']['peak_hour']
        tips.append({
            'title': 'Time Management for Safer Driving',
            'description': get_time_specific_advice(peak_hour),
            'category': 'time_management'
        })
    
    # Generate severity trend tips
    if analysis_result['severity_trend'] == 'increasing':
        tips.append({
            'title': 'Increasing Fine Severity Alert',
            'description': 'Your fine amounts are increasing over time, which may indicate escalating violations. Consider enrolling in a defensive driving course to improve your driving habits and avoid more serious penalties.',
            'category': 'trend'
        })
    
    # Add general tip if no specific tips were generated
    if not tips:
        tips.append({
            'title': 'Safe Driving Practices',
            'description': 'Maintain a safe distance from vehicles ahead, use indicators when changing lanes, and regularly check your vehicle\'s condition to ensure safety on the road.',
            'category': 'general'
        })
    
    # Add RTA Smart Driver Program tip if multiple fines
    if analysis_result['total_fines'] >= 3:
        tips.append({
            'title': 'RTA Smart Driver Program',
            'description': 'Based on your fine history, you may benefit from the RTA Smart Driver Program which offers personalized coaching for drivers with multiple violations. Completing this program can improve your driving habits and may make you eligible for reduced insurance premiums.',
            'category': 'program'
        })
    
    return tips

# Function to generate insights using Ollama API
def generate_insights(analysis_result):
    if not analysis_result or analysis_result['total_fines'] == 0:
        return "No fine history available to generate insights."
    
    def get_fallback_insights(analysis):
        try:
            # Validate analysis data
            if not analysis or not isinstance(analysis, dict):
                return "Based on your driving history, we'll provide personalized safety recommendations once all your fine details are processed."
            
            insights = []
            
            # Add violation-specific insights with proper null checks
            most_common_violation = analysis.get('most_common_violation')
            if most_common_violation:
                violation_insights = {
                    'Exceeding maximum speed limit': "Your most frequent violation is speeding. Consider using cruise control and leaving earlier to avoid rushing.",
                    'Parking violation': "Parking violations are your main concern. Always check for parking signs and use the RTA parking app.",
                    'Using phone while driving': "Phone usage while driving is your primary violation. Enable 'Do Not Disturb' mode for safer driving."
                }
                if insight := violation_insights.get(most_common_violation):
                    insights.append(insight)
            
            # Add pattern-based insights with safe dictionary access
            time_pattern = analysis.get('time_pattern', {})
            if isinstance(time_pattern, dict) and 'peak_hour' in time_pattern:
                insights.append(f"Most violations occur around {time_pattern['peak_hour']}:00. Consider adjusting your schedule.")
            
            location_pattern = analysis.get('location_pattern', {})
            if isinstance(location_pattern, dict) and 'common_location' in location_pattern:
                insights.append(f"Exercise extra caution on {location_pattern['common_location']}, where multiple violations occurred.")
            
            # Add severity trend insights with safe access
            if analysis.get('severity_trend') == 'increasing':
                insights.append("Your fine amounts show an increasing trend. Consider reviewing your driving habits.")
            
            # Return combined insights or default message
            return " ".join(insights) if insights else "Drive safely by following traffic rules and maintaining awareness of your surroundings. Regular self-assessment of driving habits helps prevent violations."
                
        except Exception as e:
            print(f"Error generating fallback insights: {e}")
            return "Stay safe on the roads. Follow traffic rules and maintain regular checks of your driving record."
    
    try:
        # Create a prompt for the Ollama model
        prompt = f"""Based on the following traffic fine analysis, provide 2-3 personalized safety insights in a friendly, helpful tone:
        
        Total Fines: {analysis_result['total_fines']}
        Total Amount: AED {analysis_result['total_amount']}
        Most Common Violation: {analysis_result['most_common_violation'] or 'None'}
        Severity Trend: {analysis_result['severity_trend'] or 'Stable'}
        
        Time Pattern: {analysis_result['time_pattern'] if analysis_result['time_pattern'] else 'No significant time pattern'}
        Location Pattern: {analysis_result['location_pattern'] if analysis_result['location_pattern'] else 'No significant location pattern'}
        
        Format the response as a paragraph addressing the driver directly with practical advice.
        """
        
        # Call Ollama API
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('response', get_fallback_insights(analysis_result))
        else:
            print(f"Error from Ollama API: {response.status_code} - {response.text}")
            return get_fallback_insights(analysis_result)
    
    except Exception as e:
        print(f"Exception when calling Ollama API: {e}")
        return get_fallback_insights(analysis_result)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/results')
def results():
    # Get user_id from query parameter
    user_id = request.args.get('user_id', '12345')  # Default to a test user ID if not provided
    
    # Retrieve user's fine history
    fine_history = get_user_fine_history(user_id)
    
    # Perform analysis
    analysis_result = analyze_fine_patterns(fine_history)
    
    # Generate personalized insights
    insights = generate_insights(analysis_result)
    
    # Generate safety tips
    safety_tips = generate_safety_tips(analysis_result)
    
    return render_template('results.html', 
                          analysis=analysis_result, 
                          insights=insights, 
                          safety_tips=safety_tips, 
                          fine_history=fine_history)

@app.route('/api/fines/history', methods=['POST'])
def get_fines_history():
    # Check if request contains JSON data
    if not request.is_json:
        return jsonify({'error': 'Invalid request format. JSON required'}), 400
        
    user_id = request.json.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    fine_history = get_user_fine_history(user_id)
    
    # Convert numpy types to Python native types for JSON serialization
    serializable_result = convert_numpy_types({
        'fine_history': fine_history
    })
    
    return jsonify(serializable_result)

@app.route('/api/fines/analysis', methods=['POST'])
def analyze_fines():
    try:
        # Check if request contains JSON data
        if not request.is_json:
            return jsonify({'error': 'Invalid request format. JSON required'}), 400
            
        user_id = request.json.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        # Retrieve user's fine history
        fine_history = get_user_fine_history(user_id)
        if fine_history is None:
            return jsonify({'error': 'Failed to retrieve fine history. Database connection error.'}), 500
        
        # Perform analysis
        analysis_result = analyze_fine_patterns(fine_history)
        
        # Generate personalized insights
        insights = generate_insights(analysis_result)
        
        # Generate safety tips
        safety_tips = generate_safety_tips(analysis_result)
        
        # Convert numpy types to Python native types for JSON serialization
        serializable_result = convert_numpy_types({
            'analysis': analysis_result,
            'insights': insights,
            'safety_tips': safety_tips,
            'fine_history': fine_history,
            'user_id': user_id
        })
        
        return jsonify(serializable_result)
    except Exception as e:
        print(f"Error in analyze_fines: {str(e)}")
        return jsonify({'error': 'An internal server error occurred'}), 500

@app.route('/api/safety/tips', methods=['POST'])
def get_safety_tips():
    # Check if request contains JSON data
    if not request.is_json:
        return jsonify({'error': 'Invalid request format. JSON required'}), 400
        
    user_id = request.json.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    # Retrieve user's fine history
    fine_history = get_user_fine_history(user_id)
    
    # Perform analysis
    analysis_result = analyze_fine_patterns(fine_history)
    
    # Generate safety tips
    safety_tips = generate_safety_tips(analysis_result)
    
    # Convert numpy types to Python native types for JSON serialization
    serializable_result = convert_numpy_types({
        'safety_tips': safety_tips
    })
    
    return jsonify(serializable_result)

@app.route('/api/stats/summary', methods=['POST'])
def get_stats_summary():
    # Check if request contains JSON data
    if not request.is_json:
        return jsonify({'error': 'Invalid request format. JSON required'}), 400
        
    user_id = request.json.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    
    # Retrieve user's fine history
    fine_history = get_user_fine_history(user_id)
    
    # Perform analysis
    analysis_result = analyze_fine_patterns(fine_history)
    
    # Convert numpy types to Python native types for JSON serialization
    serializable_result = convert_numpy_types({
        'summary': analysis_result
    })
    
    return jsonify(serializable_result)

# Admin routes for backoffice
@app.route('/admin')
def admin_dashboard():
    connection = get_db_connection()
    if not connection:
        return render_template('admin/dashboard.html', total_fines=0, total_users=0, total_amount=0, error="Database connection failed")
    
    # Add your admin dashboard logic here
    return render_template('admin/dashboard.html')

# Run the application
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8002))
    app.run(host='0.0.0.0', port=port, debug=False)

# Main entry point
if __name__ == '__main__':
    # Create database tables if they don't exist
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            # Create traffic_fines table if it doesn't exist
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS traffic_fines (
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
            )
            """)
            
            connection.commit()
            print("Database tables created successfully")
        except Error as e:
            print(f"Error creating database tables: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
# Initialize database tables
def initialize_database():
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            # Create traffic_fines table if it doesn't exist
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS traffic_fines (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(50) NOT NULL,
                vehicle_info VARCHAR(255),
                issue_date DATETIME NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                source VARCHAR(100),
                black_points INT DEFAULT 0,
                location VARCHAR(255) NOT NULL,
                violation_details TEXT NOT NULL,
                fine_number VARCHAR(50),
                status VARCHAR(50) DEFAULT 'Unpaid',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_user_id (user_id),
                INDEX idx_issue_date (issue_date)
            )
            """)
            
            connection.commit()
            print("Database tables created successfully")
            return True
        except Error as e:
            print(f"Error creating database tables: {e}")
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    else:
        print("Could not connect to database for initialization. Will use mock data.")
        return False

# Initialize database when the application starts
initialize_database()

# Add a health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    db_status = "connected" if get_db_connection() else "disconnected"
    return jsonify({
        'status': 'ok',
        'database': db_status,
        'version': '1.0.0'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8002))
    app.run(host='0.0.0.0', port=port, debug=False)


def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'root'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'traffic_safety'),
            port=int(os.environ.get('DB_PORT', 3306))
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL Database: {e}")
        return None