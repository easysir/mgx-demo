# MGX MVP - AI-Powered Development Platform

MGX (MetaGPTX) is an AI-powered development platform that enables users to build web applications through natural language conversations with a team of AI agents.

## 🌟 Features

- **6-Person AI Agent Team**: Mike (Team Leader), Emma (Product Manager), Bob (Architect), Alex (Engineer), David (Data Analyst), Iris (Researcher)
- **Real-time Collaboration**: WebSocket-based streaming responses and status updates
- **Code Editor**: Monaco-based editor with syntax highlighting and multi-file support
- **Live Preview**: Real-time preview of your application with responsive device views
- **GitHub Integration**: Automatic code commits and deployments
- **Multi-LLM Support**: OpenAI GPT-4, Anthropic Claude, Google Gemini

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                            │
│  (Next.js 14 + shadcn/ui + Tailwind CSS + Zustand)        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend API                            │
│              (FastAPI + WebSocket)                          │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  PostgreSQL   │  │     Redis     │  │    Qdrant     │
│   Database    │  │     Cache     │  │  Vector DB    │
└───────────────┘  └───────────────┘  └───────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/mgx/mgx-mvp.git
   cd mgx-mvp
   ```

2. **Run setup script**
   ```bash
   make setup
   ```

3. **Update environment variables**
   ```bash
   # Edit .env and add your API keys:
   # - JWT_SECRET_KEY (use: openssl rand -hex 32)
   # - OPENAI_API_KEY
   # - ANTHROPIC_API_KEY
   # - GITHUB_TOKEN
   ```

4. **Start all services**
   ```bash
   make dev
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## 📖 Documentation

- [Implementation Plan](docs/design/implementation_plan.md)
- [System Design](docs/design/system_design.md)
- [Architecture Diagram](docs/design/architect.plantuml)
- [API Documentation](http://localhost:8000/docs) (when running)

## 🛠️ Development

### Available Commands

```bash
# Setup & Installation
make setup              # Initial project setup
make install-backend    # Install backend dependencies
make install-frontend   # Install frontend dependencies

# Development
make dev                # Start all services
make dev-backend        # Start backend only
make dev-frontend       # Start frontend only

# Docker
make docker-up          # Start Docker containers
make docker-down        # Stop Docker containers
make docker-logs        # Show Docker logs

# Database
make migrate            # Run database migrations
make migrate-create     # Create a new migration
make db-seed            # Seed database with test data

# Testing
make test               # Run all tests
make test-backend       # Run backend tests
make test-frontend      # Run frontend tests
make coverage           # Generate coverage report

# Code Quality
make lint               # Run linters
make format             # Format code

# Build
make build              # Build production images
```

For more commands, run `make help`.

### Project Structure

```
mgx-mvp/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── agents/         # AI Agent implementations
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core services (LLM, Tools, Session)
│   │   ├── models/         # Database models
│   │   ├── middleware/     # Authentication middleware
│   │   └── utils/          # Utility functions
│   ├── tests/              # Backend tests
│   └── requirements.txt    # Python dependencies
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── app/           # Next.js app router
│   │   ├── components/    # React components
│   │   ├── lib/           # Utility libraries
│   │   └── store/         # State management (Zustand)
│   └── package.json       # Node.js dependencies
├── infrastructure/         # Infrastructure configs
│   ├── docker/            # Dockerfiles
│   └── nginx/             # Nginx configs
├── docs/                  # Documentation
│   ├── design/            # Design documents
│   └── project_management/ # Project tracking
└── docker-compose.yml     # Docker Compose config
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v --cov=app
```

### Frontend Tests
```bash
cd frontend
npm run test
```

### E2E Tests
```bash
cd frontend
npm run test:e2e
```

## 📊 Project Management

We use a structured project management approach:

- [Sprint Board](docs/project_management/sprint_board.md) - Current sprint status
- [Task Checklist](docs/project_management/phase1_task_checklist.md) - Phase 1 tasks
- [Task Dependencies](docs/project_management/task_dependencies.md) - Dependency graph
- [Progress Tracker](docs/project_management/progress_tracker.md) - Weekly progress

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Run tests: `make test`
4. Run linters: `make lint`
5. Commit: `git commit -m "feat: your feature"`
6. Push: `git push origin feature/your-feature`
7. Create a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework for Python
- [Next.js](https://nextjs.org/) - React framework for production
- [shadcn/ui](https://ui.shadcn.com/) - Beautiful UI components
- [LangChain](https://www.langchain.com/) - LLM orchestration framework

## 📧 Contact

- **Project Lead**: Mike (mike@mgx.dev)
- **Technical Lead**: Bob (bob@mgx.dev)
- **Development Lead**: Alex (alex@mgx.dev)

## 🗺️ Roadmap

### Phase 1: MVP Core (Current)
- ✅ Project initialization
- 🔄 Database models and authentication
- ⏸️ Session Manager and Context Store
- ⏸️ LLM Service and Tool Executor
- ⏸️ 6-Person Agent Team
- ⏸️ API and WebSocket
- ⏸️ Preview Server
- ⏸️ Frontend UI

### Phase 2: Feature Expansion
- Supabase backend integration
- Multi-model switching
- Deployment to Vercel/Netlify
- Python/Data Science support
- Advanced search and web scraping

### Phase 3: Advanced Features
- Real-time collaboration
- Project template library
- Private deployment support

---

**Status**: 🚧 In Development (Phase 1, Sprint 1)

**Last Updated**: 2024-11-08