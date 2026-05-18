# 📌 ContractForge Auditor — Deployment Quick Reference

**One-page reference for deploying to Render + Vercel**

---

## 🔗 Important URLs

| Service | URL |
|---------|-----|
| **GitHub Repo** | https://github.com/HiImSunny/contractforge-auditor |
| **Render Dashboard** | https://render.com/dashboard |
| **Vercel Dashboard** | https://vercel.com/dashboard |
| **Google API Keys** | https://aistudio.google.com/apikey |
| **Frontend (Live)** | https://contractforge-auditor.vercel.app |
| **Backend (Live)** | https://contractforge-auditor-backend.onrender.com |

---

## 🚀 Deployment Steps (15 minutes)

### 1️⃣ Backend to Render (5 min)

```
Render Dashboard → New Web Service
├─ Repository: contractforge-auditor
├─ Name: contractforge-auditor-backend
├─ Environment: Docker
├─ Dockerfile: ./Dockerfile
├─ Plan: Free
└─ Environment Variables:
   ├─ GOOGLE_API_KEY = <your_key>
   ├─ FRONTEND_ORIGIN = https://contractforge-auditor.vercel.app
   ├─ GEMINI_MODEL = gemini-1.5-flash
   └─ PORT = 8000
```

**Verify:** `curl https://contractforge-auditor-backend.onrender.com/api/health`

### 2️⃣ Frontend to Vercel (5 min)

```
Vercel Dashboard → Add Project → Import Git Repository
├─ Repository: contractforge-auditor
├─ Project Name: contractforge-auditor
├─ Framework: Vite
├─ Root Directory: ./frontend
├─ Build Command: npm run build
├─ Output Directory: dist
└─ Environment Variables:
   └─ VITE_API_BASE_URL = https://contractforge-auditor-backend.onrender.com
```

**Verify:** Open https://contractforge-auditor.vercel.app

### 3️⃣ Update Backend CORS (1 min)

```
Render Dashboard → Service → Environment
└─ FRONTEND_ORIGIN = https://contractforge-auditor.vercel.app
   (Auto-redeploys)
```

---

## 🔑 Environment Variables

### Backend (Render)

```env
GOOGLE_API_KEY=AIzaSyD...                                    # Required
FRONTEND_ORIGIN=https://contractforge-auditor.vercel.app    # Required
GEMINI_MODEL=gemini-1.5-flash                               # Optional
PORT=8000                                                    # Optional
```

### Frontend (Vercel)

```env
VITE_API_BASE_URL=https://contractforge-auditor-backend.onrender.com  # Required
```

---

## ✅ Verification Checklist

```bash
# 1. Backend health check
curl https://contractforge-auditor-backend.onrender.com/api/health
# Expected: {"status": "ok"}

# 2. CORS headers
curl -H "Origin: https://contractforge-auditor.vercel.app" \
     https://contractforge-auditor-backend.onrender.com/api/health
# Expected: Access-Control-Allow-Origin header present

# 3. Frontend loads
open https://contractforge-auditor.vercel.app
# Expected: Dashboard visible

# 4. Upload works
# Click "Upload Contract" → Select sample file → Verify processing
```

---

## 🆘 Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| **API connection failed** | Check `VITE_API_BASE_URL` in Vercel env vars |
| **Backend won't deploy** | Check Render logs for build errors |
| **GOOGLE_API_KEY error** | Verify key in Render environment variables |
| **CORS blocked** | Update `FRONTEND_ORIGIN` in Render |
| **Blank page** | Check Vercel build logs |
| **Slow first request** | Free tier spins down after 15 min (normal) |

See `TROUBLESHOOTING.md` for detailed solutions.

---

## 📊 Monitoring

```bash
# Backend logs
Render Dashboard → Service → Logs

# Frontend logs
Vercel Dashboard → Deployments → Latest → Logs

# Health check
curl https://contractforge-auditor-backend.onrender.com/api/health
```

---

## 🔄 Redeploy After Code Changes

```bash
# Push to GitHub
git add .
git commit -m "fix: update deployment config"
git push origin master

# Auto-deploys to:
# - Render (if autoDeploy enabled)
# - Vercel (always auto-deploys on push)
```

---

## 💰 Pricing

| Service | Free Tier | Paid Tier |
|---------|-----------|-----------|
| **Render** | 512MB RAM, spins down after 15 min | $7/month (always on) |
| **Vercel** | Unlimited deployments | $20/month (advanced features) |
| **Google Gemini** | 60 req/min, 1500 req/day | Pay-as-you-go |

---

## 📝 File Locations

```
contractforge-auditor/
├── DEPLOYMENT_GUIDE.md              ← Full deployment guide
├── DEPLOYMENT_QUICK_REFERENCE.md    ← This file
├── TROUBLESHOOTING.md               ← Troubleshooting guide
├── scripts/deploy-checklist.md      ← Step-by-step checklist
├── frontend/
│   ├── vercel.json                  ← Vercel config
│   ├── .env.example                 ← Frontend env template
│   └── package.json
└── backend/
    ├── render.yaml                  ← Render config
    ├── Dockerfile                   ← Docker config
    ├── .env.example                 ← Backend env template
    └── requirements.txt
```

---

## 🎯 Next Steps

1. **Get Google API Key**
   - Go to https://aistudio.google.com/apikey
   - Click "Create API key"
   - Copy the key

2. **Deploy Backend**
   - Follow "Backend to Render" steps above
   - Save the backend URL

3. **Deploy Frontend**
   - Follow "Frontend to Vercel" steps above
   - Save the frontend URL

4. **Update Backend CORS**
   - Follow "Update Backend CORS" steps above

5. **Test Live**
   - Open frontend URL
   - Upload a contract
   - Run risk simulation
   - Generate report

6. **Share with Team**
   - Frontend: https://contractforge-auditor.vercel.app
   - Backend: https://contractforge-auditor-backend.onrender.com

---

## 📞 Support Resources

- **Render Docs**: https://render.com/docs
- **Vercel Docs**: https://vercel.com/docs
- **Google Gemini Docs**: https://ai.google.dev/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **React Docs**: https://react.dev

---

**Deployment Time: ~15 minutes** ⏱️

**Questions?** See `DEPLOYMENT_GUIDE.md` or `TROUBLESHOOTING.md`
