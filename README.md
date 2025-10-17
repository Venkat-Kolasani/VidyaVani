# VidyaVani - AI-Powered IVR Learning System

VidyaVani is an AI-powered Interactive Voice Response (IVR) learning system that enables students in rural India to access educational content and ask questions through basic phone calls. The system addresses barriers such as lack of internet connectivity, limited smartphone access, and shortage of trained teachers.

## Features

- **Phone-based Access**: Works with any basic mobile phone or landline
- **Multilingual Support**: English and Telugu language support
- **NCERT Curriculum**: Based on official Class 10 Science content
- **AI-Powered Responses**: Uses OpenAI GPT-5-nano for intelligent tutoring
- **Voice Processing**: Google Cloud Speech-to-Text and Text-to-Speech
- **Exotel Integration**: Uses Exotel APIs for Indian telephony infrastructure
- **Fast Response**: Target response time under 8 seconds

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Virtual environment (recommended)
- API keys for Exotel, OpenAI, and Google Cloud

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd vidyavani-ivr
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file with your API keys (see API Keys section below)
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

## API Keys Setup

### 1. **OpenAI API Key** (Required)
- Go to [OpenAI Platform](https://platform.openai.com/api-keys)
- Sign up/login to your account
- Click "Create new secret key"
- Copy the key (starts with `sk-`)

### 2. **Exotel API Keys** (Required)
- Go to [Exotel Console](https://my.exotel.com/signup)
- Sign up for a new account (free trial available)
- From the dashboard, get:
  - **Account SID** (from Account Details)
  - **API Key** (Settings → API Settings)
  - **API Token** (generated with API Key)
  - **Phone Number** (purchase from dashboard)
  - **App ID** (create an IVR app)
- See detailed setup guide: `docs/EXOTEL_SETUP.md`

### 3. **Google Cloud Credentials** (Required)
- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Create a new project or select existing one
- Enable these APIs:
  - Cloud Speech-to-Text API
  - Cloud Text-to-Speech API
- Go to IAM & Admin → Service Accounts
- Create a service account with Speech APIs access
- Download the JSON key file

### 4. **Configure Environment Variables**
Edit your `.env` file with the actual keys:

```bash
# Exotel Configuration
EXOTEL_ACCOUNT_SID=your_account_sid_here
EXOTEL_API_KEY=your_api_key_here
EXOTEL_API_TOKEN=your_api_token_here
EXOTEL_PHONE_NUMBER=your_exotel_phone_number
EXOTEL_APP_ID=your_app_id_here

# OpenAI Configuration
OPENAI_API_KEY=sk-your_openai_key_here

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
```

### Environment Variables

Copy `.env.example` to `.env` and configure the following required variables:

```bash
# Exotel (Required)
EXOTEL_ACCOUNT_SID=your-exotel-account-sid
EXOTEL_API_KEY=your-exotel-api-key
EXOTEL_API_TOKEN=your-exotel-api-token
EXOTEL_PHONE_NUMBER=your-exotel-phone-number
EXOTEL_APP_ID=your-exotel-app-id

# OpenAI (Required)
OPENAI_API_KEY=your-openai-api-key

# Google Cloud (Required)
GOOGLE_CLOUD_PROJECT=your-google-cloud-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
```

## Project Structure

```
vidyavani-ivr/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── src/                   # Source code modules
│   ├── ivr/              # IVR interface components
│   ├── audio/            # Audio processing (STT/TTS)
│   ├── rag/              # RAG engine for content retrieval
│   ├── content/          # NCERT content management
│   ├── session/          # Session management
│   ├── cache/            # Caching layer
│   └── utils/            # Utility functions
├── tests/                # Test suite
├── data/                 # Data storage
│   └── ncert/           # NCERT content files
└── logs/                # Application logs
```

## API Endpoints

- `GET /health` - Health check endpoint
- `GET /` - Root endpoint with system information
- `POST /webhook/incoming-call` - Exotel webhook for incoming calls
- `POST /webhook/language-selection` - Language selection processing
- `POST /webhook/record-question` - Question recording handler

## Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black src/ tests/
flake8 src/ tests/
```

### Performance Monitoring

The application includes comprehensive logging for performance monitoring:
- Response time tracking for each component
- API call performance metrics
- Cache hit/miss ratios
- Concurrent user monitoring

Logs are stored in the `logs/` directory:
- `vidyavani_YYYYMMDD.log` - General application logs
- `performance.log` - Performance metrics

## Technology Stack

- **Backend**: Python 3.9+ with Flask
- **LLM**: OpenAI GPT-5-nano for intelligent tutoring responses
- **Embeddings**: OpenAI text-embedding-3-small for semantic search
- **Vector DB**: FAISS for efficient content retrieval
- **Speech**: Google Cloud Speech-to-Text (STT) and Text-to-Speech (TTS)
- **IVR**: Exotel voice platform for call handling
- **Storage**: Local vector database with metadata persistence

## Architecture

The VidyaVani system uses a RAG (Retrieval-Augmented Generation) architecture:

1. **User Query** → Exotel IVR
2. **Speech-to-Text** → Google Cloud STT
3. **Semantic Search** → FAISS vector DB retrieves top-3 NCERT chunks
4. **Answer Generation** → GPT-5-nano with retrieved context
5. **Text-to-Speech** → Google Cloud TTS
6. **Response** → Exotel IVR plays audio back to student

## Configuration

Key environment variables (see `.env.example`):

```bash
# LLM Settings
LLM_MODEL=gpt-5-nano
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=500

# Other services...
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions and support, please open an issue in the GitHub repository.