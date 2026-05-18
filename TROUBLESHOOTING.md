# 🔧 ContractForge Auditor — Troubleshooting Guide

Common issues and solutions for deployment and runtime.

---

## 🌐 Frontend Issues

### Issue: "Cannot connect to API" or "API Error"

**Symptoms:**
- Dashboard shows error message
- Network tab shows failed requests to backend
- Console shows CORS errors

**Solutions:**

1. **Check API URL is correct**
   ```bash
   # In Vercel dashboard:
   # Settings → Environment Variables
   # Verify VITE_API_BASE_URL = https://contractforge-auditor-backend.onrender.com
   ```

2. **Verify backend is running**
   ```bash
   curl https://contractforge-auditor-backend.onrender.com/api/health
   ```
   Should return: `{"status": "ok"}`

3. **Check CORS headers**
   ```bash
   curl -H "Origin: https://contractforge-auditor.vercel.app" \
        -H "Access-Control-Request-Method: POST" \
        https://contractforge-auditor-backend.onrender.com/api/health
   ```
   Should include `Access-Control-Allow-Origin` header

4. **Redeploy frontend**
   - Vercel Dashboard → Deployments → Latest → "Redeploy"
   - Wait 2-3 minutes

---

### Issue: "Page not found" or blank page

**Symptoms:**
- Vercel shows 404 error
- Page is completely blank
- No content loads

**Solutions:**

1. **Check build succeeded**
   - Vercel Dashboard → Deployments → Latest
   - Look for "✓ Build successful"

2. **Check build logs**
   - Click on deployment
   - Click "Logs"
   - Look for build errors

3. **Verify root directory**
   - Vercel Dashboard → Settings → General
   - Root Directory should be `./frontend`

4. **Clear browser cache**
   ```bash
   # Hard refresh in browser
   Ctrl+Shift+R (Windows/Linux)
   Cmd+Shift+R (Mac)
   ```

---

### Issue: Styles not loading (unstyled page)

**Symptoms:**
- Page loads but has no styling
- TailwindCSS not applied
- Components look broken

**Solutions:**

1. **Check build command**
   - Vercel Dashboard → Settings → Build & Development Settings
   - Build Command should be: `npm run build`

2. **Verify Tailwind config**
   ```bash
   # In frontend/tailwind.config.ts
   # Should include content paths:
   content: [
     "./index.html",
     "./src/**/*.{js,ts,jsx,tsx}",
   ]
   ```

3. **Redeploy**
   - Vercel Dashboard → Deployments → Latest → "Redeploy"

---

## 🔙 Backend Issues

### Issue: "Build failed" on Render

**Symptoms:**
- Render shows red "Build failed" status
- Service won't start
- Logs show build errors

**Solutions:**

1. **Check build logs**
   - Render Dashboard → Service → Logs
   - Look for error messages

2. **Verify Dockerfile**
   ```bash
   # Check Dockerfile exists in backend root
   ls -la backend/Dockerfile
   
   # Verify it's valid
   docker build -f backend/Dockerfile -t test .
   ```

3. **Check requirements.txt**
   ```bash
   # Verify all dependencies are listed
   cat backend/requirements.txt
   
   # Try installing locally
   pip install -r backend/requirements.txt
   ```

4. **Common Docker errors:**
   - `COPY failed: file not found` → Check file paths in Dockerfile
   - `ModuleNotFoundError` → Add missing package to requirements.txt
   - `Port already in use` → Change PORT env var

5. **Redeploy**
   - Render Dashboard → Service → Manual Deploy

---

### Issue: "GOOGLE_API_KEY not found" error

**Symptoms:**
- Backend logs show: `KeyError: 'GOOGLE_API_KEY'`
- API returns 500 error
- Service crashes on startup

**Solutions:**

1. **Verify API key is set**
   - Render Dashboard → Service → Environment
   - Check `GOOGLE_API_KEY` is listed

2. **Get new API key**
   - Go to https://aistudio.google.com/apikey
   - Click "Create API key"
   - Copy the key

