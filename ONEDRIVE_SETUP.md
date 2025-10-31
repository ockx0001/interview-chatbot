# Setting Up Microsoft OneDrive Storage for Interview Conversations

## Why OneDrive?

Railway's filesystem is ephemeral - files are lost on restart. Microsoft OneDrive provides persistent cloud storage that survives deployments and restarts, and integrates easily with Microsoft accounts.

## Step 1: Register an Azure AD Application

1. **Go to Azure Portal**
   - Visit https://portal.azure.com/
   - Sign in with your Microsoft account

2. **Navigate to Azure Active Directory**
   - Search for "Azure Active Directory" in the portal
   - Click "App registrations" → "New registration"

3. **Register Application**
   - **Name**: `Interview Chatbot OneDrive`
   - **Supported account types**: "Accounts in any organizational directory and personal Microsoft accounts"
   - **Redirect URI**: 
     - Platform: "Web"
     - URI: `http://localhost:5003/callback` (for local testing)
     - Click "Register"

4. **Note Application Details**
   - **Application (client) ID**: Copy this (you'll need it)
   - **Directory (tenant) ID**: Copy this too

## Step 2: Configure API Permissions

1. **In your app registration, go to "API permissions"**
   - Click "+ Add a permission"
   - Select "Microsoft Graph"
   - Select "Delegated permissions"

2. **Add Permissions**
   Add these permissions:
   - `Files.ReadWrite` - Read and write files in user's OneDrive
   - `User.Read` - Sign in and read user profile

3. **Grant Admin Consent**
   - Click "Grant admin consent for [your tenant]"
   - Click "Yes" to confirm

## Step 3: Create Client Secret

1. **Go to "Certificates & secrets"**
   - Click "+ New client secret"
   - **Description**: `Interview Chatbot Secret`
   - **Expires**: Choose an expiration (6 months, 1 year, or never)
   - Click "Add"

2. **Copy the Secret Value**
   - **IMPORTANT**: Copy the "Value" immediately (shown once only!)
   - Save this along with your Application ID

## Step 4: Get Access Token

You have two options:

### Option A: Use a Long-Lived Refresh Token (Recommended)

1. **Create a simple script or use a tool to get tokens**
   - You'll need to authenticate once to get a refresh token
   - Then refresh tokens periodically (they last up to 90 days)

2. **Use Microsoft Graph Explorer** (Easier)
   - Go to https://developer.microsoft.com/en-us/graph/graph-explorer
   - Sign in with your Microsoft account
   - Grant permissions when prompted
   - Copy the access token from the token box

### Option B: Use App-Only Authentication (For Production)

For production, you'll want to use app-only authentication with client credentials flow. This requires a bit more setup.

## Step 5: Add Environment Variables to Railway

1. **Go to Railway Project**
   - Open your `interview-chatbot` service
   - Go to "**Variables**" tab

2. **Add OneDrive Configuration Variables**
   Add these environment variables:

   | Variable Name | Value |
   |--------------|-------|
   | `ONEDRIVE_ACCESS_TOKEN` | `your-access-token` (from Step 4) |
   | `ONEDRIVE_FILE_NAME` | `conversations.json` (optional, defaults to this) |
   | `ONEDRIVE_FOLDER_PATH` | `InterviewChatbot` (optional, defaults to this) |

3. **Save Variables**
   - Click "**Add**" for each variable
   - Railway will auto-deploy

## Step 6: Automate Token Refresh (Important!)

Access tokens expire (usually in 1 hour). You'll need to:

1. **Set up a refresh token mechanism**
   - Use the refresh token to get new access tokens
   - Or use app-only authentication for production

2. **Update Railway periodically**
   - When tokens expire, update `ONEDRIVE_ACCESS_TOKEN` in Railway
   - Or set up an automated process to refresh tokens

## How It Works

- **Without OneDrive configured**: Uses local file (ephemeral on Railway)
- **With OneDrive configured**: Saves/loads from OneDrive (persistent)

The code automatically:
- Creates the folder if it doesn't exist
- Creates the file if it doesn't exist
- Updates existing files
- Falls back to local file if OneDrive fails

## Important Notes

### Token Expiration
- Access tokens expire in 1 hour
- Refresh tokens last up to 90 days
- For production, set up automatic token refresh

### Security
- Never commit tokens to Git (already in `.gitignore`)
- Store tokens securely in Railway environment variables
- Consider using Azure Key Vault for production

### Folder Structure
- Files are saved to: `/InterviewChatbot/conversations.json`
- Folder is created automatically if it doesn't exist

## Alternative: Simplified Setup (Using Personal Account)

If you just want to test quickly with a personal Microsoft account:

1. Go to https://developer.microsoft.com/en-us/graph/graph-explorer
2. Sign in with your Microsoft account
3. Click "Sign in with Microsoft"
4. Grant permissions for "Files.ReadWrite"
5. Copy the access token from the token box
6. Add `ONEDRIVE_ACCESS_TOKEN` to Railway
7. The token will expire in 1 hour - you'll need to refresh it periodically

## Troubleshooting

**Problem**: `onedrive_configured: false`
- **Solution**: Check that `ONEDRIVE_ACCESS_TOKEN` is set correctly
- Token might have expired - get a new one

**Problem**: 401 Unauthorized errors
- **Solution**: Token expired - refresh it and update Railway

**Problem**: 403 Forbidden errors
- **Solution**: Check API permissions in Azure AD app registration
- Make sure "Files.ReadWrite" permission is granted

**Problem**: File not appearing in OneDrive
- **Solution**: Check Railway logs for OneDrive errors
- Verify folder path and file name are correct

## Next Steps for Production

For production use, consider:

1. **App-only authentication** - Use client credentials flow instead of delegated permissions
2. **Automated token refresh** - Set up a service to refresh tokens automatically
3. **Azure Key Vault** - Store secrets securely instead of environment variables

Let me know if you need help with any of these steps!

