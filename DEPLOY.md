# Deploying Bug Report AI

This guide explains how to run the project in Docker and how to put it online. Nothing here has been run on a real hosting account yet, so treat it as a checklist to work through and correct as you go. Prices, plan sizes and menu names change, so check each provider's own pages.

## How the pieces fit together

```
Browser ──► Frontend (static site)  ──►  Backend (Docker container)  ──►  MongoDB Atlas
                                              │
                                              └──►  Model files (downloaded from a private Hugging Face repo)
```

- **Frontend**: the React site, built into static files. It can be hosted on Vercel (simplest) or served by the `frontend/Dockerfile` image (nginx).
- **Backend**: `backend/Dockerfile`. The image contains only code. It needs about 2 GB of RAM because it loads the models.
- **Database**: MongoDB Atlas (already used).
- **Model files**: about 1 GB in `ml/artifacts`, of which the backend only needs about 250 MB. They are not in Git. They are stored in a **private Hugging Face repo** and downloaded when the backend starts.

## 1. Put the model files in a private Hugging Face repo

Do this once, on your own computer, from the project folder (virtual environment active).

1. Create a free account at huggingface.co, then create an access token with **write** permission (Settings, Access Tokens). Keep it secret.
2. Collect only the files the backend needs:

   ```
   python scripts/prepare_model_bundle.py
   ```

   It creates a `model_bundle` folder (about 250 MB) and prints the sizes. It leaves out the ONNX and OpenVINO copies and the other framework copies of the MiniLM model. `model_bundle` is not committed to Git. If `ml/artifacts/severity_transformer` exists (version 2), the bundle also contains that model (about 250 MB more).
3. Upload it to a **private** repo (use your own username):

   ```
   set HF_TOKEN=hf_your_token_here
   python scripts/upload_model_bundle.py YOUR-USERNAME/bug-report-ai-models
   ```

4. For the backend you also need a **read** token. Create a second token with read permission only, and use that one on the server (not the write token).

## 2. Try it with Docker on your computer (optional)

You need Docker Desktop. It uses a lot of memory on Windows (a few GB), so skip this step on an 8 GB laptop and rely on the GitHub Actions checks instead (see below).

```
docker compose up --build
```

Open `http://localhost:8080`. The backend reads `backend\.env` and mounts `ml\artifacts` from your computer.

## 3. Automatic checks (GitHub Actions)

`.github/workflows/ci.yml` runs on every push to `main` and on pull requests:

- backend tests and a vulnerability check of the backend packages,
- frontend tests, build and a vulnerability check of the production packages,
- builds both Docker images and checks that the frontend container sends its security headers, and that the backend image stops with a clear message when the model files are missing.

Open the **Actions** tab of the repository to see the result. The ML tests are allowed to fail there because they need data files that are not in Git.

## 4. Deploy the backend (Docker host such as Render or Railway)

The steps are the same on any host that can build a Dockerfile from GitHub:

1. Create a new **web service** from your GitHub repository, with runtime **Docker**.
2. Dockerfile path: `backend/Dockerfile`. Build context: the **repository root** (`.`).
3. Instance size: at least **2 GB of RAM**. Check the provider's current plans; the smallest free plans are usually too small for the models.
4. Health check path: `/api/v1/health`.
5. Environment variables (set them in the host's dashboard, not in Git):

   | Variable | Value |
   | --- | --- |
   | `MONGODB_URI` | your Atlas connection string |
   | `MONGODB_DB` | `bug_report_ai` |
   | `AUTH_ENABLED` | `true` |
   | `JWT_SECRET` | a new random secret, at least 32 characters (do not reuse the development one) |
   | `CORS_ORIGINS` | the exact address of your frontend, for example `https://your-site.vercel.app` (no trailing slash) |
   | `ENABLE_DOCS` | `false` |
   | `ENABLE_HSTS` | `true` |
   | `LOAD_MODELS` | `true` |
   | `SEVERITY_MODEL` | `tfidf` (version 1) or `transformer` (version 2). The transformer needs about 600 MB more memory, so choose an instance with more RAM |
   | `MODELS_REPO` | `YOUR-USERNAME/bug-report-ai-models` |
   | `HF_TOKEN` | the **read** token |

   The host provides `PORT` itself; the container uses it.
6. The first start downloads the models, so it takes a few minutes. Watch the logs for "Models tayyar hain" and then "Authentication is ON".

### MongoDB Atlas and the host's IP address

Atlas only accepts connections from addresses on its **Network Access** list, and cloud hosts usually do not have a fixed address.

- Best: use the host's fixed outbound addresses if your plan offers them (check the provider's documentation) and add only those.
- Otherwise you must allow `0.0.0.0/0` (anywhere). This is a real risk, so reduce it: use a long random database password, create a database user that can only read and write the `bug_report_ai` database (not an admin user), and never reuse that password elsewhere.

