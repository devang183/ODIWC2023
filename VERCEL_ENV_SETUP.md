# How to Add MONGO_URI Environment Variable in Vercel

## The Error You're Seeing
```
Environment Variable "MONGO_URI" references Secret "mongo_uri", which does not exist.
```

This error means you need to add the `MONGO_URI` environment variable directly in Vercel's dashboard.

---

## Step-by-Step Solution

### Method 1: Add During Initial Deployment (Recommended)

When deploying for the first time:

1. **Import your GitHub repository** in Vercel
2. In the configuration screen, find **"Environment Variables"** section
3. Click **"Add"** or **"Add New"**
4. Enter the following:

   **Key (Name):**
   ```
   MONGO_URI
   ```

   **Value:**
   ```
   mongodb+srv://kankariadevang:FRg8Euj7xssSKpob@devangdb.2ckz3bw.mongodb.net/?retryWrites=true&w=majority&appName=devangDB
   ```

   **Environments to apply:**
   - ✅ Production
   - ✅ Preview
   - ✅ Development

5. Click **"Save"** or **"Add"**
6. Click **"Deploy"**

---

### Method 2: Add to Existing Project

If your project is already deployed but failing:

1. Go to https://vercel.com/dashboard
2. Click on your project (ODIWC2023)
3. Click **"Settings"** in the top menu
4. Click **"Environment Variables"** in the left sidebar
5. Click **"Add New"** button
6. Fill in the form:

   **Key:**
   ```
   MONGO_URI
   ```

   **Value:** (paste the entire connection string)
   ```
   mongodb+srv://kankariadevang:FRg8Euj7xssSKpob@devangdb.2ckz3bw.mongodb.net/?retryWrites=true&w=majority&appName=devangDB
   ```

   **Select Environments:**
   - ✅ Check "Production"
   - ✅ Check "Preview"
   - ✅ Check "Development"

7. Click **"Save"**
8. Go back to **"Deployments"** tab
9. Click **"Redeploy"** on the latest deployment
10. **IMPORTANT:** Uncheck "Use existing Build Cache"
11. Click **"Redeploy"**

---

## Visual Guide

```
Vercel Dashboard
├── Your Project (ODIWC2023)
│   ├── Deployments
│   ├── Analytics
│   ├── Settings  ← Click here
│       ├── General
│       ├── Domains
│       ├── Environment Variables  ← Then click here
│           └── [Add New] ← Click this button
```

---

## Screenshot of What You Should See

When you click "Environment Variables", you should see:

```
┌────────────────────────────────────────────┐
│  Environment Variables                      │
│                                            │
│  [Add New]                                 │
│                                            │
│  Key: MONGO_URI                            │
│  Value: mongodb+srv://...                  │
│  Environment: ☑ Production                 │
│              ☑ Preview                     │
│              ☑ Development                 │
│                                            │
│  [Save]                                    │
└────────────────────────────────────────────┘
```

---

## Common Mistakes to Avoid

❌ **Don't** put environment variables in `vercel.json` file
❌ **Don't** commit your `.env` file to GitHub
❌ **Don't** forget to select all three environments
❌ **Don't** add quotes around the connection string
❌ **Don't** forget to redeploy after adding the variable

✅ **Do** add the variable in Vercel Dashboard
✅ **Do** keep `.env` in `.gitignore`
✅ **Do** select Production, Preview, and Development
✅ **Do** paste the connection string without quotes
✅ **Do** redeploy after adding/changing variables

---

## Verify Environment Variable is Set

After adding the variable:

1. Go to **Settings** → **Environment Variables**
2. You should see:
   ```
   MONGO_URI
   Value: mongodb+srv://••••••••
   Environments: Production, Preview, Development
   ```

3. The value will be masked (••••••) for security - this is normal!

---

## Your MongoDB Connection String

Copy this exact string (no quotes, no spaces):

```
mongodb+srv://kankariadevang:FRg8Euj7xssSKpob@devangdb.2ckz3bw.mongodb.net/?retryWrites=true&w=majority&appName=devangDB
```

---

## MongoDB Atlas Network Access

Make sure MongoDB allows connections from Vercel:

1. Go to MongoDB Atlas (https://cloud.mongodb.com)
2. Click **"Network Access"** in the left sidebar
3. Click **"Add IP Address"**
4. Select **"Allow Access from Anywhere"**
5. IP Address: `0.0.0.0/0`
6. Click **"Confirm"**

This is required because Vercel uses dynamic IPs.

---

## Test if Environment Variable Works

After deployment, check the Vercel function logs:

1. Go to **Deployments** tab
2. Click on your latest deployment
3. Click **"Functions"** or **"Logs"**
4. You should see:
   ```
   Connecting to MongoDB with URI: mongodb+srv://kankariadevang:FRg8Euj7xssSKpob...
   Successfully connected to MongoDB server
   ```

If you see this, the environment variable is working! ✅

---

## Still Getting the Error?

If you still see the secret reference error:

1. **Delete the project** from Vercel (Settings → Delete Project)
2. **Re-import** from GitHub
3. **Add the environment variable** during import (Method 1)
4. Deploy

This ensures a completely fresh start with no cached configurations.

---

## Quick Checklist

- [ ] Removed `"env"` section from `vercel.json`
- [ ] Added `MONGO_URI` in Vercel Dashboard
- [ ] Selected all 3 environments (Production, Preview, Development)
- [ ] Redeployed the application
- [ ] Unchecked "Use existing Build Cache" when redeploying
- [ ] MongoDB Atlas allows connections from `0.0.0.0/0`

Once all boxes are checked, your deployment should succeed! ✅
