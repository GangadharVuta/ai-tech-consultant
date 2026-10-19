# Live Server Deployment Guide (100% Free & Beginner-Friendly)

This guide walks you through deploying the **AI Tech Consultant** to a live public server with a shareable HTTPS URL.

Both options below are **100% free** and require zero server administration experience.

---

## Comparison of Free Hosting Options

| Platform | Free Cost | Credit Card Required? | Build Time | Best For |
| :--- | :--- | :--- | :--- | :--- |
| **Hugging Face Spaces** *(Recommended)* | **100% Free** (16GB RAM, 2 vCPU) | ❌ **No Credit Card** | ~2 mins | Easiest, no billing verification |
| **Render.com** | **100% Free Tier** | ❌ **No Credit Card** | ~3 mins | Direct GitHub integration |
| **Koyeb / Railway** | Free credits / Hobby | Free tier available | ~2 mins | Fast edge containers |

---

## Option 1: Hugging Face Spaces (Recommended — No Credit Card Needed)

Hugging Face Spaces gives you a dedicated container with **2 vCPUs and 16 GB RAM for free**, with an automatic SSL certificate (`https://<username>-ai-tech-consultant.hf.space`).

### Step 1: Create a Free Account
1. Go to [huggingface.co/join](https://huggingface.co/join) and create a free account.

### Step 2: Create a New Space
1. Click your profile icon (top right) and click **"New Space"** (or visit [huggingface.co/new-space](https://huggingface.co/new-space)).
2. Configure:
   - **Space name**: `ai-tech-consultant`
   - **License**: `mit` or `apache-2.0`
   - **Space SDK**: Select **Docker** 🐳
   - **Choose a Docker template**: Select **Blank**
   - **Space hardware**: Select **CPU basic · 2 vCPU · 16 GB · Free**
   - **Visibility**: **Public**
3. Click **"Create Space"**.

### Step 3: Push Your Code to the Space
Hugging Face gives you a git URL for your Space: `https://huggingface.co/spaces/<YOUR_USERNAME>/ai-tech-consultant`.

In your local terminal (inside `ai-tech-consultant/`):
```bash
# Add Hugging Face Space as a git remote
git remote add space https://huggingface.co/spaces/<YOUR_USERNAME>/ai-tech-consultant

# Push code to your Space
git push space master
```
*(When prompted for password, use your Hugging Face Access Token from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) with "Write" permissions).*

### Step 4: Your Live URL Is Ready!
Hugging Face will automatically build the `Dockerfile`, start Nginx, and launch Task 1, Task 2, and Task 3.
In ~2 minutes, your live system will be running at:
```
https://<YOUR_USERNAME>-ai-tech-consultant.hf.space
```

---

## Option 2: Render.com (1-Click GitHub Deploy)

Render offers free web services that build directly from your GitHub repository.

### Step 1: Push Your Project to GitHub
1. Create a repository on GitHub (e.g. `ai-tech-consultant`).
2. Push your project:
   ```bash
   git remote add origin https://github.com/<YOUR_GITHUB_USER>/ai-tech-consultant.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy on Render
1. Go to [render.com](https://render.com) and sign in with GitHub.
2. Click **New +** (top right) -> Select **Web Service**.
3. Select your GitHub repository `ai-tech-consultant`.
4. Render will detect the `Dockerfile` automatically:
   - **Name**: `ai-tech-consultant`
   - **Region**: Choose closest to you (e.g. Oregon or Frankfurt)
   - **Branch**: `main` or `master`
   - **Runtime**: `Docker`
   - **Instance Type**: **Free** ($0/month)
5. *(Optional)* Under **Environment Variables**, add:
   - `ANTHROPIC_API_KEY`: *(Optional — your Anthropic API key if testing live Claude API)*
6. Click **"Deploy Web Service"**.

Render will build and deploy the container and generate your live HTTPS URL:
```
https://ai-tech-consultant.onrender.com
```

---

## Option 3: Run Live on Any Cloud VPS with Docker Compose

If you have a free VPS (e.g. Oracle Cloud Always-Free VM, AWS EC2 Free Tier, or DigitalOcean droplet):

```bash
# 1. Clone your repository
git clone https://github.com/<YOUR_USERNAME>/ai-tech-consultant.git
cd ai-tech-consultant

# 2. Start the container in the background
docker compose up -d --build
```
Your dashboard will be accessible immediately at `http://<YOUR_SERVER_IP>:8000`.

---

## Verifying Your Live Deployment

Once deployed to your live server:
1. Open the live URL in any browser or on your phone.
2. The health badges in the top navigation bar will turn **GREEN**:
   - `Task 1: ONLINE`
   - `Task 2: ONLINE`
   - `Task 3: ONLINE`
3. Try asking a question in **Task 1** (e.g. "How do I configure Stripe?").
4. Open **Task 2** and click "Generate Grounded Draft" for an email.
5. Open **Task 3** and run the analysis on `meeting_a.txt`.
