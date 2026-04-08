---
title: CV Bot AI Resume Optimizer
sdk: docker
app_port: 8000
base_path: /web
tags:
- reinforcement-learning
- resume-optimization
- ai
- gemini
---

# CV Bot AI Powered Resume Optimizer with Reinforcement Learning

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/license-BSD-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Hugging%20Face-Spaces-yellow.svg" alt="Hugging Face">
</p>

CV Bot is an AI powered resume optimization environment that uses reinforcement learning to improve your resume for job applications. It analyzes your resume against job requirements, suggests improvements using Google Gemini AI, and learns from application outcomes to maximize your chances of getting selected.

## Features

- **Resume Parsing** - Supports PDF, DOCX, and TXT file formats
- **ATS Scoring** - Automated Applicant Tracking System score calculation
- **RL Based Optimization** - Uses Q Learning to optimize resume for job applications
- **Interactive Web UI** - Beautiful interface to upload, edit, and optimize resumes
- **Real Time Feedback** - Get instant feedback on resume improvements
- **Smart Suggestions** - AI powered improvement recommendations using Google Gemini

## How It Works

CV Bot uses Q Learning a reinforcement learning algorithm to optimize resumes:

1. **Parse** - Upload your resume, the system extracts skills, experience, and summary
2. **Apply** - System applies to jobs and simulates employer decisions
3. **Learn** - Based on selected rejected outcomes, the RL agent updates its Q table
4. **Improve** - Suggests resume improvements to increase selection chances
5. **Repeat** - Continues learning until optimal resume state is achieved

## Reward System

CV Bot uses a sophisticated reward system to guide the RL agent:

### Base Rewards and Penalties

| Outcome | Reward | Description |
|---------|--------|-------------|
| Selected | +10.0 | Resume selected by employer |
| Near Selected | +2.0 | Close to being selected within 5 ATS points |
| Rejected | -1.0 | Resume rejected by employer |
| Step Reward | +0.1 | Small reward per step to reduce sparsity |

### Bonus Rewards

| Bonus | Value | Description |
|-------|-------|-------------|
| ATS Improvement | +0.5 times improvement | Reward for improving ATS score |
| ATS Milestone | +2.0 | Bonus when reaching ATS 60 70 80 90 |
| Keyword Match | +0.3 times improvement | Reward for matching job keywords |
| Efficiency Bonus | up to +5.0 | Bonus for getting selected in fewer iterations |

### RL Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| Learning Rate | 0.1 | How quickly Q values are updated |
| Discount Factor | 0.95 | Importance of future rewards |
| Exploration Rate | 1.0 to 0.01 | Starts high, decays over episodes |

## Installation

### Using Docker Recommended

```bash
# Build the Docker image
docker build -t cv_bot .

# Run the container
docker run -p 8000:8000 -e GEMINI_API_KEY=your_api_key cv_bot
```

### Local Development

```bash
# Clone the repository
git clone https://github.com/yourusername/cv_bot.git
cd cv_bot

# Install dependencies
pip install -r requirements.txt

# Set environment variable
export GEMINI_API_KEY=your_api_key
 
```

## Usage

### Web Interface

1. Start the server
2. Open http://localhost:8000/web/ in your browser
3. Upload your resume PDF DOCX or TXT
4. Review and edit parsed information
5. Click Start Optimization to begin
6. Click Step to apply to jobs and get feedback
7. Monitor your stats Selected Rejected ATS scores

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /web/ | GET | Web UI |
| /parse-resume | POST | Parse resume file |
| /session-reset | POST | Start new optimization session |
| /session-step | POST | Apply for a job and get feedback |
| /session-state | GET | Get current session state |

### API Example

```bash
# Parse a resume
curl -X POST http://localhost:8000/parse-resume \
  -F "file=@resume.pdf"

# Start a session
curl -X POST http://localhost:8000/session-reset \
  -H "Content-Type: application/json" \
  -d '{"action": {"skills": ["Python", "SQL"], "experience_years": 3, "summary": "Software Engineer"}}'

# Step through an iteration
curl -X POST http://localhost:8000/session-step

# Get current state
curl http://localhost:8000/session-state
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| GEMINI_API_KEY | Yes | Google Gemini API key for AI features |

Get your API key from: https://aistudio.google.com/app/apikey

## Project Structure

```
cv_bot/
├── server/
│   ├── app.py              # FastAPI application
│   ├── cv_bot_environment.py  # RL environment
│   └── static/
│       └── index.html      # Web UI
├── core/
│   ├── rl_agent.py        # Q Learning agent
│   ├── gemini_optimizer.py # AI optimization
│   └── resume_manager.py  # Resume handling
├── config/
│   └── rl_config.py       # RL parameters
├── models.py              # Data models
├── Dockerfile             # Docker configuration
├── requirements.txt       # Python dependencies
├── openenv.yaml           # OpenEnv manifest
└── README.md             # This file
```

## Tech Stack

- **Backend**: FastAPI, Uvicorn
- **AI/ML**: Google Gemini API, Q Learning Reinforcement Learning
- **Resume Parsing**: pdfplumber, python-docx
- **Frontend**: Vanilla HTML/CSS/JS
- **Deployment**: Docker, Hugging Face Spaces