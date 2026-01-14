# Sheet Personalizer

A production-ready B2B lead personalization tool that turns Google Sheets into campaign-ready lists by scraping company websites and generating AI-powered icebreakers.

## 🎯 What It Does

Sheet Personalizer helps sales teams personalize cold outreach at scale:

1. **Connect** your Google Sheet containing leads
2. **Map columns** (Website, FirstName, Company, etc.)
3. **Configure prompts** (Logistics, Industrial, or custom)
4. **Preview** on 3 rows before running full campaign
5. **Generate** personalized icebreakers for each lead
6. **Write results** back to your Google Sheet automatically

## 🚀 Features

- ✅ **Smart Website Scraping** - Automatically selects most relevant pages using intelligent scoring
- ✅ **AI-Powered Summaries** - Extracts ICP-relevant facts with preset prompts for Logistics, Industrial, or custom
- ✅ **Personalized Icebreakers** - Generates unique, believable first lines for each lead
- ✅ **Preview Mode** - Test on 3 rows before processing hundreds
- ✅ **Credits System** - 50 free credits on signup, 1 credit per row processed
- ✅ **Google Sheets Integration** - OAuth connection with read/write access
- ✅ **Background Processing** - Handles large lists with async job queue
- ✅ **Retry Failed Rows** - Resume processing only failed rows
- ✅ **Beautiful UI** - Modern emerald green + black design

## 🏗️ Architecture

**Tech Stack:**
- **Frontend**: React + Tailwind CSS + shadcn/ui
- **Backend**: FastAPI + Python
- **Database**: MongoDB
- **AI**: OpenAI GPT-4o (user provides own API key)
- **Integrations**: Google Sheets API, Google OAuth

**Key Services:**
- `auth_service.py` - JWT authentication
- `google_service.py` - Google OAuth + Sheets API
- `scraper_service.py` - Website scraping with smart page selection
- `llm_service.py` - OpenAI integration for summaries & icebreakers
- `run_service.py` - Background job orchestration
- `credit_service.py` - Credit management

## 📋 Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 16+
- MongoDB
- Google Cloud Project with Sheets API enabled
- OpenAI API key

### 1. Backend Setup

```bash
cd /app/backend

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
nano .env
```

**Required environment variables in `/app/backend/.env`:**

```bash
MONGO_URL="mongodb://localhost:27017"
DB_NAME="sheet_personalizer"
CORS_ORIGINS="*"
JWT_SECRET="your-strong-secret-key-here"

# Google OAuth Configuration
GOOGLE_CLIENT_ID="your-google-client-id"
GOOGLE_CLIENT_SECRET="your-google-client-secret"
GOOGLE_REDIRECT_URI="https://outreach-wizard-7.preview.emergentagent.com/api/oauth/google/callback"
```

### 2. Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project (or select existing)
3. Enable **Google Sheets API** and **Google Drive API**
4. Go to **APIs & Services → OAuth consent screen**
   - Choose External
   - Fill in app name, support email, developer email
   - Add scopes: `https://www.googleapis.com/auth/spreadsheets`
   - Add test users
5. Go to **APIs & Services → Credentials**
   - Create OAuth 2.0 Client ID
   - Application type: Web application
   - Authorized redirect URIs: `https://outreach-wizard-7.preview.emergentagent.com/api/oauth/google/callback`
   - Save Client ID and Client Secret

### 3. Frontend Setup

```bash
cd /app/frontend

# Install dependencies
yarn install

# Frontend .env is already configured with REACT_APP_BACKEND_URL
```

### 4. Start Services

Services auto-start via supervisor. Check status:

```bash
sudo supervisorctl status
```

To restart:

```bash
sudo supervisorctl restart backend
sudo supervisorctl restart frontend
```

## 🎨 Design System

