document.addEventListener('DOMContentLoaded', function() {
    const dropArea = document.getElementById('dropArea');
    const fileInput = document.getElementById('fileInput');
    const browseButton = document.getElementById('browseButton');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const removeFile = document.getElementById('removeFile');
    const jobDescription = document.getElementById('jobDescription');
    const analyzeButton = document.getElementById('analyzeButton');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const resultsContainer = document.getElementById('resultsContainer');
    
    let selectedFile = null;
    let matchChart = null;

    // Ensure loading overlay is hidden initially
    loadingOverlay.classList.add('hidden');

    // Initialize disabled state of analyze button
    updateAnalyzeButtonState();

    // Event listeners for drag and drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });

    function highlight() {
        dropArea.classList.add('active');
    }

    function unhighlight() {
        dropArea.classList.remove('active');
    }

    dropArea.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length) {
            handleFiles(files[0]);
        }
    }

    browseButton.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleFiles(e.target.files[0]);
        }
    });

    removeFile.addEventListener('click', () => {
        selectedFile = null;
        fileInput.value = '';
        fileInfo.classList.add('hidden');
        updateAnalyzeButtonState();
    });

    jobDescription.addEventListener('input', updateAnalyzeButtonState);

    function handleFiles(file) {
        const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
        
        if (!validTypes.includes(file.type)) {
            alert('Please upload a PDF or DOCX file');
            return;
        }
        
        selectedFile = file;
        fileName.textContent = file.name;
        fileInfo.classList.remove('hidden');
        updateAnalyzeButtonState();
    }

    function updateAnalyzeButtonState() {
        if (selectedFile && jobDescription.value.trim() !== '') {
            analyzeButton.disabled = false;
        } else {
            analyzeButton.disabled = true;
        }
    }

    analyzeButton.addEventListener('click', async () => {
        if (!selectedFile || jobDescription.value.trim() === '') {
            return;
        }

        // Show loading overlay
        loadingOverlay.classList.remove('hidden');
        
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('job_description', jobDescription.value);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            displayResults(data);
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while analyzing your resume. Please try again.');
        } finally {
            // Hide loading overlay when done
            loadingOverlay.classList.add('hidden');
        }
    });

    async function displayResults(data) {
        // Extract the first item from the array response
        const result = data[0];
        
        // Parse the match score from the JobDescriptionMatch field
        const matchScore = parseInt(result.JobDescriptionMatch) || 0;
    
        // Build the bullet list for Missing Keywords
        const missingKeywordsHTML = result.MissingKeywords
            .map(keyword => `<li>${keyword}</li>`)
            .join('');
        document.getElementById('missingKeywords').innerHTML = `<ol>${missingKeywordsHTML}</ol>`;
    
        // Build the bullet list for Personalized Suggestions
        const suggestionsHTML = result.PersonalizedSuggestions
            .map(suggestion => `<li>${suggestion}</li>`)
            .join('');
        document.getElementById('suggestions').innerHTML = `<ol>${suggestionsHTML}</ol>`;
    
        // Update other UI elements
        document.getElementById('matchDescription').innerHTML = result.JobDescriptionMatch;
        document.getElementById('matchScore').textContent = `${matchScore}%`;
        document.getElementById('profileSummary').innerHTML = result.ProfileSummary;
        document.getElementById('successRate').innerHTML = result.ApplicationSuccessRate;
    
        // Show the results container
        resultsContainer.classList.remove('hidden');
    
        // Animate result cards
        const resultCards = document.querySelectorAll('.result-card');
        resultCards.forEach((card, index) => {
            setTimeout(() => {
                card.classList.add('show');
            }, 100 * index);
        });
    
        // Draw the match score chart
        drawMatchChart(matchScore);
    
        // Scroll to results
        resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    

    function drawMatchChart(score) {
        const ctx = document.getElementById('matchChart').getContext('2d');
        
        // If chart already exists, destroy it
        if (matchChart) {
            matchChart.destroy();
        }
        
        // Create new chart
        matchChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [score, 100 - score],
                    backgroundColor: [
                        getScoreColor(score),
                        '#e5e7eb'
                    ],
                    borderWidth: 0,
                    cutout: '75%'
                }]
            },
            options: {
                responsive: false,
                maintainAspectRatio: false,
                plugins: {
                    tooltip: {
                        enabled: false
                    },
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    function getScoreColor(score) {
        if (score >= 80) return '#10B981'; // Green for excellent
        if (score >= 60) return '#F59E0B'; // Amber for good
        return '#EF4444'; // Red for poor
    }
});