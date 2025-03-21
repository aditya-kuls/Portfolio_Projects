document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const userIdInput = document.getElementById('userId');
    const getRecommendationsBtn = document.getElementById('getRecommendations');
    const recommendationsContainer = document.getElementById('recommendationsContainer');
    const recommendationsList = document.getElementById('recommendations');
    const loadingElement = document.getElementById('loading');
    const errorMessage = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');

    // User feedback data storage
    let currentUserId = '';
    let userRatings = [];

    // Event Listeners
    getRecommendationsBtn.addEventListener('click', fetchRecommendations);
    userIdInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            fetchRecommendations();
        }
    });

    // Function to fetch recommendations from the API
    function fetchRecommendations() {
        const userId = userIdInput.value.trim();
        currentUserId = userId; // Store current user ID for ratings
        
        // Validate input
        if (!userId) {
            showError('Please enter a User ID');
            return;
        }
        
        // Clear previous results and show loading spinner
        recommendationsList.innerHTML = '';
        recommendationsContainer.style.display = 'none';
        errorMessage.style.display = 'none';
        loadingElement.style.display = 'block';
        
        // Fetch recommendations from the API
        fetch(`/recommendations/${userId}`)
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || 'Failed to get recommendations');
                    });
                }
                return response.json();
            })
            .then(data => {
                // Display recommendations
                displayRecommendations(data);
                loadingElement.style.display = 'none';
                recommendationsContainer.style.display = 'block';
                
                // Log telemetry for recommendations shown
                logTelemetry('recommendations_shown', {
                    user_id: userId,
                    count: data.recommendations.length,
                    recommendation_ids: data.recommendations.map(r => r.movie_name)
                });
            })
            .catch(error => {
                loadingElement.style.display = 'none';
                showError(error.message);
                
                // Log telemetry for error
                logTelemetry('recommendation_error', {
                    user_id: userId,
                    error_message: error.message
                });
            });
    }

    // Function to display recommendations with rating UI
    function displayRecommendations(data) {
        if (!data.recommendations || data.recommendations.length === 0) {
            showError('No recommendations found for this user');
            return;
        }
        
        // Create a movie card for each recommendation
        data.recommendations.forEach((movie, index) => {
            const movieName = movie.movie_name;
            // Extract year if present (assuming format: "movie title year")
            let title = movieName;
            let year = '';
            
            // Try to extract year from the end of the movie name
            const yearMatch = movieName.match(/\s(\d{4})$/);
            if (yearMatch) {
                title = movieName.substring(0, yearMatch.index);
                year = yearMatch[1];
            }
            
            // Create movie card element
            const movieCard = document.createElement('div');
            movieCard.className = 'movie-card';
            movieCard.dataset.movieName = movieName;
            movieCard.dataset.index = index;
            
            // Create movie info section
            const infoDiv = document.createElement('div');
            infoDiv.className = 'movie-info';
            
            // Create and add title
            const titleElement = document.createElement('h3');
            titleElement.className = 'movie-title';
            titleElement.textContent = title.charAt(0).toUpperCase() + title.slice(1);
            
            // Create and add year if present
            const yearElement = document.createElement('p');
            yearElement.className = 'movie-year';
            yearElement.textContent = year ? `(${year})` : '';
            
            // Create poster placeholder (empty, as requested)
            const posterDiv = document.createElement('div');
            posterDiv.className = 'movie-poster';
            
            // Create rating overlay
            const ratingOverlay = document.createElement('div');
            ratingOverlay.className = 'movie-rating-overlay';
            
            // Add content to rating overlay
            ratingOverlay.innerHTML = `
                <h4>Did you watch "${title}"?</h4>
                <p>Let us know how you liked it!</p>
                <div class="rating-stars" data-movie="${movieName}">
                    <i class="star fas fa-star" data-rating="1"></i>
                    <i class="star fas fa-star" data-rating="2"></i>
                    <i class="star fas fa-star" data-rating="3"></i>
                    <i class="star fas fa-star" data-rating="4"></i>
                    <i class="star fas fa-star" data-rating="5"></i>
                </div>
                <div class="feedback-buttons">
                    <button class="feedback-btn yes-btn" data-watched="yes">I've watched it</button>
                    <button class="feedback-btn no-btn" data-watched="no">Haven't seen it</button>
                </div>
                <div class="rating-status"></div>
            `;
            
            // Assemble the card
            infoDiv.appendChild(titleElement);
            if (year) {
                infoDiv.appendChild(yearElement);
            }
            
            movieCard.appendChild(posterDiv);
            movieCard.appendChild(infoDiv);
            movieCard.appendChild(ratingOverlay);
            
            // Add to recommendations list
            recommendationsList.appendChild(movieCard);
            
            // Add click event to the movie card to show rating overlay
            movieCard.addEventListener('click', function() {
                // Toggle the rating overlay visibility
                if (ratingOverlay.style.opacity === '1') {
                    ratingOverlay.style.opacity = '0';
                    ratingOverlay.style.visibility = 'hidden';
                } else {
                    ratingOverlay.style.opacity = '1';
                    ratingOverlay.style.visibility = 'visible';
                }
                
                // Log telemetry for movie card click
                logTelemetry('movie_card_clicked', {
                    user_id: currentUserId,
                    movie_name: movieName
                });
            });
            
            // Add event listeners for star ratings
            setupRatingListeners(movieCard, ratingOverlay);
        });
    }

    // Function to setup rating event listeners
    function setupRatingListeners(movieCard, ratingOverlay) {
        const stars = movieCard.querySelectorAll('.star');
        const statusElement = movieCard.querySelector('.rating-status');
        const feedbackButtons = movieCard.querySelectorAll('.feedback-btn');
        
        // Star rating functionality
        stars.forEach(star => {
            star.addEventListener('click', function(e) {
                e.stopPropagation(); // Prevent card click event from firing
                const rating = parseInt(this.dataset.rating);
                const movieName = this.parentNode.dataset.movie;
                
                // Visual feedback - highlight stars
                stars.forEach(s => {
                    const starRating = parseInt(s.dataset.rating);
                    if (starRating <= rating) {
                        s.classList.add('selected');
                    } else {
                        s.classList.remove('selected');
                    }
                });
                
                // Submit the rating
                submitRating(movieName, rating);
                statusElement.textContent = 'Thanks for your rating!';
                
                // Log telemetry
                logTelemetry('movie_rated', {
                    user_id: currentUserId,
                    movie_name: movieName,
                    rating: rating
                });
                
                // Hide overlay after a delay
                setTimeout(() => {
                    ratingOverlay.style.opacity = '0';
                    ratingOverlay.style.visibility = 'hidden';
                }, 2000);
            });
        });
        
        // Watched/Not watched buttons
        feedbackButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.stopPropagation(); // Prevent card click event from firing
                const watched = this.dataset.watched;
                const movieName = movieCard.dataset.movieName;
                
                if (watched === 'yes') {
                    // Show the rating stars more prominently
                    statusElement.textContent = 'Please rate the movie with stars above!';
                } else {
                    // Log that user hasn't seen it
                    submitRating(movieName, 0, false);
                    statusElement.textContent = 'Thanks for letting us know!';
                    
                    // Log telemetry
                    logTelemetry('movie_not_watched', {
                        user_id: currentUserId,
                        movie_name: movieName
                    });
                    
                    // Hide overlay after a delay
                    setTimeout(() => {
                        ratingOverlay.style.opacity = '0';
                        ratingOverlay.style.visibility = 'hidden';
                    }, 2000);
                }
            });
        });
        
        // Close overlay when clicking outside
        document.addEventListener('click', function(e) {
            if (!movieCard.contains(e.target)) {
                ratingOverlay.style.opacity = '0';
                ratingOverlay.style.visibility = 'hidden';
            }
        });
    }

    // Function to submit rating to the server
    function submitRating(movieName, rating, watched = true) {
        const ratingData = {
            user_id: currentUserId,
            movie_name: movieName,
            rating: rating,
            watched: watched,
            timestamp: new Date().toISOString()
        };
        
        // Add to local collection
        userRatings.push(ratingData);
        
        // Send to server
        fetch('/submit-rating', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(ratingData)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Rating submitted successfully:', data);
        })
        .catch(error => {
            console.error('Error submitting rating:', error);
        });
    }

    // Telemetry logging function
    function logTelemetry(eventName, data) {
        const telemetryData = {
            event: eventName,
            timestamp: new Date().toISOString(),
            ...data
        };
        
        // Send telemetry to backend
        fetch('/log-telemetry', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(telemetryData)
        })
        .catch(error => {
            console.error('Error logging telemetry:', error);
        });
        
        // Also log to console for debugging
        console.log('Telemetry:', telemetryData);
    }

    // Function to show error messages
    function showError(message) {
        errorText.textContent = message;
        errorMessage.style.display = 'block';
    }
});