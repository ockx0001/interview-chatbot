# Setting Up Google Drive Storage for Interview Conversations

## Why Google Drive?

Railway's filesystem is ephemeral - files are lost on restart. Google Drive provides persistent cloud storage with **service accounts** that never expire (unlike access tokens). Much simpler than OneDrive or AWS S3!

## Step 1: Create Google Cloud Project

1. **Go to Google Cloud Console**
   - Visit https://console.cloud.google.com/
   - Sign in with your Google account

2. **Create New Project**
   - Click "Select a project" → "New Project"
   - **Project name**: `Interview Chatbot`
   - Click "**Create**"

## Step 2: Enable Google Drive API

1. **Navigate to APIs & Services**
   - In your project, go to "APIs & Services" → "Library"
   - Search for "**Google Drive API**"
   - Click on it → Click "**Enable**"

## Step 3: Create Service Account

1. **Go to Service Accounts**
   - Navigate to "APIs & Services" → "Credentials"
   - Click "**Create Credentials**" → "**Service account**"

2. **Configure Service Account**
   - **Service account name**: `interview-chatbot-drive`
   - **Service account ID**: Auto-generated (or customize)
   - Click "**Create and Continue**"

3. **Grant Role** (optional)
   - Skip or grant "Editor" role
   - Click "**Continue**" → "**Done**"

## Step 4: Create Service Account Key

1. **Create Key**
   - Click on the service account you just created
   - Go to "**Keys**" tab
   - Click "**Add Key**" → "**Create new key**"
   - Select "**JSON**"
   - Click "**Create**"

2. **Download JSON File**
   - A JSON file will download automatically
   - **IMPORTANT**: Save this file - you'll need it!
   - It contains your service account credentials

## Step 5: Create Google Drive Folder and Share It

1. **Create a Folder in Google Drive**
   - Go to https://drive.google.com
   - Create a new folder called "InterviewChatbot" (or any name)
   - Right-click the folder → "**Share**"

2. **Share with Service Account**
   - In the downloaded JSON file, find the `"client_email"` field
   - It looks like: `interview-chatbot-drive@your-project.iam.gserviceaccount.com`
   - Copy this email
   - In the share dialog, paste the email
   - Give "**Editor**" permission
   - Click "**Send**" (or "Share")

3. **Get Folder ID**
   - Open the folder you just shared
   - Look at the URL: `https://drive.google.com/drive/folders/FOLDER_ID_HERE`
   - Copy the **FOLDER_ID** (long string after `/folders/`)
   - Save this - you'll need it!

## Step 6: Add Environment Variables to Railway

1. **Go to Railway Project**
   - Open your `interview-chatbot` service
   - Go to "**Variables**" tab

2. **Add Google Drive Configuration Variables**
   Add these environment variables:

   | Variable Name | Value |
   |--------------|-------|
   | `GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON` | The entire contents of the JSON file (see below) |
   | `GOOGLE_DRIVE_FOLDER_ID` | The folder ID from Step 5 |
   | `GOOGLE_DRIVE_FILE_NAME` | `conversations.json` (optional, defaults to this) |

3. **Important: Format the JSON Correctly**
   - Open the downloaded JSON file
   - Copy the **entire contents** of the file
   - In Railway, paste it as a **single-line** value (no newlines)
   - Or use the JSON as-is but escape quotes properly
   
   **Example**: The value should look like:
   ```
   {"type":"service_account","project_id":"your-project",...}
   ```

4. **Save Variables**
   - Click "**Add**" for each variable
   - Railway will auto-deploy

## Step 7: Verify Setup

1. **Wait for Deployment**
   - Go to "Deployments" tab
   - Wait for deployment to complete (green checkmark)

2. **Test Health Endpoint**
   - Visit: `YOUR_RAILWAY_URL/health`
   - Check `storage_config.type` - should show `"Google Drive"`
   - Check `storage_config.gdrive_configured` - should be `true`

3. **Test Interview**
   - Complete an interview
   - Check Google Drive folder
   - You should see `conversations.json` file appear

## How It Works

- **Without Google Drive configured**: Uses local file (ephemeral on Railway)
- **With Google Drive configured**: Saves/loads from Google Drive folder (persistent)

The code automatically:
- Creates the file if it doesn't exist
- Updates existing files
- Falls back to local file if Google Drive fails

## Important Notes

### Service Account Never Expires
- Unlike access tokens, service accounts **never expire**
- Once set up, you don't need to refresh tokens
- Much easier than OneDrive!

### Security
- Never commit the JSON file to Git (already in `.gitignore`)
- Store JSON securely in Railway environment variables
- Only share the folder with your service account email

### Folder Sharing
- **Critical**: The folder must be shared with the service account email
- Without sharing, the service account can't access the folder
- Check sharing if you get permission errors

## Troubleshooting

**Problem**: `gdrive_configured: false`
- **Solution**: Check that `GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON` is set correctly
- Make sure JSON is valid (single-line format works best in Railway)

**Problem**: 403 Forbidden errors
- **Solution**: Check that you shared the folder with the service account email
- Verify folder ID is correct

**Problem**: 404 File not found
- **Solution**: File will be created automatically on first save
- This is normal if the file doesn't exist yet

**Problem**: JSON parsing errors
- **Solution**: Make sure JSON is properly formatted as single-line in Railway
- Or escape quotes properly if using multi-line format

## Benefits Over OneDrive/AWS S3

✅ **No token expiration** - Service accounts never expire  
✅ **Simple setup** - Just share a folder  
✅ **Easy to access** - Files visible in Google Drive  
✅ **Free tier** - Google Drive free tier is generous  
✅ **No periodic maintenance** - Set it and forget it

## Cost

- **Google Drive free tier**: 15 GB free storage
- **API calls**: Free for reasonable usage
- For interview conversations (JSON files), you'll stay well within free limits

This is much simpler than OneDrive (no token refresh) or AWS S3 (no bucket setup)!

