# Setting Up Persistent Storage on Railway

## Why You Need This

Railway's container filesystem is **ephemeral** - any files saved to the container (like `conversations.json`) will be lost when the container restarts or redeploys. To persist your interview data, you need to use Railway's **Persistent Volume**.

## Step-by-Step Setup

### Step 1: Add a Persistent Volume in Railway

1. **Go to your Railway project dashboard**
   - Navigate to your `interview-chatbot` project
   - Click on your service (the one running the Flask app)

2. **Go to the "Storage" tab**
   - Click on the "Storage" tab in your service settings

3. **Create a new volume**
   - Click "**+ New Volume**" or "**Add Volume**"
   - Name it: `conversations-storage` (or any name you prefer)
   - Size: Railway will give you a default (usually 1GB is fine for JSON files)
   - Mount path: `/data` (this is the default - Railway will set this)
   - Click "**Create**"

4. **Note the mount path**
   - Railway will show you the mount path (usually `/data`)
   - This is where files will persist

### Step 2: Set Environment Variable

1. **Go to the "Variables" tab** in your Railway service

2. **Add the volume path as an environment variable:**
   - Variable name: `RAILWAY_VOLUME_MOUNT_PATH`
   - Variable value: `/data` (or whatever Railway shows as the mount path)
   - Click "**Add**"

### Step 3: Redeploy

1. **Trigger a redeploy:**
   - Go to "Deployments" tab
   - Click "**Redeploy**" or wait for automatic deployment after the env var change

2. **Verify it's working:**
   - The app will now save `conversations.json` to `/data/conversations.json`
   - This file will persist across deployments and restarts

## How It Works

- **Without persistent volume:** Files saved in container → Lost on restart
- **With persistent volume:** Files saved in `/data` → Persist across restarts

The code has been updated to:
- Check for `RAILWAY_VOLUME_MOUNT_PATH` environment variable
- Use that path if set (for Railway)
- Fall back to the current directory if not set (for local development)

## Accessing Your Data

### Option 1: Download via Railway CLI

If Railway CLI is installed:
```bash
railway connect
railway volume download conversations-storage
```

### Option 2: Access via Railway Dashboard

Some Railway plans allow you to browse volume contents in the dashboard.

### Option 3: Add an Export Endpoint

The code already has `/export_mapping` endpoint - you can access your conversation data via:
- `https://your-app.railway.app/export_mapping`

## Important Notes

- **Volume size:** Each volume has a size limit based on your Railway plan
- **Backups:** Consider backing up your `conversations.json` regularly
- **Cost:** Persistent volumes may have additional costs on some Railway plans

## Troubleshooting

**Problem:** Files still disappear after redeploy
- **Solution:** Make sure `RAILWAY_VOLUME_MOUNT_PATH` is set correctly
- Check Railway logs for any file permission errors

**Problem:** Permission denied errors
- **Solution:** Railway volumes should have write permissions by default
- Check that the mount path matches what Railway shows

**Problem:** Can't find the volume in dashboard
- **Solution:** Not all Railway plans show volume contents in UI
- Use the export endpoint or Railway CLI to access files