3. **Update environment variable**
   - Render Dashboard → Service → Environment
   - Click `GOOGLE_API_KEY`
   - Paste new key
   - Click "Save"
   - Render auto-redeploys

4. **Verify key works**
   ```bash
   curl -X POST https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=YOUR_KEY \
     -H "Content-Type: application/json" \
     -d '{"contents":[{"parts":[{"text":"test"}]}]}'
   ```

---

### Issue: Service goes to sleep (free tier)

**Symptoms:**
- First request takes 30+ seconds
- Service spins down after 15 minutes of inactivity
- Subsequent requests are fast

**Solutions:**

1. **Upgrade to paid plan**
   - Render Dashboard → Service → Settings
   - Change Plan to "Starter" ($7/month)
   - Services stay running 24/7

2. **Use monitoring service** (free alternative)
   - Set up a cron job to ping health endpoint every 10 minutes
   - Example: https://uptimerobot.com (free tier)

3. **Accept the limitation**
   - Free tier is fine for demos
   - Users will wait for first request

---

### Issue: "FRONTEND_ORIGIN not set" or CORS errors

**Symptoms:**
- Frontend requests blocked by CORS
- Backend logs show CORS errors
- Browser console shows: `Access to XMLHttpRequest blocked by CORS policy`

**Solutions:**

1. **Verify FRONTEND_ORIGIN is set**
   - Render Dashboard → Service → Environment
   - Check `FRONTEND_ORIGIN` is listed

2. **Update FRONTEND_ORIGIN**
   - Should be your Vercel URL: `https://contractforge-auditor.vercel.app`
   - No trailing slash
   - Must be HTTPS

3. **Redeploy backend**
   - Render Dashboard → Service → Manual Deploy

4. **Test CORS**
   ```bash
   curl -H "Origin: https://contractforge-auditor.vercel.app" \
        -H "Access-Control-Request-Method: POST" \
        https://contractforge-auditor-backend.onrender.com/api/health
   ```
   Should include: `Access-Control-Allow-Origin: https://contractforge-auditor.vercel.app`

---

## 📤 File Upload Issues

### Issue: "File upload failed" or "Invalid file format"

**Symptoms:**
- Upload button doesn't work
- Error message appears after selecting file
- File is rejected

**Solutions:**

1. **Check file format**
   - Supported: PDF, TXT, DOCX
   - Verify file extension is correct
   - Try a different file

2. **Check file size**
   - Max size: 10MB (configurable)
   - Compress PDF if too large

3. **Check backend is running**
   ```bash
   curl https://contractforge-auditor-backend.onrender.com/api/health
   ```

4. **Check upload endpoint**
   ```bash
   curl -X POST https://contractforge-auditor-backend.onrender.com/api/upload \
     -F "file=@sample.pdf"
   ```

---

### Issue: "PDF parsing failed" or "No text extracted"

**Symptoms:**
- File uploads but shows empty content
- Risk analysis shows no results
- Backend logs show parsing errors

**Solutions:**

1. **Verify PDF is text-based**
   - Scanned PDFs (images) won't work
   - Use OCR to convert scanned PDFs first

2. **Check file is not corrupted**
   - Try opening PDF in Adobe Reader
   - Try uploading a different PDF

3. **Check Gemini API quota**
   - Go to https://aistudio.google.com/apikey
   - Check usage and quota
   - May need to upgrade to paid plan

---

## 🤖 AI/Gemini Issues

### Issue: "Gemini API error" or "Rate limit exceeded"

**Symptoms:**
- Backend logs show Gemini errors
- API returns 429 (Too Many Requests)
- Analysis takes very long

**Solutions:**

1. **Check API quota**
   - Go to https://aistudio.google.com/apikey
   - Check daily quota usage
   - Free tier: 60 requests/minute

2. **Upgrade to paid plan**
   - Go to https://console.cloud.google.com
   - Enable billing
   - Increase quota limits

3. **Reduce request frequency**
   - Don't spam analysis requests
   - Wait between requests

