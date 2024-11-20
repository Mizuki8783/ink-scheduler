
# AI-Powered Appointment Scheduler

A sophisticated appointment scheduling system that leverages AI to manage appointments through natural language processing. The system integrates with Google Calendar and provides a seamless interface for appointment management.

## Features

- 🤖 AI-powered natural language appointment scheduling
- 📅 Google Calendar integration
- 💬 Real-time appointment management
- 🔄 Webhook support for calendar synchronization
- 🔐 Secure credential management
- 🚀 Scalable architecture with Celery workers

## Tech Stack

- **Backend**: Flask
- **Task Queue**: Celery with Redis
- **AI/ML**: LangChain with GPT-4
- **Database**: MongoDB
- **External Services**:
  - Google Calendar API
  - Airtable
  - OpenAI/Groq

## Prerequisites

- Python 3.12
- Redis Server
- MongoDB
- Google Calendar API credentials
- Various API keys (see Environment Variables section)

## Installation

1. Clone the repository:
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```

2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Set up environment variables (see Environment Variables section)

4. Run the application:
    ```bash
    python ink-scheduler.py
    ```

## Environment Variables

Create a `.env` file with the following variables:
env
FLASK_APP=ink-scheduler.py
FLASK_ENV=development
FLASK_DEBUG=1
FERNET_KEY=<your-fernet-key>
API Keys
OPENAI_API_KEY=<your-openai-key>
GROQ_API_KEY=<your-groq-key>
AIRTABLE_API_KEY=<your-airtable-key>
GITGUARDIAN_API_KEY=<your-gitguardian-key>
Database URLs
MONGODB_URL=<your-mongodb-url>
REDIS_URL=<your-redis-url>
LangChain Configuration
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=<your-langchain-endpoint>
LANGCHAIN_API_KEY=<your-langchain-key>
LANGCHAIN_PROJECT=<your-project-name>

## Docker Support

The application can be containerized using Docker. Two Dockerfile configurations are provided:

1. Flask Application (`Dockerfiles/Dockerfile.flask`)
2. Celery Workers (`Dockerfiles/Dockerfile.celery`)

## Project Structure
plaintext
.
├── app/
│ ├── main/ # Main application routes
│ ├── webhook/ # Webhook handlers
│ ├── utils/ # Utility functions
│ │ ├── llm/ # LangChain AI components
│ │ └── setup/ # Setup utilities
│ └── tasks.py # Celery tasks
├── Dockerfiles/ # Docker configurations
├── requirements.txt # Python dependencies
└── config.py # Application configuration

## Security

- Credentials are encrypted using Fernet encryption
- GitGuardian integration for secret scanning
- Pre-commit hooks for security checks

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI/Groq for AI capabilities
- LangChain for AI framework
- Google Calendar API for calendar integration
