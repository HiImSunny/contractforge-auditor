# 🚀 ContractForge Auditor — Deployment Checklist

Quick checklist to deploy to Render + Vercel in ~15 minutes.

---

## ✅ Pre-Deployment (5 minutes)

- [ ] Have Google API key ready (from https://aistudio.google.com/apikey)
- [ ] GitHub repo is public: https://github.com/HiImSunny/contractforge-auditor
- [ ] Create Render account: https://render.com
- [ ] Create Vercel account: https://vercel.com

---

## 🔧 Deploy Backend to Render (5 minutes)

1. **Go to Render Dashboard**
   - https://render.com/dashboard

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Select "Deploy an existing repository"
   - Connect GitHub and select `contractforge-auditor`

3. **Configure Service**
   ```
   Name: contractforge-auditor-backend
   Environment: Docker
   Region: Singapore (or closest)
   Branch: master
   Dockerfile Path: ./Dockerfile
   Docker Context: .
   Plan: Free
   ```

4. **Add Environment Variables**
   ```
   GOOGLE_API_KEY = <your_api_key>
   FRONTEND_ORIGIN = https://contractforge-auditor.vercel.app
   GEMINI_MODEL = gemini-1.5-flash
   PORT = 8000
   ```

5. **Deploy**
   - Click "Create Web Service"
   - Wait 5-10 minutes for build
   - **Save backend URL**: `https://contractforge-auditor-backend.onrender.com`

6. **Verify**
   ```bash
   curl https://contractforge-auditor-backend.onrender.com/api/health
   ```

---

## 🎨 Deploy Frontend to Vercel (5 minutes)

1. **Go to Vercel Dashboard**
   - https://vercel.com/dashboard

2. **Import Project**
   - Click "Add New..." → "Project"
   - Select "Import Git Repository"
   - Connect GitHub and select `contractforge-auditor`

3. **Configure Project**
   ```
   Project Name: contractforge-auditor
   Framework: Vite
   Root Directory: ./frontend
   Build Command: npm run build
   Output Directory: dist
   ```

4. **Add Environment Variables**
   ```
   VITE_API_BASE_URL = https://contractforge-auditor-backend.onrender.com
   ```

5. **Deploy**
   - Click "Deploy"
   - Wait 2-3 minutes
   - **Save frontend URL**: `https://contractforge-auditor.vercel.app`

6. **Verify**
   - Open https://contractforge-auditor.vercel.app
   - Should see dashboard

---

## 🔄 Update Backend with Frontend URL (1 minute)

1. **Go to Render Backend Service**
   - https://render.com/dashboard

2. **Update Environment Variable**
   - Click "Environment"
   - Update `FRONTEND_ORIGIN` to your Vercel URL
   - Click "Save"
   - Render auto-redeploys

---

## 🧪 Test Live Deployment (2 minutes)

1. **Open Frontend**
   - https://contractforge-auditor.vercel.app

2. **Upload Sample Contract**
   - Click "Upload Contract"
   - Upload from `backend/samples/contracts/`
   - Verify it processes

3. **Test Risk Simulation**
   - Click "Simulate Risk"
   - Select a scenario
   - Verify risk score updates

4. **Generate Report**
   - Click "Generate Report"
   - Verify PDF downloads

---

## 🎉 Done!

Your ContractForge Auditor is now live:

- **Frontend**: https://contractforge-auditor.vercel.app
- **Backend**: https://contractforge-auditor-backend.onrender.com

---

## 📞 Troubleshooting

| Issue | Solution |
|-------|----------|
| API connection failed | Check `VITE_API_BASE_URL` in Vercel env vars |
| Backend won't deploy | Check Render logs for build errors |
| GOOGLE_API_KEY error | Verify key is set in Render environment |
| Service goes to sleep | Free tier spins down after 15 min inactivity |

See `DEPLOYMENT_GUIDE.md` for detailed troubleshooting.

---

## 📊 Monitoring

- **Backend Logs**: Render Dashboard → Service → Logs
- **Frontend Logs**: Vercel Dashboard → Project → Deployments → Logs
- **Health Check**: `curl https://contractforge-auditor-backend.onrender.com/api/health`

---

**Total Time: ~15 minutes** ⏱️
