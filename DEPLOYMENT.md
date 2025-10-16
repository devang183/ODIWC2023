# Deployment Guide for Vercel

This guide will help you deploy your ODI World Cup 2023 Dashboard to Vercel.

## Prerequisites

- GitHub account
- Vercel account (sign up at https://vercel.com)
- MongoDB Atlas database (already configured)

## Step 1: Push Code to GitHub

1. Initialize git repository (if not already done):
   ```bash
   git init
   ```

2. Add all files:
   ```bash
   git add .
   ```

3. Commit your changes:
   ```bash
   git commit -m "Initial commit - Ready for Vercel deployment"
   ```

4. Create a new repository on GitHub

5. Add remote and push:
   ```bash
   git remote add origin <your-github-repo-url>
   git branch -M main
   git push -u origin main
   ```

## Step 2: Deploy to Vercel

### Option A: Using Vercel Dashboard (Recommended)

1. Go to https://vercel.com and sign in
2. Click **"Add New Project"**
3. Click **"Import Git Repository"**
4. Select your GitHub repository
5. Configure the project:
   - **Framework Preset**: Other
   - **Root Directory**: `./` (leave as is)
   - **Build Command**: (leave empty)
   - **Output Directory**: (leave empty)

6. **Add Environment Variable**:
   - Click **"Environment Variables"**
   - Add variable:
     - **Name**: `MONGO_URI`
     - **Value**: Your MongoDB connection string from `.env` file
     ```
     mongodb+srv://kankariadevang:FRg8Euj7xssSKpob@devangdb.2ckz3bw.mongodb.net/?retryWrites=true&w=majority&appName=devangDB
     ```
   - Click **"Add"**

7. Click **"Deploy"**
8. Wait for deployment to complete (usually 1-2 minutes)

### Option B: Using Vercel CLI

1. Install Vercel CLI:
   ```bash
   npm install -g vercel
   ```

2. Login to Vercel:
   ```bash
   vercel login
   ```

3. Deploy from project directory:
   ```bash
   cd /Users/devangkankaria/Downloads/ODIWC2023
   vercel
   ```

4. Follow the prompts:
   - Link to existing project? **No**
   - Project name: **odiwc2023** (or your choice)
   - Which directory? **./`**
   - Override settings? **No**

5. Add environment variable:
   ```bash
   vercel env add MONGO_URI
   ```
   Paste your MongoDB URI when prompted

6. Deploy to production:
   ```bash
   vercel --prod
   ```

## Step 3: Verify Deployment

1. Once deployed, Vercel will provide a URL like: `https://odiwc2023.vercel.app`
2. Open the URL in your browser
3. Test the following:
   - ✅ Dashboard loads with statistics
   - ✅ Players section loads
   - ✅ Matches section loads
   - ✅ Dropdowns filter correctly
   - ✅ Charts display properly
   - ✅ Click on player opens modal with performance
   - ✅ Click on chart bars highlights rows

## Troubleshooting

### Issue: "Module not found" errors

**Solution**: Make sure all dependencies are in `requirements.txt`

### Issue: MongoDB connection fails

**Solution**:
1. Check environment variable is set correctly in Vercel dashboard
2. Verify MongoDB Atlas allows connections from all IPs (0.0.0.0/0)
   - Go to MongoDB Atlas > Network Access
   - Add IP Address > Allow Access from Anywhere

### Issue: API calls return 404

**Solution**:
- Verify `vercel.json` routes are configured correctly
- Check that API endpoints work locally first

### Issue: Static files not loading

**Solution**:
- Ensure templates folder exists
- Check Flask template rendering is working

## Post-Deployment

### Custom Domain (Optional)

1. Go to your Vercel project dashboard
2. Click **"Settings"** > **"Domains"**
3. Add your custom domain
4. Follow DNS configuration instructions

### Environment Variables

To update environment variables after deployment:
1. Go to Vercel Dashboard > Your Project
2. Click **"Settings"** > **"Environment Variables"**
3. Edit or add new variables
4. **Redeploy** for changes to take effect

### Automatic Deployments

Vercel automatically deploys when you push to GitHub:
- Push to `main` branch → Production deployment
- Push to other branches → Preview deployment

## Important Notes

1. **`.env` file is NOT deployed** - It's in `.gitignore` for security
2. **Environment variables must be set in Vercel** - Required for MongoDB connection
3. **No pandas dependency** - Removed to avoid binary compatibility issues
4. **API calls use relative URLs** - Works both locally and on Vercel

## Useful Commands

```bash
# Check deployment status
vercel ls

# View deployment logs
vercel logs

# Remove a deployment
vercel rm <deployment-url>

# Open project in browser
vercel open
```

## Support

If you encounter issues:
1. Check Vercel deployment logs
2. Review MongoDB Atlas connection settings
3. Ensure all environment variables are set correctly
4. Test locally before deploying

## Files Modified for Vercel Deployment

- ✅ `app.py` - Removed pandas import
- ✅ `requirements.txt` - Removed pandas dependency
- ✅ `vercel.json` - Added Vercel configuration
- ✅ `templates/index.html` - Updated API URL to be environment-aware
- ✅ `.gitignore` - Added Vercel-specific entries

Your application is now ready for deployment! 🚀
