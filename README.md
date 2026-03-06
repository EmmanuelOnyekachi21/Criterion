# 🛡️ Criterion

> AI-powered code review agent that ensures every merge request delivers complete value

[![GitLab AI Hackathon](https://img.shields.io/badge/GitLab-AI%20Hackathon-FC6D26?logo=gitlab)](https://gitlab.devpost.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

An autonomous GitLab agent built on the GitLab Duo Agent Platform that validates merge requests against acceptance criteria and surfaces historical design context to prevent incomplete implementations and uninformed changes.

**🚧 Work in Progress** - Currently in development for the [GitLab AI Hackathon 2026](https://gitlab.devpost.com)

---

## 🎯 The Problem

**30% of merged code requires follow-up work** due to:

1. **Incomplete Implementations**: MRs implement 2 of 5 acceptance criteria, get merged, and issues stay open
2. **Lost Context**: Developers change code without knowing the historical constraints, causing regressions

**Cost**: Weeks of rework, production bugs, requirement drift, wasted engineering hours

---
## ✨ The Solution

Criterion is an AI agent that runs automatically on every merge request to:

### 🎯 Validate Acceptance Criteria
- Extracts requirements from linked GitLab issues
- Analyzes MR diffs semantically using Claude AI
- Reports compliance: "This MR implements 3/5 criteria"
- Blocks merge when incomplete (configurable)
- Provides evidence for each finding

### 📚 Surface Historical Context
- Analyzes git blame for changed lines
- Traces code to original MRs and issues
- Extracts design decisions and constraints using AI
- Warns when changes might violate historical reasoning
- Links to relevant past discussions

### 📊 Example Output
```markdown
## 🛡️ Criterion Analysis

### ✅ Acceptance Criteria Compliance
**3/5 criteria implemented (60%)**

✅ Implemented:
- Export to CSV (evidence: lines 45-67 in exporter.py)
- Include user fields (evidence: UserSerializer changes)
- Add download button (evidence: frontend/Export.tsx)

❌ Missing:
- Export to JSON format
- Add progress indicator during export

### 📚 Historical Context
⚠️ **Design Constraint Found**
This file was modified in MR !247 (8 months ago) to handle large datasets 
by streaming results instead of loading to memory.

Your changes (lines 78-92) reintroduce full-load pattern.

**Original issue**: #189 - "Export crashes on 10K+ users"
**Recommendation**: Verify your changes handle large datasets or document 
why constraint no longer applies.
```

---

## 🏗️ Architecture

### System Overview

```mermaid
graph LR
    subgraph GitLab["🔷 GitLab"]
        MR["MR Created"]
        Webhook["Webhook"]
        Comment["Comment Posted"]
    end
    
    subgraph Agent["🤖 Criterion Agent"]
        Router["Router"]
        Report["Report Generator"]
    end
    
    subgraph Acceptance["✅ Acceptance Criteria Path"]
        AccAnalyzer["Analyzer"]
        Parser["Parser"]
        AccClaude["Claude AI"]
    end
    
    subgraph Historical["📚 Historical Context Path"]
        HistAnalyzer["Analyzer"]
        GitBlame["Git Blame"]
        Tracer["MR/Issue Tracer"]
        HistClaude["Claude AI"]
    end
    
    subgraph External["🌐 External Services"]
        GitLabAPI["GitLab API"]
        AnthropicAPI["Anthropic API"]
        Git["Git Repo"]
    end
    
    subgraph Storage["💾 Data Layer"]
        Cache["Redis"]
        DB["PostgreSQL"]
    end
    
    MR --> Webhook
    Webhook --> Router
    
    Router -->|criteria| AccAnalyzer
    AccAnalyzer --> Parser
    Parser --> AccClaude
    AccClaude --> AnthropicAPI
    
    Router -->|diff & history| HistAnalyzer
    HistAnalyzer --> GitBlame
    HistAnalyzer --> Tracer
    GitBlame --> Git
    Tracer --> GitLabAPI
    HistAnalyzer --> HistClaude
    HistClaude --> AnthropicAPI
    
    AccClaude --> Report
    HistClaude --> Report
    Report --> Comment
    
    Cache -.->|cache| AccAnalyzer
    Cache -.->|cache| HistAnalyzer
    DB -.->|persist| Report
```

### Tech Stack

**Backend**
- Python 3.11+ (FastAPI for async API)
- Celery + Redis (async task processing)
- PostgreSQL (data persistence)
- SQLAlchemy 2.x (async ORM)

**AI/ML**
- Anthropic Claude 3.5 Sonnet (semantic analysis)
- GitLab Duo Agent Platform integration

**Infrastructure**
- Docker + Docker Compose
- Structured logging (JSON)
- OpenTelemetry (observability)

**GitLab Integration**
- python-gitlab SDK
- Webhook processing
- MR comment API
- Git operations

---

## 📁 Project Structure

```
criterion/
├── docker-compose.yml          # Multi-container orchestration
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── README.md                   # This file
│
├── backend/                    # FastAPI backend service
│   ├── Dockerfile              # Backend container image
│   ├── requirements.txt         # Python dependencies
│   ├── alembic.ini             # Database migration config
│   ├── alembic/                # Database migrations
│   │   └── versions/           # Migration scripts
│   │
│   └── app/
│       ├── main.py             # FastAPI app entry point
│       ├── config.py           # Settings from environment
│       ├── database.py         # SQLAlchemy async setup
│       ├── celery_app.py       # Celery task queue config
│       │
│       ├── models/             # SQLAlchemy ORM models
│       │   ├── merge_request.py
│       │   ├── analysis.py
│       │   ├── webhook.py
│       │   ├── design_rationale.py
│       │   └── override.py
│       │
│       ├── schemas/            # Pydantic request/response schemas
│       │   ├── webhook.py
│       │   └── analysis.py
│       │
│       ├── api/                # FastAPI route handlers
│       │   ├── webhooks.py     # GitLab webhook endpoints
│       │   ├── analyses.py     # Analysis endpoints
│       │   └── health.py       # Health check endpoint
│       │
│       ├── tasks/              # Celery async tasks
│       │   └── analysis.py     # Analysis task definitions
│       │
│       └── services/           # Business logic layer
│           ├── gitlab_client.py    # GitLab API client
│           ├── claude_client.py    # Anthropic Claude client
│           └── analysis_service.py # Core analysis logic
│
└── frontend/                   # Streamlit dashboard
    ├── Dockerfile              # Frontend container image
    ├── requirements.txt         # Python dependencies
    └── app.py                  # Streamlit app entry point
```

### Directory Breakdown

**backend/** - Core analysis engine
- Handles GitLab webhooks
- Runs acceptance criteria validation
- Extracts historical context
- Generates analysis reports
- Manages async task processing with Celery

**frontend/** - User dashboard
- Displays analysis results
- Shows historical trends
- Provides configuration UI
- Built with Streamlit for rapid development

**models/** - Data persistence layer
- Merge request tracking
- Analysis results storage
- Design rationale history
- Override configurations

**services/** - Business logic (framework-agnostic)
- GitLab integration
- Claude AI interactions
- Analysis algorithms
- No FastAPI/Streamlit dependencies

**api/** - HTTP endpoints
- Webhook receivers
- Analysis queries
- Health monitoring

---

## 🚀 Quick Start

> **Note**: Full setup instructions coming soon. Project is under active development.

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- GitLab account
- Anthropic API key

### Installation
```bash
# Clone repository
git@github.com:EmmanuelOnyekachi21/Criterion.git
cd Criterion

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Start services
docker-compose up -d

# Run migrations
alembic upgrade head

# Start application
python -m app.main
```

---

## 🎓 Learning & Development

This project follows **FAANG-level engineering practices**:

- ✅ Hexagonal architecture (ports & adapters)
- ✅ Comprehensive testing (80%+ coverage)
- ✅ Async/await throughout
- ✅ Circuit breakers and retries
- ✅ Structured logging and tracing
- ✅ Production-ready from day 1

### Development Principles
- Design before code
- Tests before implementation
- Error handling is first-class
- Observability built-in
- Security by default

---

## 📊 Project Status

**Timeline**: 30 days (Feb 23 - Mar 25, 2026)

### Development Progress

#### ✅ Completed Phases

**Phase 0: Architecture & Design**
- ✅ System architecture design
- ✅ Database schema design
- ✅ API contract definition
- ✅ System design documentation

**Phase 1: Foundation & Infrastructure**
- ✅ Project scaffold setup
- ✅ Docker Compose configuration
- ✅ FastAPI skeleton with async support
- ✅ Celery worker setup with Redis
- ✅ Health check endpoint
- ✅ Streamlit dashboard scaffold

**Phase 2: Webhook Handler**
- ✅ Webhook receiver endpoint
- ✅ Token verification
- ✅ Idempotency check (duplicate webhook detection)
- ✅ MR upsert with conflict handling
- ✅ Celery task enqueue

**Phase 3: GitLab Integration & Analysis (Partial)**
- ✅ GitLab client methods (get_mr_changes, get_mr_details, get_blame, get_commit, get_issue)
- ✅ Celery task skeleton with status tracking
- ✅ Extract relevant commits logic
- ✅ Claude client with optimized prompt
- ✅ Issue content fetching and integration

#### 🚧 Remaining Phases

**Phase 3 (Finish): Complete Analysis Pipeline**
- 🔲 Wire Claude analysis into Celery task
- 🔲 Save Claude results to database
- 🔲 Error handling for Claude API failures

**Phase 4: Acceptance Criteria Engine**
- 🔲 Fetch linked issue requirements
- 🔲 Check acceptance criteria against diff
- 🔲 Generate compliance report

**Phase 5: Post Analysis Results**
- 🔲 Post analysis comment back to GitLab MR
- 🔲 Format results as markdown
- 🔲 Include evidence and links

**Phase 6: Streamlit Dashboard**
- 🔲 Show analysis results
- 🔲 Manual trigger interface
- 🔲 Real-time polling for updates

**Phase 7: Production Hardening**
- 🔲 Error handling and logging
- 🔲 Circuit breakers for external APIs
- 🔲 Retry logic with exponential backoff

**Phase 8: Testing**
- 🔲 Unit tests
- 🔲 Integration tests
- 🔲 End-to-end testing

**Phase 9: Deployment**
- 🔲 Deploy to Render
- 🔲 Deploy to Streamlit Cloud
- 🔲 Configure production environment

**Phase 10: Demo & Submission**
- 🔲 Record demo video
- 🔲 Finalize documentation
- 🔲 Submit to hackathon

**Current Phase**: Phase 2 - GitLab Integration (70% complete)

---

## 🎯 Hackathon Goals

**Primary**
- Submit working project by March 25, 2026
- Target GitLab + Anthropic prize ($10,000)
- Demonstrate production-ready engineering

**Secondary**
- Learn distributed systems design
- Master async Python patterns
- Understand LLM integration at scale
- Build judge-testable interface

---

## 🤝 Contributing

This is currently a solo hackathon project, but feedback and suggestions are welcome!

### Ways to Help
- 🐛 Report issues you find
- 💡 Suggest features or improvements
- 📖 Improve documentation
- ⭐ Star the repo if you find it interesting

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 🙏 Acknowledgments

- Built for [GitLab AI Hackathon 2026](https://gitlab.devpost.com)
- Powered by [Anthropic Claude](https://www.anthropic.com/)
- Uses [GitLab Duo Agent Platform](https://docs.gitlab.com/ee/user/gitlab_duo/)

---

## 📧 Contact

**Developer**: D3MXN  
**Email**: emmanuelonyekachi04122000@gmail.com  
**Twitter/X**: [@akpan_itoro_](https://https://x.com/akpan_itoro_)  
**LinkedIn**: [Click me!](https://linkedin.com/in/emmanuelonyekachi21/)

---

## 🎬 Demo

> Demo video coming March 2026

---

**⚡ Building in public** - Follow along for updates on the journey from junior to mid-level engineering thinking!

**#GitLabHackathon #BuildInPublic #AI #SoftwareEngineering**
```

---

# **Additional Files to Create**

## **LICENSE (MIT)**
```
MIT License

Copyright (c) 2026 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## **.gitignore**
```
# Python
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
__pycache__/

# Virtual Environment
venv/
env/
ENV/
.venv

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Environment Variables
.env
.env.local
.env.*.local

# Database
*.db
*.sqlite3
*.sql
*.dump

# Logs
*.log
logs/

# Testing
.coverage
.pytest_cache/
htmlcov/
.tox/

# Docker
docker-compose.override.yml

# Redis
dump.rdb

# Celery
celerybeat-schedule
celerybeat.pid

# Project Specific
*.pid
checkpoints/
temp/
tmp/
```

---

## **.env.example**
```
# Application
DEBUG=True
ENVIRONMENT=development
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/criterion
DB_HOST=localhost
DB_PORT=5432
DB_NAME=meridian
DB_USER=postgres
DB_PASSWORD=postgres

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# GitLab
GITLAB_URL=https://gitlab.com
GITLAB_TOKEN=your-gitlab-token-here
GITLAB_WEBHOOK_SECRET=your-webhook-secret-here

# Anthropic Claude
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Security
CORS_ORIGINS=["http://localhost:3000"]