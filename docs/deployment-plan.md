# DineWise Deployment Plan

This document outlines the step-by-step procedure to deploy the DineWise AI Restaurant Recommender on **Streamlit Community Cloud**.

---

## 📋 Prerequisites

Before deploying, ensure you have:
1. A **GitHub account** with the project codebase pushed to a repository.
2. A **Streamlit Community Cloud account** (linked to your GitHub account).
3. A **Google Gemini API Key** (obtainable from [Google AI Studio](https://aistudio.google.com/apikey)).

---

## 🛠️ Step 1: Prepare and Push Code to GitHub

Streamlit Community Cloud deploys directly from a GitHub repository. 

> [!IMPORTANT]
> Ensure your `.gitignore` is correctly configured so that sensitive files and large caches are never committed to your public repository.

### 1.1 Verify `.gitignore`
Make sure the following lines are in your `.gitignore` file:
```text
.env
.venv/
__pycache__/
data/processed/
data/zomato.csv
```

### 1.2 Initialize and Push to GitHub
If you haven't already, run the following commands in your project root:
```bash
# Initialize git repository
git init

# Add all files (respecting .gitignore)
git add .

# Create initial commit
git commit -m "feat: DineWise AI recommender ready for deployment"

# Create a new repository on GitHub, then link and push
git remote add origin https://github.com/<your-username>/<your-repo-name>.git
git branch -M main
git push -u origin main
```

---

## 🚀 Step 2: Deploy on Streamlit Community Cloud

1. Navigate to the [Streamlit Share Console](https://share.streamlit.io/).
2. Log in using your **GitHub account**.
3. Click the **"New app"** button in the top-right corner.
4. Fill in the deployment details:
   * **Repository:** Select your `DineWise` repository.
   * **Branch:** `main`
   * **Main file path:** `src/app/ui.py`
   * **App URL:** Customize your subdomain (e.g., `dinewise-recommender.streamlit.app`).

---

## 🔑 Step 3: Configure Environment Secrets

Since DineWise requires a Google Gemini API Key to power the AI-driven recommendation summaries and rationales, you must configure this securely in the Streamlit Cloud dashboard.

1. In the **"Deploy an app"** screen, click on **"Advanced settings..."** before deploying (or click the **"Settings" -> "Secrets"** menu on an already deployed app).
2. Enter your Gemini API Key in the **Secrets** text box in TOML format:
   ```toml
   GEMINI_API_KEY = "AIzaSy..."
   ```
   *(Note: The application is designed to automatically pick up `GEMINI_API_KEY`, `LLM_API_KEY`, or `GOOGLE_API_KEY` from either environment variables or Streamlit secrets).*
3. Click **"Save"**.
4. Click **"Deploy!"** to build the application.

---

## 📥 Step 4: Bootstrap the Zomato Dataset

Since the preprocessed `restaurants.parquet` is gitignored to keep the repository lightweight, the database must be bootstrapped upon the first deployment.

> [!TIP]
> DineWise has a built-in auto-bootstrapper. On the first launch, the app will detect that the data cache is missing and display a friendly setup screen.

1. Access your newly deployed Streamlit app URL.
2. You will see a warning: **"⚠️ Zomato dataset has not been preprocessed yet. Let's bootstrap it first!"**
3. Click the **"📥 Load & Bootstrap Zomato Dataset (Hugging Face)"** button.
4. Streamlit will download the dataset directly from Hugging Face, clean the columns, compute budget bands, deduplicate entries, and build the optimized Parquet cache in the background (takes approx. 30-45 seconds).
5. Once completed, the app will automatically refresh and be fully operational!

---

## 🧪 Step 5: Post-Deployment Verification

After the app is built and bootstrapped, verify that it is fully functional:
1. **Search localizations:** Verify the `Location` dropdown is populated with neighborhood localities (e.g., *Indiranagar*, *Bellandur*, *Whitefield*).
2. **Filters & LLM query:** Submit a search (e.g., Location: *Bellandur*, Budget: *Medium*, Cuisine: *Italian*, Rating: *4.0*, Preferences: *family-friendly*).
3. **AI Output:** Ensure the top recommendations load cleanly, showing:
   * A premium, structured card with an emoji icon matching the cuisine.
   * A personalized rating and cost display (*"₹X for two"*).
   * A 1-2 sentence AI-tailored explanation matching your extra preferences.
   * An elegant AI summary box highlighting the overall recommendations.
