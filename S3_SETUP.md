# Setting Up AWS S3 Storage for Interview Conversations

## Why S3?

Railway's filesystem is ephemeral - files are lost on restart. AWS S3 provides persistent cloud storage that survives deployments and restarts.

## Step 1: Create AWS S3 Bucket

1. **Sign in to AWS Console**
   - Go to https://console.aws.amazon.com/
   - Sign in or create an account (free tier available)

2. **Navigate to S3**
   - Search for "S3" in AWS Console
   - Click "Create bucket"

3. **Configure Bucket**
   - **Bucket name**: `interview-chatbot-conversations` (or any unique name)
   - **Region**: Choose a region (e.g., `us-east-1`)
   - **Block all public access**: ✅ Keep checked (private bucket)
   - **Bucket Versioning**: Optional (disable for now)
   - **Default encryption**: Optional (can enable later)
   - Click "**Create bucket**"

4. **Note Your Bucket Details**
   - Bucket name: `interview-chatbot-conversations`
   - Region: `us-east-1` (or your chosen region)

## Step 2: Create IAM User for S3 Access

1. **Go to IAM Console**
   - In AWS Console, search for "IAM"
   - Click "Users" → "Create user"

2. **Create User**
   - **Username**: `interview-chatbot-s3-user`
   - Click "**Next**"

3. **Set Permissions**
   - Select "**Attach policies directly**"
   - Search for "S3" and select "**AmazonS3FullAccess**" (or create a custom policy with only PutObject/GetObject on your bucket)
   - Click "**Next**" → "**Create user**"

4. **Get Access Keys**
   - Click on the user you just created
   - Go to "Security credentials" tab
   - Click "**Create access key**"
   - Select "**Application running outside AWS**"
   - Click "**Next**" → "**Create access key**"
   - **IMPORTANT**: Copy both:
     - **Access key ID** (starts with `AKIA...`)
     - **Secret access key** (show once - save it!)
   - Click "**Done**"

## Step 3: Add Environment Variables to Railway

1. **Go to Railway Project**
   - Open your `interview-chatbot` service
   - Go to "**Variables**" tab

2. **Add S3 Configuration Variables**
   Add these environment variables:

   | Variable Name | Value |
   |--------------|-------|
   | `AWS_S3_BUCKET` | `interview-chatbot-conversations` (your bucket name) |
   | `AWS_S3_KEY` | `conversations.json` (filename in S3) |
   | `AWS_ACCESS_KEY_ID` | `AKIA...` (your access key ID) |
   | `AWS_SECRET_ACCESS_KEY` | `your-secret-key` (your secret access key) |
   | `AWS_REGION` | `us-east-1` (your bucket region) |

3. **Save Variables**
   - Click "**Add**" for each variable
   - Railway will auto-deploy

## Step 4: Verify Setup

1. **Wait for Deployment**
   - Go to "Deployments" tab
   - Wait for deployment to complete (green checkmark)

2. **Test Health Endpoint**
   - Visit: `YOUR_RAILWAY_URL/health`
   - Check `storage_config.type` - should show `"S3"`
   - Check `storage_config.s3_client_configured` - should be `true`

3. **Test Interview**
   - Complete an interview
   - Check AWS S3 Console
   - Your bucket should have `conversations.json` file

## How It Works

- **Without S3 configured**: Uses local file (ephemeral on Railway)
- **With S3 configured**: Saves/loads from S3 bucket (persistent)

The code automatically:
- Detects if `AWS_S3_BUCKET` is set
- Uses S3 if available, falls back to local file if not
- Handles S3 errors gracefully (falls back to local)

## Cost Estimate

**AWS S3 Free Tier:**
- 5 GB storage
- 20,000 GET requests
- 2,000 PUT requests
- First 12 months free

For interview conversations (JSON files), you'll likely stay well within free tier limits.

## Security Best Practices

1. **Never commit access keys to Git**
   - Keep them in Railway environment variables only
   - Already in `.gitignore`

2. **Use IAM Policy**
   - Create a custom IAM policy with minimal permissions:
     - `s3:PutObject` on your bucket
     - `s3:GetObject` on your bucket
   - Don't use full S3 access if not needed

3. **Enable Bucket Encryption**
   - Go to S3 bucket → Properties → Encryption
   - Enable server-side encryption

## Troubleshooting

**Problem**: `s3_client_configured: false`
- **Solution**: Check that all 4 environment variables are set correctly in Railway

**Problem**: Access Denied errors
- **Solution**: Verify IAM user has correct permissions on the bucket

**Problem**: Bucket not found
- **Solution**: Check bucket name and region match environment variables

**Problem**: Files not appearing in S3
- **Solution**: Check Railway logs for S3 errors, verify bucket permissions

## Alternative: Other Cloud Storage

If you prefer not to use AWS S3, you can use:
- **Google Cloud Storage** (requires code changes)
- **Azure Blob Storage** (requires code changes)
- **DigitalOcean Spaces** (S3-compatible)

Let me know if you'd like to switch to a different provider!