### First-time data and the first admin

You can run the helper scripts from your own computer against the same Atlas database (put the production `MONGODB_URI` in your local `backend\.env` for a moment):

```
cd backend
python init_db.py --import-sample 2000
python register_models.py
python create_admin.py
cd ..
```

Use a strong password for the admin. Afterwards, put your development `MONGODB_URI` back.

## 5. Deploy the frontend

### Option A: Vercel

1. Import the repository. Set **Root Directory** to `frontend`. Framework preset: Vite. Build command `npm run build`, output directory `dist`.
2. Environment variables:
   - `VITE_API_URL` = `https://YOUR-BACKEND-ADDRESS/api/v1`
   - `VITE_SHOW_API_DOCS` = `false`
3. Add a file `frontend/vercel.json` with a rewrite (so page refreshes work) and security headers. Replace `YOUR-BACKEND-ADDRESS` with your backend's address (scheme and host only, no path):

   ```json
   {
     "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }],
     "headers": [
       {
         "source": "/(.*)",
         "headers": [
           { "key": "X-Content-Type-Options", "value": "nosniff" },
           { "key": "X-Frame-Options", "value": "DENY" },
           { "key": "Referrer-Policy", "value": "no-referrer" },
           { "key": "Permissions-Policy", "value": "camera=(), microphone=(), geolocation=()" },
           {
             "key": "Content-Security-Policy",
             "value": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; connect-src 'self' https://YOUR-BACKEND-ADDRESS; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
           }
         ]
       }
     ]
   }
   ```

4. After the first deploy, copy the site's address into the backend's `CORS_ORIGINS` and redeploy the backend.

### Option B: the nginx image

`frontend/Dockerfile` builds the site and serves it with nginx (security headers included). Pass the backend address when building:

```
docker build -t bug-report-frontend ^
  --build-arg VITE_API_URL=https://YOUR-BACKEND-ADDRESS/api/v1 ^
  --build-arg API_ORIGIN=https://YOUR-BACKEND-ADDRESS ^
  frontend
```

The container listens on port 8080. Terminate HTTPS at the host.

## 6. Check it after deploying

From any computer (replace the addresses):

1. Open the site. You should see the login page. Sign in with the admin you created.
2. As a reviewer, check that Upload, Bulk predict, Settings and Users are not available.
3. Security headers on the backend:

   ```
   curl -I https://YOUR-BACKEND-ADDRESS/api/v1/health
   ```

   You should see `x-content-type-options`, `x-frame-options`, `content-security-policy`, `strict-transport-security` and `cache-control: no-store`.
4. `https://YOUR-BACKEND-ADDRESS/docs` and `/openapi.json` must answer **404**.
5. `https://YOUR-BACKEND-ADDRESS/.env` and `/.git/config` must answer **404**.
6. Try 5 wrong passwords for a test user. The account should lock (message "Too many failed sign-in attempts").
7. Without a token, `https://YOUR-BACKEND-ADDRESS/api/v1/reports` must answer **401**.

## 7. Keeping it safe

- Never commit `backend\.env`, tokens or passwords. If a secret was ever shown or committed, replace it (new Atlas password, new `JWT_SECRET`, new Hugging Face token).
- Changing `JWT_SECRET` signs everyone out.
- Rate limiting by IP address is not built into the application. Use the host's or a proxy's features for that if you expect public traffic.
- Re-run the checks in the Actions tab after you change dependencies. Dependabot (in the repository's Security settings) can propose updates.
- The severity model is weak (macro F1 about 0.42). Keep the human review step.
