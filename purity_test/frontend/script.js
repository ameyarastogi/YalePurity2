const API_ENDPOINT = 'https://nls3ehrs7h.execute-api.us-east-1.amazonaws.com/prod'; // Replace with your actual API endpoint
const NUM_QUESTIONS = 10; // Using 10 questions for this example

// Function to load questions dynamically on quiz.html
function loadQuestions() {
    const questionsDiv = document.getElementById('questions');
    if (questionsDiv) {
        for (let i = 0; i < NUM_QUESTIONS; i++) {
            const questionDiv = document.createElement('div');
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `q${i}`;
            checkbox.name = `q${i}`;
            checkbox.value = 'true';

            const label = document.createElement('label');
            label.htmlFor = `q${i}`;
            label.textContent = `Question ${i + 1}: Have you done this example activity?`; // Replace with actual questions

            questionDiv.appendChild(checkbox);
            questionDiv.appendChild(label);
            questionsDiv.appendChild(questionDiv);
        }
    }
}

// Function to handle quiz submission
async function submitQuiz(event) {
    event.preventDefault();

    const form = document.getElementById('quiz-form');
    const formData = new FormData(form);

    const demographics = {
        year: formData.get('year'),
        college: formData.get('college') || null,
        gender: formData.get('gender') || null,
        social_club: formData.get('social_club') || null,
    };

    const answers = [];
    for (let i = 0; i < NUM_QUESTIONS; i++) {
        answers.push(formData.has(`q${i}`));
    }

    const submissionData = {
        demographics: demographics,
        answers: {
            answers: answers
        }
    };

    try {
        const response = await fetch(`${API_ENDPOINT}/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(submissionData),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        console.log('Submission successful:', result);

        // Store submission ID and redirect to results page
        sessionStorage.setItem('submissionId', result.id);
        window.location.href = 'results.html';

    } catch (error) {
        console.error('Error submitting quiz:', error);
        alert('There was an error submitting your quiz. Please try again.');
    }
}

// Function to load results on results.html
async function loadResults() {
    const submissionId = sessionStorage.getItem('submissionId');
    if (!submissionId) {
        alert('No submission ID found. Please submit the quiz first.');
        window.location.href = 'quiz.html';
        return;
    }

    document.getElementById('submission-id').textContent = submissionId;

    try {
        const response = await fetch(`${API_ENDPOINT}/stats/${submissionId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const stats = await response.json();
        console.log('Stats received:', stats);

        document.getElementById('score').textContent = stats.score;
        document.getElementById('percentile').textContent = stats.percentile ? stats.percentile.toFixed(1) : 'N/A';

        // Populate question stats
        const questionStatsList = document.getElementById('question-stats');
        if (stats.question_stats && questionStatsList) {
            questionStatsList.innerHTML = ''; // Clear previous stats
            for (let i = 0; i < NUM_QUESTIONS; i++) {
                const percentage = stats.question_stats[i] !== undefined ? stats.question_stats[i].toFixed(1) : 'N/A';
                const li = document.createElement('li');
                li.textContent = `Question ${i + 1}: ${percentage}% said Yes`;
                questionStatsList.appendChild(li);
            }
        }

        // Populate score distribution chart
        if (stats.distribution) {
            renderScoreChart(stats.distribution);
        }

    } catch (error) {
        console.error('Error fetching stats:', error);
        alert('There was an error fetching your results.');
    }
}

// Function to render the score distribution chart
function renderScoreChart(distribution) {
    const ctx = document.getElementById('scoreChart').getContext('2d');
    
    // Prepare data for Chart.js
    const labels = Object.keys(distribution).sort(); // Sort buckets (e.g., "0-9", "10-19")
    const data = labels.map(label => distribution[label]);

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Number of Submissions',
                data: data,
                backgroundColor: 'rgba(0, 53, 107, 0.6)', // Yale Blue with transparency
                borderColor: 'rgba(0, 53, 107, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Frequency'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Score Range'
                    }
                }
            }
        }
    });
}


// Event Listeners based on the current page
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('quiz-form')) {
        loadQuestions();
        document.getElementById('quiz-form').addEventListener('submit', submitQuiz);
    }
    if (document.getElementById('scoreChart')) {
        loadResults();
    }
}); 