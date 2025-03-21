document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the analytics page
    if (!document.getElementById('analyticsContainer')) {
        return; // Not on analytics page, skip execution
    }

    // DOM elements
    const timeRangeSelector = document.getElementById('timeRange');
    const averageRatingElement = document.getElementById('averageRating');
    const clickThroughRateElement = document.getElementById('clickThroughRate');
    const ratingCompletionElement = document.getElementById('ratingCompletion');
    const totalRecommendationsElement = document.getElementById('totalRecommendations');
    
    // Fetch analytics data
    fetchAnalyticsData();
    
    // Add event listener for time range changes
    if (timeRangeSelector) {
        timeRangeSelector.addEventListener('change', function() {
            fetchAnalyticsData(this.value);
        });
    }
    
    // Function to validate and normalize percentages
    function normalizePercentage(value) {
        // Ensure the value is a number between 0 and 100
        const numValue = Number(value);
        return (isNaN(numValue) || numValue < 0 || numValue > 100) ? 0 : numValue;
    }
    
    // Function to fetch analytics data from the server
    function fetchAnalyticsData(timeRange = 'week') {
        fetch(`/analytics-data?timeRange=${timeRange}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Validate and clean the data before updating
                const cleanedData = {
                    ...data,
                    rated_percentage: normalizePercentage(data.rated_percentage),
                    clicked_not_rated_percentage: normalizePercentage(data.clicked_not_rated_percentage),
                    not_clicked_percentage: normalizePercentage(data.not_clicked_percentage),
                    click_through_rate: normalizePercentage(data.click_through_rate),
                    rating_completion_rate: normalizePercentage(data.rating_completion_rate)
                };
                
                updateDashboard(cleanedData);
                updateUserEngagementChart(cleanedData);
                createRatingDistributionChart(cleanedData.rating_distribution);

            })
            .catch(error => {
                console.error('Error fetching analytics data:', error);
                // Display error message on the dashboard
                document.getElementById('errorMessage').textContent = 
                    'Failed to load analytics data. Please try again later.';
                document.getElementById('errorMessage').style.display = 'block';
            });
    }
    
    // Function to update dashboard metrics
    function updateDashboard(data) {
        // Update summary metrics
        if (averageRatingElement) {
            averageRatingElement.textContent = data.average_rating 
                ? data.average_rating.toFixed(1) 
                : 'N/A';
        }
        
        if (clickThroughRateElement) {
            clickThroughRateElement.textContent = data.click_through_rate 
                ? data.click_through_rate.toFixed(1) + '%' 
                : 'N/A';
        }
        
        if (ratingCompletionElement) {
            ratingCompletionElement.textContent = data.rating_completion_rate 
                ? data.rating_completion_rate.toFixed(1) + '%' 
                : 'N/A';
        }
        
        if (totalRecommendationsElement) {
            totalRecommendationsElement.textContent = data.total_recommendations 
                ? data.total_recommendations.toLocaleString() 
                : '0';
        }
        
        // Update top movies table if it exists
        const topMoviesTable = document.getElementById('topMoviesTable');
        if (topMoviesTable && data.top_rated_movies) {
            const tbody = topMoviesTable.querySelector('tbody');
            tbody.innerHTML = ''; // Clear existing rows
            
            data.top_rated_movies.forEach(movie => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${movie.title}</td>
                    <td class="text-center">${movie.average_rating.toFixed(1)}</td>
                `;
                tbody.appendChild(row);
            });
        }

    }
    
    // Function to create charts
    function createCharts(data) {
        createRatingDistributionChart(data.rating_distribution);
        createEngagementChart(data);
    }
    
    // Function to create rating distribution chart
    function createRatingDistributionChart(distribution) {
        const ctx = document.getElementById('ratingDistributionChart');
        if (!ctx || !distribution) return;
        
        // Clear any existing chart
        if (window.ratingChart) {
            window.ratingChart.destroy();
        }
        
        const labels = Object.keys(distribution).sort();
        const values = labels.map(label => distribution[label]);
        
        window.ratingChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels.map(l => l + ' Star'),
                datasets: [{
                    label: 'Percentage of Ratings',
                    data: values,
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.7)',
                        'rgba(255, 159, 64, 0.7)',
                        'rgba(255, 205, 86, 0.7)',
                        'rgba(75, 192, 192, 0.7)',
                        'rgba(54, 162, 235, 0.7)'
                    ],
                    borderColor: [
                        'rgb(255, 99, 132)',
                        'rgb(255, 159, 64)',
                        'rgb(255, 205, 86)',
                        'rgb(75, 192, 192)',
                        'rgb(54, 162, 235)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.raw.toFixed(1) + '%';
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Function to create engagement chart
    function createEngagementChart(data) {
        const ctx = document.getElementById('engagementChart');
        if (!ctx) return;
        
        // Clear any existing chart
        if (window.engagementChart) {
            window.engagementChart.destroy();
        }
        
        // Ensure percentages sum to 100%
        const totalPercentage = data.rated_percentage + 
                                data.clicked_not_rated_percentage + 
                                data.not_clicked_percentage;
        
        const normalizedData = totalPercentage > 0 
            ? [
                (data.rated_percentage / totalPercentage) * 100,
                (data.clicked_not_rated_percentage / totalPercentage) * 100,
                (data.not_clicked_percentage / totalPercentage) * 100
            ]
            : [0, 0, 0];
        
        window.engagementChart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: ['Rated', 'Clicked but not rated', 'Not clicked'],
                datasets: [{
                    data: normalizedData,
                    backgroundColor: [
                        'rgba(54, 162, 235, 0.7)',
                        'rgba(255, 205, 86, 0.7)',
                        'rgba(201, 203, 207, 0.7)'
                    ],
                    borderColor: [
                        'rgb(54, 162, 235)',
                        'rgb(255, 205, 86)',
                        'rgb(201, 203, 207)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.raw.toFixed(1) + '%';
                            }
                        }
                    }
                }
            }
        });
    }
    // Store a reference to the chart
    let engagementChart = null;

    function updateUserEngagementChart(data) {
    const ctx = document.getElementById("engagementChart").getContext("2d");
    
    // Destroy the existing chart if it exists
    if (engagementChart) {
        engagementChart.destroy();
    }
    
    // Create a new chart and store the reference
    engagementChart = new Chart(ctx, {
        type: "doughnut",
        data: {
        labels: ["Rated", "Clicked but Not Rated", "Not Clicked"],
        datasets: [{
            data: [
            data.rated_percentage,
            data.clicked_not_rated_percentage,
            data.not_clicked_percentage
            ],
            backgroundColor: ["#4CAF50", "#FF9800", "#F44336"]
        }]
        },
        options: {
        responsive: true,
        plugins: {
            legend: {
            position: "bottom"
            }
        }
        }
    });
    }

});