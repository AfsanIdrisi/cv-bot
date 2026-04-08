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

# CV Bot AI Resume Optimizer

CV Bot is an AI-powered resume optimization environment that uses reinforcement learning to improve your resume for job applications.

## Features

- Resume Parsing - Supports PDF, DOCX, and TXT
- ATS Scoring - Automated score calculation
- RL Based Optimization - Uses Q-Learning
- Interactive Web UI
- Real Time Feedback
- Smart Suggestions - AI powered

## Usage

Run the server and access http://localhost:8000/web/

## API Endpoints

- /web/ - Web UI
- /parse-resume - Parse resume file
- /session-reset - Start new session
- /session-step - Apply for job
- /session-state - Get current state

## Environment Variables

- GEMINI_API_KEY - Google Gemini API key

## Tech Stack

- FastAPI, Uvicorn
- Google Gemini API
- Q-Learning (RL)
- pdfplumber, python-docx
- Docker, HuggingFace Spaces