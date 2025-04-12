// Salama AI Assistant - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the application
    initSalamaAI();
});

// Initialize the Salama AI Assistant
function initSalamaAI() {
    // Check if we're on the results page or the main page
    const isResultsPage = document.querySelector('.summary-section');
    const isFinesPage = document.querySelector('.salama-button');
    
    if (isResultsPage) {
        // Initialize results page functionality
        initResultsPage();
    } else if (isFinesPage) {
        // Initialize button on fines page
        initSalamaButton();
    }
}

// Initialize the Salama AI button on the fines page
function initSalamaButton() {
    const salamaButton = document.querySelector('.salama-button');
    
    if (salamaButton) {
        salamaButton.addEventListener('click', function() {
            // Show loading indicator
            showLoadingIndicator();
            
            // Get user ID from the page
            const userId = getUserIdFromPage();
            
            // Call the analysis API
            fetch('/api/fines/analysis', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: userId
                })
            })
            .then(response => response.json())
            .then(data => {
                // Hide loading indicator
                hideLoadingIndicator();
                
                // Display the Salama AI Assistant results page
                displayResultsPage(data);
            })
            .catch(error => {
                console.error('Error:', error);
                hideLoadingIndicator();
                showErrorMessage();
            });
        });
    }
}

// Initialize the results page functionality
function initResultsPage() {
    // Add event listener to back button
    const backButton = document.querySelector('.back-button');
    
    if (backButton) {
        backButton.addEventListener('click', function() {
            // Navigate back to the fines page
            window.location.href = '/'; // or the appropriate URL
        });
    }
    
    // Initialize the fine history chart
    const chartContainer = document.getElementById('fine-history-chart');
    if (chartContainer) {
        // Get analysis data from the page
        const analysisDataElement = document.getElementById('analysis-data');
        if (analysisDataElement) {
            try {
                const analysisData = JSON.parse(analysisDataElement.textContent);
                createFineHistoryChart(analysisData);
            } catch (error) {
                console.error('Error parsing analysis data:', error);
                chartContainer.innerHTML = '<div style="text-align: center; padding: 50px 0;">Error loading chart data</div>';
            }
        }
    }
}

// Helper function to get user ID from the page
function getUserIdFromPage() {
    // This would need to be customized based on how the user ID is stored in the page
    // For now, we'll return a dummy ID for testing
    return '12345';
}

// Show loading indicator
function showLoadingIndicator() {
    // Create loading indicator if it doesn't exist
    if (!document.getElementById('loading-indicator')) {
        const loadingIndicator = document.createElement('div');
        loadingIndicator.id = 'loading-indicator';
        loadingIndicator.innerHTML = `
            <div class="loading-spinner"></div>
            <p>Analyzing your fine history...</p>
        `;
        loadingIndicator.style.position = 'fixed';
        loadingIndicator.style.top = '0';
        loadingIndicator.style.left = '0';
        loadingIndicator.style.width = '100%';
        loadingIndicator.style.height = '100%';
        loadingIndicator.style.backgroundColor = 'rgba(255, 255, 255, 0.8)';
        loadingIndicator.style.display = 'flex';
        loadingIndicator.style.flexDirection = 'column';
        loadingIndicator.style.alignItems = 'center';
        loadingIndicator.style.justifyContent = 'center';
        loadingIndicator.style.zIndex = '9999';
        
        // Add spinner styles
        const style = document.createElement('style');
        style.textContent = `
            .loading-spinner {
                border: 5px solid #f3f3f3;
                border-top: 5px solid #00796b;
                border-radius: 50%;
                width: 50px;
                height: 50px;
                animation: spin 2s linear infinite;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
        
        document.body.appendChild(loadingIndicator);
    } else {
        document.getElementById('loading-indicator').style.display = 'flex';
    }
}

// Hide loading indicator
function hideLoadingIndicator() {
    const loadingIndicator = document.getElementById('loading-indicator');
    if (loadingIndicator) {
        loadingIndicator.style.display = 'none';
    }
}

// Show error message
function showErrorMessage() {
    alert('Sorry, there was an error analyzing your fine history. Please try again later.');
}

// Display the results page
function displayResultsPage(data) {
    // Navigate to the results page with the user ID
    const userId = data.user_id || getUserIdFromPage();
    window.location.href = '/results?user_id=' + encodeURIComponent(userId);
}

// Function to create and update charts
function createFineHistoryChart(chartData) {
    const chartContainer = document.getElementById('fine-history-chart');
    if (!chartContainer) return;
    
    // Clear any existing chart
    chartContainer.innerHTML = '';
    
    // If no data or empty data, show a message
    if (!chartData || !chartData.total_fines || chartData.total_fines === 0) {
        chartContainer.innerHTML = '<div style="text-align: center; padding: 50px 0;">No fine history available to display</div>';
        return;
    }
    
    // Process data for chart
    const finesByMonth = {};
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    
    // Initialize all months with zero
    monthNames.forEach(month => {
        finesByMonth[month] = 0;
    });
    
    // If we have fine history data, process it
    if (chartData.fine_history && chartData.fine_history.length > 0) {
        chartData.fine_history.forEach(fine => {
            const date = new Date(fine.issue_date);
            const month = monthNames[date.getMonth()];
            finesByMonth[month]++;
        });
    }
    
    // Create chart bars
    const maxValue = Math.max(...Object.values(finesByMonth));
    const chartHeight = 160; // Maximum height for bars in pixels
    
    let chartHTML = '<div class="chart-title">Your Fine History (Last 12 Months)</div>';
    
    // Create bars for each month
    monthNames.forEach((month, index) => {
        const count = finesByMonth[month];
        const barHeight = maxValue > 0 ? (count / maxValue) * chartHeight : 0;
        const leftPosition = 40 + (index * 70); // Position bars evenly
        
        chartHTML += `
            <div class="chart-bar" style="height: ${barHeight}px; left: ${leftPosition}px;"></div>
            <div class="chart-label" style="left: ${leftPosition}px;">${month}</div>
        `;
    });
    
    // Add chart to container
    chartContainer.innerHTML = chartHTML;
}