# Quick Setup Guide for Sheet Personalizer

## 🚀 Get Started in 5 Steps

### Step 1: Set Up Google OAuth

The app requires Google OAuth to access Google Sheets. Here's how to set it up:

1. **Go to Google Cloud Console**: https://console.cloud.google.com
2. **Create/Select Project**: Create a new project or select existing one
3. **Enable APIs**:
   - Navigate to "APIs & Services" → "Library"
   - Search and enable "Google Sheets API"
   - Search and enable "Google Drive API"

4. **Configure OAuth Consent Screen**:
   - Go to "APIs & Services" → "OAuth consent screen"
   - Choose "External" user type
   - Fill in required fields:
     - App name: "Sheet Personalizer"
     - User support email: your email
     - Developer contact: your email
   - Click "Save and Continue"
   - Under "Scopes", click "Add or Remove Scopes"
   - Add: `https://www.googleapis.com/auth/spreadsheets`
   - Add: `https://www.googleapis.com/auth/drive.readonly`
   - Click "Save and Continue"
   - Under "Test users", add your Gmail address
   - Click "Save and Continue"

5. **Create OAuth Credentials**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: "Web application"
   - Name: "Sheet Personalizer"
   - Authorized JavaScript origins: `https://your-app-url.preview.emergentagent.com`
   - Authorized redirect URIs: `https://your-app-url.preview.emergentagent.com/api/oauth/google/callback`
   - Click "Create"
   - **COPY** the Client ID and Client Secret

6. **Update Backend Environment Variables**:
   ```bash
   nano /app/backend/.env
   ```
   
   Add these lines (replace with your actual values):
   ```bash
   GOOGLE_CLIENT_ID="your-client-id-from-google-console"
   GOOGLE_CLIENT_SECRET="your-client-secret-from-google-console"
   GOOGLE_REDIRECT_URI="https://your-app-url.preview.emergentagent.com/api/oauth/google/callback"
   ```

7. **Restart Backend**:
   ```bash
   sudo supervisorctl restart backend
   ```

### Step 2: Get OpenAI API Key

You'll need an OpenAI API key to generate summaries and icebreakers:

1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy it (starts with `sk-...`)
4. Keep it safe - you'll add it in the app's Settings page

### Step 3: Access the Application

1. Open your app URL: `https://your-app-url.preview.emergentagent.com`
2. Click "Get Started" to sign up
3. Create an account (you'll receive 50 free credits)

### Step 4: Configure Settings

1. Go to **Settings** from the dashboard
2. **Connect Google Sheets**:
   - Click "Connect Google Sheets"
   - Sign in with your Google account
   - Grant permissions
3. **Add OpenAI API Key**:
   - Paste your OpenAI API key
   - Click "Save"

### Step 5: Create Your First Project

1. Click **"New Project"** from dashboard
2. Follow the 5-step wizard:
   - **Step 1**: Verify Google connection ✓
   - **Step 2**: Select your spreadsheet and sheet tab
   - **Step 3**: Map columns (Website, FirstName, Company)
   - **Step 4**: Configure prompts (choose Logistics or Industrial preset)
   - **Step 5**: Run preview (test on 3 rows first!)

## 📝 Sample Google Sheet Format

Create a Google Sheet with these columns:

| Website | FirstName | Company | Email | Title |
|---------|-----------|---------|-------|-------|
| acmelogistics.com | John | ACME Logistics | john@acme.com | VP Operations |
| techsolutions.io | Jane | Tech Solutions | jane@tech.com | CEO |

## ✅ Verification Checklist

Before creating a project, verify:

- ✅ Google OAuth credentials are configured in `/app/backend/.env`
- ✅ Backend has been restarted after adding credentials
- ✅ You've signed up and have 50 credits
- ✅ Google Sheets is connected (green checkmark in Settings)
- ✅ OpenAI API key is added in Settings
- ✅ Your Google Sheet has Website, FirstName, and Company columns

## 🎯 Testing Your Setup

### 1. Test Backend Health
```bash
API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
curl "$API_URL/api/health"
# Should return: {"status":"healthy"}
```

### 2. Test Authentication
```bash
API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
curl -X POST "$API_URL/api/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","name":"Test User"}'
# Should return access token and user info
```

### 3. Test Google OAuth Status
After logging in via the UI, check Google connection:
```bash
API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
TOKEN="your-jwt-token-from-login"
curl "$API_URL/api/oauth/google/status" \
  -H "Authorization: Bearer $TOKEN"
# Should return: {"connected": true/false}
```

## 🔧 Common Issues

### Issue: "Missing required parameter: client_id"
**Solution**: Google OAuth credentials not configured
1. Check `/app/backend/.env` has GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET
2. Restart backend: `sudo supervisorctl restart backend`

### Issue: "Redirect URI mismatch"
**Solution**: Redirect URI doesn't match Google Console
1. In Google Console, verify redirect URI matches EXACTLY
2. Format: `https://your-domain/api/oauth/google/callback`
3. No trailing slash, must use HTTPS

### Issue: "Cannot access spreadsheets"
**Solution**: Test user not added or scopes missing
1. Add your Gmail to "Test users" in OAuth consent screen
2. Ensure scopes include `spreadsheets` and `drive.readonly`
3. Disconnect and reconnect Google in Settings

## 💡 Pro Tips

1. **Preview First**: Always run preview mode (3 rows) before full run to test prompts
2. **Credit Usage**: 1 credit = 1 row processed (even if scraping fails)
3. **Smart Scraping**: The app automatically picks the best pages (About, Services, Products)
4. **Retry Failed**: Use "Retry Failed" to only reprocess rows that failed
5. **Prompt Templates**: Start with Logistics or Industrial presets, then customize

## 🎉 You're Ready!

Once Google OAuth is configured and you've connected your account, you can:
- Process hundreds of leads in minutes
- Generate personalized icebreakers at scale
- Write results directly back to Google Sheets
- Track progress with live dashboard

**Need Help?** Check `/app/README.md` for detailed documentation.

---

**Happy Personalizing! 🚀**
