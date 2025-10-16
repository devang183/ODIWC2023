# Vercel Deployment Troubleshooting

## Current Issue: Pandas Import Error (Cache Problem)

The error you're seeing indicates Vercel is using an **old cached version** of your code, even though the latest code is correct.

### ✅ Verified: Your Local Code is Correct
- `app.py` - No pandas import ✅
- `requirements.txt` - No pandas dependency ✅
- Latest commit pushed to GitHub ✅

### 🔧 Solution: Force Vercel to Redeploy

Choose one of these methods:

---

## Method 1: Redeploy from Vercel Dashboard (Easiest)

1. Go to https://vercel.com/dashboard
2. Click on your project
3. Go to the **"Deployments"** tab
4. Find the latest deployment
5. Click the **three dots (...)** menu
6. Click **"Redeploy"**
7. Check **"Use existing Build Cache"** should be **UNCHECKED** ⚠️
8. Click **"Redeploy"**

This forces Vercel to rebuild from scratch without using cache.

---

## Method 2: Trigger New Deployment with Dummy Commit

If Method 1 doesn't work, force a new build:

```bash
# Make a small change to trigger rebuild
echo "# Updated for Vercel" >> README.md

# Commit and push
git add README.md
git commit -m "Trigger Vercel rebuild - clear cache"
git push origin main
```

This will trigger a fresh deployment automatically.

---

## Method 3: Clear Build Cache via Vercel CLI

```bash
# Install Vercel CLI if not already installed
npm install -g vercel

# Login
vercel login

# Link to your project
vercel link

# Deploy with force flag (clears cache)
vercel --force --prod
```

---

## Method 4: Delete and Redeploy Project (Nuclear Option)

If nothing else works:

1. Go to Vercel Dashboard
2. Go to your project **Settings**
3. Scroll to bottom → **"Delete Project"**
4. Confirm deletion
5. Import the project again from GitHub
6. **IMPORTANT**: Add the `MONGO_URI` environment variable again
7. Deploy

---

## Verification Steps After Redeployment

Once redeployed, verify in Vercel logs:

1. Go to **Deployments** tab
2. Click on the latest deployment
3. Click **"Building"** or **"Logs"**
4. You should see:
   ```
   Installing dependencies from requirements.txt
   Flask==2.3.3
   flask-cors==4.0.0
   pymongo==4.5.0
   python-dotenv==1.0.0
   dnspython==2.4.2
   ```
5. **NO pandas should appear** ✅

---

## Common Vercel Deployment Issues

### Issue: Environment Variable Not Set

**Symptom**: MongoDB connection errors

**Fix**:
1. Go to Settings → Environment Variables
2. Add `MONGO_URI` with your connection string
3. Scope: Production, Preview, Development (all selected)
4. Redeploy

### Issue: Build Cache Stuck

**Symptom**: Old code still running despite new commits

**Fix**: Use Method 1 or 2 above (force rebuild)

### Issue: MongoDB Network Access

**Symptom**: Connection timeout errors

**Fix**:
1. Go to MongoDB Atlas → Network Access
2. Add IP: `0.0.0.0/0` (Allow from anywhere)
3. This is required for Vercel's dynamic IPs

---

## Expected Successful Deployment Log

```
> Building...
> Installing Python dependencies from requirements.txt
> Collecting Flask==2.3.3
> Collecting flask-cors==4.0.0
> Collecting pymongo==4.5.0
> Collecting python-dotenv==1.0.0
> Collecting dnspython==2.4.2
> Successfully installed Flask-2.3.3 flask-cors-4.0.0 pymongo-4.5.0 ...
> Build completed successfully
```

**No pandas, no numpy** should appear in the logs!

---

## Quick Test After Deployment

Visit your Vercel URL and test:
- [ ] Home page loads
- [ ] Dashboard shows statistics
- [ ] Players section loads
- [ ] Can filter by team/role
- [ ] Matches section loads
- [ ] Charts display
- [ ] Click player opens modal

---

## Still Having Issues?

### Check These Files in Your GitHub Repository

1. Visit your GitHub repo in browser
2. Check `app.py` line 1-10:
   ```python
   from flask import Flask, render_template, jsonify, request
   from flask_cors import CORS
   from pymongo import MongoClient
   import os
   from dotenv import load_dotenv
   import re
   ```
   Should **NOT** have `import pandas as pd`

3. Check `requirements.txt`:
   ```
   Flask==2.3.3
   flask-cors==4.0.0
   pymongo==4.5.0
   python-dotenv==1.0.0
   dnspython==2.4.2
   ```
   Should **NOT** have `pandas`

If files are correct on GitHub but Vercel still fails, use **Method 1** to force rebuild without cache.

---

## Contact Support

If all methods fail:
1. Screenshot the error from Vercel logs
2. Verify files on GitHub match expected content
3. Check Vercel's status page: https://www.vercel-status.com/
4. Create support ticket with Vercel

---

## Success Indicators

✅ Deployment shows "Ready" status
✅ No pandas/numpy in build logs
✅ Application loads without errors
✅ MongoDB connection works
✅ All API endpoints respond

---

**Next Step**: Try **Method 1** first (Redeploy from Dashboard) and make sure to uncheck "Use existing Build Cache"
