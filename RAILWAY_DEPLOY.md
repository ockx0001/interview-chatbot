# Railway Deployment Guide

## Quick Start

### Step 1: Push to GitHub (if not already)
```bash
git init  # if you haven't already
git add .
git commit -m "Initial commit"
git remote add origin <your-github-repo-url>
git push -u origin main
```

### Step 2: Deploy on Railway

1. **Sign up/Login**: Go to [railway.app](https://railway.app) and sign in with GitHub

2. **Create New Project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway will auto-detect Python

3. **Set Environment Variables**:
   - In your Railway project dashboard, go to "Variables" tab
   - Add: `OPENAI_API_KEY` = `your-openai-api-key-here`
   - (Optional): `PORT` will be set automatically by Railway
   - (Optional): `DEBUG` = `False` for production

4. **Deploy**:
   - Railway will automatically build and deploy
   - You'll see build logs in real-time
   - Once deployed, Railway will provide a public URL (e.g., `https://your-app-name.railway.app`)

### Step 3: Get Your Public URL

- Railway will generate a URL automatically
- You can also set a custom domain in the "Settings" tab
- Share this URL with your interview participants

## Files Included

- ✅ `requirements.txt` - Python dependencies
- ✅ `Procfile` - Railway deployment configuration
- ✅ `runtime.txt` - Python version (optional, Railway auto-detects)
- ✅ `.gitignore` - Prevents committing sensitive data

## Environment Variables Needed

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | ✅ Yes |
| `PORT` | Port number (auto-set by Railway) | ❌ No |
| `DEBUG` | Debug mode (`True`/`False`) | ❌ No |

## Troubleshooting

- **Build fails**: Check that all dependencies in `requirements.txt` are correct
- **App won't start**: Verify `OPENAI_API_KEY` is set in Railway variables
- **502 errors**: Check Railway logs for Python errors

## Cost

- Railway offers a free tier with $5 credit monthly
- Check Railway pricing for your usage needs

