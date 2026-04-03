# GitHub Repository & CI/CD Setup Guide

This guide explains how to set up a private GitHub repository with automatic deployment to AWS Lightsail.

---

## 🔐 Security First: .env Files

### ⚠️ NEVER push .env to GitHub!

Your `.env` file contains sensitive API keys:
```
DEEPGRAM_API_KEY=xxx
OPENAI_API_KEY=xxx
GOOGLE_API_KEY=xxx
...
```

**Why it's dangerous:**
- Even in private repos, if someone gains access, all your API keys are exposed
- Git history keeps files forever - even if you delete later
- API keys can be used to rack up huge bills on your accounts

**What we do instead:**
1. `.gitignore` excludes `.env` (already configured ✅)
2. Push `env.example` as a template (no real keys)
3. Create `.env` manually on the server
4. Use GitHub Secrets for CI/CD

---

## 📦 Step 1: Create Private GitHub Repository

### Option A: Using GitHub CLI
```bash
# Install GitHub CLI if needed
brew install gh

# Login to GitHub
gh auth login

# Create private repo and push
cd /Users/apple/Desktop/nester\ ai\ bot\ opensource/NesterConversationalBot
gh repo create nester-conversational-bot --private --source=. --push
```

### Option B: Using GitHub Website
1. Go to https://github.com/new
2. Repository name: `nester-conversational-bot`
3. Select: **Private**
4. Click "Create repository"
5. Follow the commands shown to push existing code

---

## 📤 Step 2: Push Your Code

```bash
# Navigate to project
cd /Users/apple/Desktop/nester\ ai\ bot\ opensource/NesterConversationalBot

# Initialize git (if not already)
git init

# Add all files (respects .gitignore)
git add .

# Commit
git commit -m "Initial commit: NesterConversationalBot"

# Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/nester-conversational-bot.git

# Push to main
git push -u origin main
```

---

## 🔗 Step 3: Connect Lightsail to GitHub

### 3.1 SSH into Lightsail
```bash
ssh -i your-key.pem ec2-user@3.6.64.48
```

### 3.2 Install Git (if not installed)
```bash
sudo yum install -y git
```

### 3.3 Generate SSH Key on Lightsail
```bash
ssh-keygen -t ed25519 -C "lightsail-deploy"
cat ~/.ssh/id_ed25519.pub
```

### 3.4 Add SSH Key to GitHub
1. Go to: https://github.com/settings/keys
2. Click "New SSH key"
3. Title: "Lightsail Server"
4. Paste the public key
5. Click "Add SSH key"

### 3.5 Clone Repository on Lightsail
```bash
cd ~
# Remove old directory if exists
rm -rf nester-bot

# Clone via SSH
git clone git@github.com:YOUR_USERNAME/nester-conversational-bot.git nester-bot
cd nester-bot
```

### 3.6 Create .env on Server (MANUALLY - SECURE!)
```bash
nano .env
# Paste your API keys here
# Save with Ctrl+X, Y, Enter
```

---

## 🚀 Step 4: Set Up Automatic Deployment (CI/CD)

### 4.1 Add GitHub Secrets
Go to: `https://github.com/YOUR_USERNAME/nester-conversational-bot/settings/secrets/actions`

Add these secrets:

| Secret Name | Value |
|-------------|-------|
| `LIGHTSAIL_HOST` | `3.6.64.48` |
| `LIGHTSAIL_USER` | `ec2-user` |
| `LIGHTSAIL_SSH_KEY` | Contents of your `.pem` file |

**To get SSH key contents:**
```bash
cat /path/to/your-lightsail-key.pem
```
Copy the entire content including `-----BEGIN RSA PRIVATE KEY-----` and `-----END RSA PRIVATE KEY-----`

### 4.2 GitHub Actions Workflow
The workflow file is already created at `.github/workflows/deploy.yml`

It will:
1. Trigger on every push to `main` branch
2. SSH into your Lightsail server
3. Pull latest code
4. Rebuild and restart Docker containers

---

## 🔄 Step 5: Deploy Changes

After setup, deployment is automatic:

```bash
# Make changes locally
git add .
git commit -m "Your change description"
git push origin main

# GitHub Actions will automatically deploy to Lightsail!
```

### Manual Deployment (if needed)
```bash
# SSH to server
ssh -i your-key.pem ec2-user@3.6.64.48

# Pull and rebuild
cd ~/nester-bot
git pull origin main
docker-compose down
docker-compose up -d --build
```

---

## 📋 Summary: What Goes Where

| File | In GitHub? | Why? |
|------|------------|------|
| `.env` | ❌ NO | Contains API keys - NEVER commit |
| `env.example` | ✅ YES | Template without real keys |
| `docker-compose.yml` | ✅ YES | Infrastructure as code |
| `src/` | ✅ YES | Application code |
| `Dockerfile` | ✅ YES | Build instructions |
| `.pem` files | ❌ NO | SSH private keys |

---

## 🛡️ Security Best Practices

1. **Repository**: Always use **Private** repository
2. **API Keys**: Never in code or Git - use `.env` + GitHub Secrets
3. **SSH Keys**: Keep `.pem` files secure, never commit
4. **Rotate Keys**: If you accidentally push keys, rotate them immediately
5. **Branch Protection**: Enable for `main` branch in production

---

## 🔍 Verify .env is NOT in Git

Before pushing, verify `.env` is ignored:
```bash
git status
# .env should NOT appear in the list

# Double-check .gitignore
cat .gitignore | grep -i env
# Should show: .env
```

---

## 🆘 Troubleshooting

### "Permission denied" when cloning on Lightsail
- Ensure SSH key is added to GitHub
- Test: `ssh -T git@github.com`

### GitHub Actions failing
- Check secrets are set correctly
- View logs in Actions tab

### Changes not reflecting
- Check Docker rebuilt: `docker-compose logs -f`
- Verify git pull worked: `git log --oneline -3`

