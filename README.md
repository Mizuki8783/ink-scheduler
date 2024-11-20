
# AI-Powered Appointment Scheduler

InstagramのDMを自動化するAI予約管理システムのバックエンドサーバーです。
Manychatをフロントエンドとして使用し、InstagramのDMを通じて予約管理を実現します。
自然言語処理により、お客様とのシームレスなコミュニケーションを可能にし、ビジネスの効率化を支援します。

## 機能

- 🤖 AIによる自然言語予約スケジューリング
- 📅 Googleカレンダーとの連携
- 💬 リアルタイムの予約管理
- 🔄 カレンダー同期のためのWebhookサポート
- 🔐 安全な認証情報管理
- 🚀 Celeryワーカーによるスケーラブルなアーキテクチャ

## Tech Stack

- **Backend**: Flask
- **Database**: MongoDB, Airtable
- **Task Queue**: Celery with Redis
- **LLM Framework**: LangChain
- **Other Services**:
  - Google Calendar API
  - OpenAI/Groq

## Prerequisites

- Python 3.12
- Redis Server
- MongoDB
- Google Calendar API credentials
- API keys (Environment Variables sectionを参照)

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
### Flask setup
FLASK_APP=ink-scheduler.py
FLASK_ENV=development
FLASK_DEBUG=1
FERNET_KEY=your-fernet-key
### API Keys
OPENAI_API_KEY=your-openai-key
GROQ_API_KEY=your-groq-key
AIRTABLE_API_KEY=your-airtable-key
GITGUARDIAN_API_KEY=your-gitguardian-key
### Database URLs
MONGODB_URL=your-mongodb-url
REDIS_URL=your-redis-url
### LangChain Configuration
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=your-langchain-endpoint
LANGCHAIN_API_KEY=your-langchain-key
LANGCHAIN_PROJECT=your-project-name

## Docker Support

このアプリケーションはDockerを使用してコンテナ化することができます。2つのDockerfile構成が提供されています：

1. Flask アプリケーション (`Dockerfiles/Dockerfile.flask`)
2. Celery ワーカー (`Dockerfiles/Dockerfile.celery`)

## Security

- Google Calendarのクレデンシャル等はFernetで暗号化されています
- GitGuardianを使用し、シークレット漏洩防ぐ為のスキャンニングを行います
- セキュリティチェックのためのプリコミットフックを導入

## License

This project is licensed under the MIT License - see the LICENSE file for details.