4. **Use different model**
   - Try `gemini-1.5-pro` (slower but more capable)
   - Update `GEMINI_MODEL` env var in Render

---

### Issue: "Invalid API key" or "Unauthorized"

**Symptoms:**
- Backend logs show: `Invalid API key`
- Gemini API returns 401 error
- Analysis fails

**Solutions:**

1. **Verify API key format**
   - Should start with `AIza...`
   - Should be 39+ characters
   - No spaces or special characters

2. **Check API key is enabled**
   - Go to https://aistudio.google.com/apikey
   - Verify key is listed and active
   - Try creating a new key

3. **Update in Render**
   - Render Dashboard → Service → Environment
   - Update `GOOGLE_API_KEY`
   - Save and redeploy

---

## 📊 Performance Issues

### Issue: "Analysis is very slow" or "Timeout"

**Symptoms:**
- Analysis takes 30+ seconds
- Request times out
- Backend logs show slow processing

**Solutions:**

1. **Check backend is running**
   - Render free tier may be slow
   - First request after sleep takes 30+ seconds

2. **Upgrade backend plan**
   - Render Dashboard → Service → Settings
   - Change to "Starter" plan ($7/month)
   - Faster CPU and memory

3. **Optimize file size**
   - Smaller files process faster
   - Compress PDFs before upload

4. **Check Gemini model**
   - `gemini-1.5-flash` is faster
   - `gemini-1.5-pro` is slower but more accurate

---

### Issue: "Out of memory" or "Service crashed"

**Symptoms:**
- Backend logs show memory errors
- Service restarts unexpectedly
- Large files fail to process

**Solutions:**

1. **Upgrade backend plan**
   - Free tier: 512MB RAM
   - Starter tier: 1GB RAM
   - Render Dashboard → Service → Settings

2. **Reduce file size**
   - Split large contracts into smaller files
   - Compress PDFs

3. **Optimize code**
   - Check for memory leaks
   - Profile backend performance

---

## 🔐 Security Issues

### Issue: "Sensitive data exposed" or "Security warning"

**Symptoms:**
- API key visible in frontend code
- Secrets in GitHub commits
- CORS allows all origins

**Solutions:**

1. **Never commit secrets**
   ```bash
   # Check for exposed keys
   git log -p | grep -i "api_key\|secret\|password"
   
   # If found, use git-filter-branch to remove
   ```

2. **Use environment variables**
   - All secrets in Render/Vercel env vars
   - Never hardcode in code

3. **Verify CORS is restricted**
   - Backend should only allow frontend origin
   - Check `FRONTEND_ORIGIN` is set correctly

4. **Enable HTTPS**
   - Both Render and Vercel use HTTPS by default
   - Verify URLs start with `https://`

---

## 🆘 Getting Help

If you can't find a solution:

1. **Check logs**
   - Render: Dashboard → Service → Logs
   - Vercel: Dashboard → Deployments → Logs

2. **Search error message**
   - Google the exact error message
   - Check Stack Overflow

3. **Check documentation**
   - Render docs: https://render.com/docs
   - Vercel docs: https://vercel.com/docs
   - Gemini docs: https://ai.google.dev/docs

4. **Contact support**
   - Render support: https://render.com/support
   - Vercel support: https://vercel.com/support
   - Google AI support: https://ai.google.dev/support

---

## 📋 Debug Checklist

When troubleshooting, verify:

- [ ] Backend is running: `curl https://contractforge-auditor-backend.onrender.com/api/health`
- [ ] Frontend can reach backend: Check browser Network tab
- [ ] API key is valid: Test with curl
- [ ] Environment variables are set: Check Render/Vercel dashboards
- [ ] CORS is configured: Check response headers
- [ ] Files are correct format: Verify PDF/TXT/DOCX
- [ ] No secrets in code: Check git history
- [ ] Latest code is deployed: Check git commits

---

**Still stuck?** Check the full deployment guide: `DEPLOYMENT_GUIDE.md`
