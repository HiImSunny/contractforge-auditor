# ContractForge Auditor — Deployment Guide

Complete step-by-step guide to deploy ContractForge Auditor to **Render** (backend) and **Vercel** (frontend).

---

## 📋 Prerequisites

Before you start, ensure you have:

1. **GitHub Account** — with the repo pushed to https://github.com/HiImSunny/contractforge-auditor
2. **Google AI Studio API Key** — from [Google AI Studio](https://aistudio.google.com/apikey)
3. **Render Account** — free tier at https://render.com
4. **Vercel Account** — free tier at https://vercel.com

---

## 🚀 Part 1: Deploy Backend to Render

### Step 1.1: Create Render Account & Connect GitHub

1. Go to https://render.com and sign up (or log in)
2. Click **"New +"** → **"Web Service"**
3. Select **"Deploy an existing repository"**
4. Connect your GitHub account and authorize Render
5. Select the repository: `HiImSunny/contractforge-auditor`
6. Click **"Connect"**

### Step 1.2: Configure Backend Service

In the Render dashboard, fill in the following:

| Field | Value |
|-------|-------|
| **Name** | `contractforge-auditor-backend` |
| **Environment** | `Docker` |
| **Region** | `Singapore` (or closest to you) |
| **Branch** | `master` |
| **Dockerfile Path** | `./Dockerfile` |
| **Docker Context** | `.` |
| **Plan** | `Free` |

### Step 1.3: Add Environment Variables

Click **"Advanced"** and add these environment variables:

```
GOOGLE_API_KEY = <your_google_api_key_here>
FRONTEND_ORIGIN = https://<your-frontend-domain>.vercel.app
GEMINI_MODEL = gemini-1.5-flash
PORT = 8000
```

**Important**: Replace `<your-frontend-domain>` with your actual Vercel domain (you'll get this after deploying frontend).

### Step 1.4: Deploy

1. Click **"Create Web Service"**
2. Render will automatically build and deploy from the `Dockerfile`
3. Wait for the build to complete (5-10 minutes)
4. Once deployed, you'll get a URL like: `https://contractforge-auditor-backend.onrender.com`
5. **Save this URL** — you'll need it for the frontend

### Step 1.5: Verify Backend is Running

```bash
curl https://contractforge-auditor-backend.onrender.com/api/health
```

Expected response:
```json
{"status": "ok"}
```

---

## 🎨 Part 2: Deploy Frontend to Vercel

### Step 2.1: Create Vercel Account & Connect GitHub

1. Go to https://vercel.com and sign up (or log in)
2. Click **"Add New..."** → **"Project"**
3. Select **"Import Git Repository"**
4. Connect your GitHub account and authorize Vercel
5. Select the repository: `HiImSunny/contractforge-auditor`
6. Click **"Import"**

### Step 2.2: Configure Frontend Project

In the Vercel import dialog, configure:

| Field | Value |
|-------|-------|
| **Project Name** | `contractforge-auditor` |
| **Framework Preset** | `Vite` |
| **Root Directory** | `./frontend` |
| **Build Command** | `npm run build` |
| **Output Directory** | `dist` |

### Step 2.3: Add Environment Variables

Before deploying, add environment variables:

1. In the Vercel import dialog, click **"Environment Variables"**
2. Add:

```
VITE_API_BASE_URL = https://contractforge-auditor-backend.onrender.com
```

3. Click **"Deploy"**

### Step 2.4: Wait for Deployment

Vercel will:
1. Install dependencies
2. Build the frontend
3. Deploy to CDN
4. Provide you with a URL like: `https://contractforge-auditor.vercel.app`

**Save this URL** — you'll need it to update the backend.

### Step 2.5: Verify Frontend is Running

Open `https://contractforge-auditor.vercel.app` in your browser. You should see the ContractForge Auditor dashboard.

---

## 🔄 Part 3: Update Backend with Frontend URL

Now that you have the frontend URL, update the backend environment variable:

### Step 3.1: Update Render Environment Variable

1. Go to https://render.com and select your backend service
2. Click **"Environment"**
3. Update `FRONTEND_ORIGIN` to your Vercel URL:
   ```
   FRONTEND_ORIGIN = https://contractforge-auditor.vercel.app
   ```
4. Click **"Save"**
5. Render will automatically redeploy with the new environment variable

### Step 3.2: Verify CORS is Working

Test that the frontend can communicate with the backend:

```bash
curl -H "Origin: https://contractforge-auditor.vercel.app" \
     -H "Access-Control-Request-Method: POST" \
     https://contractforge-auditor-backend.onrender.com/api/health
```

You should see CORS headers in the response.

---

## 🧪 Part 4: Test the Live Deployment

### Test 4.1: Upload a Contract

1. Open https://contractforge-auditor.vercel.app
2. Click **"Upload Contract"**
3. Upload one of the sample contracts from `backend/samples/contracts/`
4. Verify the contract is processed and displayed

### Test 4.2: Run Risk Simulation

1. In the dashboard, click **"Simulate Risk"**
2. Select a scenario (e.g., "Force Majeure")
3. Verify the risk score updates

### Test 4.3: Generate Report

1. Click **"Generate Report"**
2. Verify the PDF is generated and downloads correctly

---

## 🔧 Troubleshooting

### Issue: Frontend shows "API connection failed"

**Solution:**
1. Check that `VITE_API_BASE_URL` in Vercel environment variables is correct
2. Verify the backend is running: `curl https://contractforge-auditor-backend.onrender.com/api/health`
3. Check CORS headers are being sent correctly
4. Redeploy frontend: Go to Vercel → Project → Deployments → Click latest → "Redeploy"

### Issue: Backend deployment fails

**Solution:**
1. Check Render build logs: Go to Render → Service → Logs
2. Verify `GOOGLE_API_KEY` is set correctly
3. Ensure `Dockerfile` is in the root of the backend directory
4. Try redeploying: Go to Render → Service → Manual Deploy

### Issue: "GOOGLE_API_KEY not found" error

**Solution:**
1. Go to https://aistudio.google.com/apikey
2. Create a new API key if you don't have one
3. Copy the key
4. Update in Render: Environment → `GOOGLE_API_KEY` → Paste key → Save
5. Render will redeploy automatically

### Issue: Render service goes to sleep (free tier)

**Solution:**
- Free tier services spin down after 15 minutes of inactivity
- To keep it running, upgrade to a paid plan or use a monitoring service
- Alternatively, set up a cron job to ping the health endpoint every 10 minutes

---

## 📊 Monitoring & Logs

### View Backend Logs

```bash
# In Render dashboard
1. Select your service
2. Click "Logs"
3. View real-time logs
```

### View Frontend Logs

```bash
# In Vercel dashboard
1. Select your project
2. Click "Deployments"
3. Click the deployment
4. Click "Logs"
```

---

## 🔐 Security Checklist

Before going live, verify:

- [ ] `GOOGLE_API_KEY` is kept secret (never commit to GitHub)
- [ ] `FRONTEND_ORIGIN` is set to your actual Vercel domain
- [ ] CORS headers are configured correctly
- [ ] No sensitive data is logged
- [ ] Environment variables are not exposed in frontend code
- [ ] HTTPS is enforced (both Render and Vercel use HTTPS by default)

---

## 📝 Environment Variables Reference

### Backend (Render)

| Variable | Required | Example |
|----------|----------|---------|
| `GOOGLE_API_KEY` | ✅ Yes | `AIzaSyD...` |
| `FRONTEND_ORIGIN` | ✅ Yes | `https://contractforge-auditor.vercel.app` |
| `GEMINI_MODEL` | ❌ No | `gemini-1.5-flash` |
| `PORT` | ❌ No | `8000` |

### Frontend (Vercel)

| Variable | Required | Example |
|----------|----------|---------|
| `VITE_API_BASE_URL` | ✅ Yes | `https://contractforge-auditor-backend.onrender.com` |

---

## 🚀 Quick Reference Commands

### Local Testing Before Deployment

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
export GOOGLE_API_KEY=your_key_here
export FRONTEND_ORIGIN=http://localhost:5173
python -m uvicorn app.main:app --reload

# Frontend (in another terminal)
cd frontend
npm install
npm run dev
```

### Redeploy After Code Changes

```bash
# Push to GitHub
git add .
git commit -m "fix: update deployment config"
git push origin master

# Render will auto-deploy (if autoDeploy is enabled)
# Vercel will auto-deploy on push to master
```

---

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review logs in Render/Vercel dashboards
3. Verify environment variables are set correctly
4. Ensure GitHub repo is up to date
5. Try redeploying manually

---

## ✅ Deployment Checklist

- [ ] GitHub repo is public and up to date
- [ ] Google API key is generated and ready
- [ ] Render account created
- [ ] Vercel account created
- [ ] Backend deployed to Render
- [ ] Frontend deployed to Vercel
- [ ] Environment variables configured
- [ ] CORS is working
- [ ] Live tests passed
- [ ] Security checklist completed

---

**Deployment Complete!** 🎉

Your ContractForge Auditor is now live and ready for use.

Frontend: https://contractforge-auditor.vercel.app
Backend: https://contractforge-auditor-backend.onrender.com