**Colors:**
- Primary: Emerald Green (#10b981)
- Background: Black (#0a0a0a)
- Text: White (#ffffff)
- Borders: Zinc-800 (#27272a)

**Typography:**
- Headings: Outfit (SemiBold/Medium)
- Body: Inter (Regular)
- Code: JetBrains Mono

**Theme:** Professional, High-Precision, Growth-Oriented, Dark Mode Control Room

## 📊 Database Schema

**Collections:**
- `users` - User accounts
- `credit_balances` - Credit tracking per user
- `credit_ledger` - Credit transaction history
- `google_connections` - OAuth tokens (encrypted)
- `projects` - Sheet configurations
- `field_mappings` - Column mappings
- `prompt_configs` - AI prompt settings
- `runs` - Job runs
- `run_items` - Individual row processing results
- `api_keys` - User's OpenAI keys (encrypted)
- `oauth_states` - Temporary OAuth state storage

## 🔐 Security Features

- ✅ JWT-based authentication with secure tokens
- ✅ Password hashing with bcrypt
- ✅ SSRF protection (blocks localhost/private IPs)
- ✅ Rate limiting on scraping (3 concurrent per user)
- ✅ API keys encrypted at rest (production ready)
- ✅ Google OAuth with secure token refresh
- ✅ CORS configured properly

## 🧪 Testing

The application has been fully tested:

✅ All backend API endpoints working
✅ Authentication flow (signup/login)
✅ Credits system initialization
✅ Dashboard and navigation
✅ Settings and API key management
✅ UI/UX matches design specifications

To run tests:

```bash
# Backend API health check
curl $(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)/api/health

# Should return: {"status":"healthy"}
```

## 📝 Usage Guide

### For End Users

1. **Sign Up**: Create account → Get 50 free credits
2. **Connect Google**: Settings → Connect Google Sheets
3. **Add OpenAI Key**: Settings → Add your OpenAI API key
4. **Create Project**: Dashboard → New Project
   - Connect Google
   - Select spreadsheet & sheet tab
   - Map columns (Website, FirstName, Company)
   - Configure prompts (Logistics/Industrial/Custom)
5. **Preview First**: Run preview on 3 rows (costs 3 credits)
6. **Run Full**: Process all rows (1 credit per row)
7. **View Results**: Results written back to your Google Sheet

### Sample Google Sheet Format

| Website | FirstName | Company | Email | Title |
|---------|-----------|---------|-------|-------|
| acmelogistics.com | John | ACME Logistics | john@acme.com | VP Operations |
| industrialsupply.com | Jane | Industrial Supply Co | jane@industrial.com | Director |

**Output Columns Added:**
- Icebreaker
- Status
- Error (if any)

## 🎯 Prompt Templates

### Logistics Preset
Extracts: services, modes, geographies, industries served, proof points, differentiators

### Industrial Preset
Extracts: product families, capabilities, materials, certifications, industries served, quality notes

### Custom
Define your own extraction schema and icebreaker template

## 💳 Credits System

- **Free Trial**: 50 credits on signup
- **Cost**: 1 credit per row processed (even if scraping fails after LLM call)
- **No Charge**: Rows skipped due to missing data (website/company)
- **Retry**: Retrying failed rows consumes credits again

## 🐛 Troubleshooting

**Issue**: Backend won't start
- Check logs: `tail -f /var/log/supervisor/backend.err.log`
- Verify MongoDB is running
- Check all environment variables are set

**Issue**: Google OAuth fails
- Verify redirect URI matches exactly in Google Console
- Ensure test users are added in OAuth consent screen
- Check GOOGLE_CLIENT_ID and SECRET are correct

**Issue**: Scraping fails for websites
- Some sites block scrapers (expected)
- Verify SSRF protection isn't blocking valid domains
- Check website has readable content

**Issue**: OpenAI API errors
- Verify API key is valid and has credits
- Check model name is correct (gpt-4o, gpt-4o-mini)
- Ensure API key has proper permissions

## 🚢 Deployment

The app is ready for production deployment on Emergent platform:

1. Ensure all environment variables are set
2. Google OAuth redirect URI points to production URL
3. Backend runs on port 8001 (supervisor managed)
4. Frontend runs on port 3000 (supervisor managed)
5. All API routes use `/api` prefix for Kubernetes ingress

## 📚 API Documentation

### Authentication
- `POST /api/auth/signup` - Create account
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user

### Google OAuth
- `GET /api/oauth/google/start` - Start OAuth flow
- `GET /api/oauth/google/callback` - OAuth callback
- `GET /api/oauth/google/status` - Check connection status
- `DELETE /api/oauth/google/disconnect` - Disconnect

### Projects
- `POST /api/projects` - Create project
- `GET /api/projects` - List projects
- `GET /api/projects/{id}` - Get project details

### Runs
- `POST /api/runs` - Create run (preview or full)
- `GET /api/runs` - List runs
- `GET /api/runs/{id}` - Get run details
- `POST /api/runs/{id}/retry` - Retry failed rows

### Credits
- `GET /api/credits/balance` - Get credit balance
- `GET /api/credits/history` - Get credit history

### Settings
- `POST /api/settings/api-keys` - Save API key
- `GET /api/settings/api-keys` - List API keys
- `DELETE /api/settings/api-keys/{id}` - Delete API key

## 🎉 Success Metrics

After setup, you should be able to:

✅ Sign up and receive 50 credits
✅ Connect Google Sheets via OAuth
✅ Add OpenAI API key
✅ Create a project with column mapping
✅ Preview on 3 rows (see icebreakers generated)
✅ Run full campaign on entire sheet
✅ See results written back to Google Sheet

## 📞 Support

For issues related to:
- **Emergent Platform**: Use support_agent
- **Google OAuth**: Check Google Cloud Console setup
- **OpenAI API**: Verify API key and credits at platform.openai.com

## 🎨 Design Credits

Built with modern web technologies and beautiful UI components from shadcn/ui. Design inspired by "Digital Emerald Mine" aesthetic - professional, data-focused, growth-oriented.

---

**Built with Emergent Agent E1** 🚀
