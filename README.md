# AI-Powered Resume Analyzer

An AI-powered web application that evaluates resumes against job descriptions and generates meaningful insights to help candidates improve their resumes and align them with specific job requirements.

## Overview

The Resume Analyzer uses Natural Language Processing (NLP) techniques to analyze resume content, compare it with a given job description, and generate a resume score along with personalized improvement suggestions.

The application provides an intuitive web interface where users can upload their resumes, view detailed analysis results, and access their previous analyses.

## Key Features

- **Resume Analysis** – Extracts and analyzes relevant information from uploaded resumes.
- **Job Description Matching** – Compares resume content with specific job requirements.
- **Resume Scoring** – Generates an overall score based on the analysis.
- **NLP-Based Analysis** – Uses Natural Language Processing to identify relevant skills and content.
- **Personalized Suggestions** – Provides actionable recommendations for improving resume quality.
- **Analysis History** – Allows users to view previously analyzed resumes.
- **Web-Based Interface** – Simple and user-friendly interface built with Flask.

## Technology Stack

| Technology | Purpose |
|------------|---------|
| Python | Backend development |
| Flask | Web application framework |
| NLP | Resume and job description analysis |
| PostgreSQL | Database management |
| HTML | Web structure |
| CSS | Styling and UI |
| JavaScript | Client-side functionality |

## Project Structure

```text
resume-analyzer/
│
├── app.py
├── requirements.txt
├── templates/
│   ├── index.html
│   ├── dashboard.html
│   ├── analysis_details.html
│   ├── history.html
│   └── results.html
│
└── .gitignore
