copy‑pasteable markdown section that explains how to run this project locally and how the data/images work with the Lovable backend.


# Running This Project Locally (With Lovable Backend)

This project is built with **Vite + React + TypeScript** and uses the **Lovable Cloud backend** for all data (actors, presets, images, etc.).  
You do **not** need to set up your own database or image storage to run it locally — the app talks directly to the existing Lovable backend.

---

## 1. What’s Included (and What Isn’t)

- ✅ **Codebase** (React app, pages, components)
- ✅ **Backend APIs & database** (actors, presets, favorites, etc.) — hosted by **Lovable Cloud**
- ✅ **Stored images** (actor portraits, preset thumbnails, etc.) — also hosted by **Lovable Cloud**
- ❌ **Local database dump** — not required to run the app
- ❌ **Local image files for all actors** — they live in Lovable’s storage, not in this repo

When you run the app locally, it should **load actors and images from the remote Lovable backend**, as long as your `.env` file is set correctly.

---

## 2. Prerequisites (Windows / macOS / Linux)

You **do not need Docker** to get this running. Docker/self‑hosting is optional and more advanced.

You will need:

- [Node.js](https://nodejs.org/) (LTS version recommended)
- [Git](https://git-scm.com/) (to clone the repo)
- A terminal (Command Prompt, PowerShell, or Windows Terminal on Windows)

---

## 3. Get the Environment Variables

The app talks to the Lovable backend using environment variables.

In the Lovable project, these variables are already configured:

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_PUBLISHABLE_KEY`
- `VITE_SUPABASE_PROJECT_ID`

To run locally, you need a `.env` file in the project root that contains these values.

1. In Lovable, open your project.
2. Go to **Settings → Environment** (or similar) and copy the values.
3. On your PC, create a file named `.env` in the project root and add:

   ```bash
   VITE_SUPABASE_URL="https://...your-url..."
   VITE_SUPABASE_PUBLISHABLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   VITE_SUPABASE_PROJECT_ID="pvlqwxkgovjwqhpqnssl"
You don’t need to change these values — they already point to the same backend Lovable uses.

4. Clone and Run the Project (No Docker)
From your terminal:


# 1. Clone the repository
git clone <YOUR_REPO_URL>
cd <YOUR_PROJECT_FOLDER>

# 2. Install dependencies
npm install

# 3. Start the dev server
npm run dev
Then open the URL shown in the terminal (usually http://localhost:5173 or http://localhost:8080 depending on config).

If your .env is correct, you should see:

All 525+ actors loaded from the backend
Actor images pulled from Lovable Cloud storage
Presets, favorites, and collections working as in the hosted version
5. Why You “Can’t Get All the Database Included”
The database (actors, presets, reviews, stories, etc.) lives in the Lovable Cloud backend, not in this Git repo.
The images (actor portraits, thumbnails) live in Lovable Cloud storage.
The frontend (this project) always talks to that backend using the environment variables.
If you want a copy of the actors or presets data (for backup or analysis), you can:

Export tables from the backend UI (actors, portrait_presets, etc.) to CSV/JSON.
Or add an export feature in the app (for example, “Download actors as JSON”).
But you do not need a local copy of the database to develop or run the app.

6. About Docker / Self‑Hosting
If you’re on Windows and trying to use Docker:

Docker is not required for normal development.
Self‑hosting with Docker means you must also bring your own database + storage and wire it up — this is more advanced and currently not needed if you’re okay using the Lovable backend.
If your goal is simply:

“Run the app on my PC and still use the existing actors, presets, and images”

Then skip Docker and just:

Clone repo
Create .env with the Lovable backend values
npm install
npm run dev
7. Quick Troubleshooting
Actors don’t load / list is empty

Check that .env exists in the project root.
Make sure VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY match the values from Lovable.
Restart npm run dev after editing .env.
Images are broken / 404

Same as above: incorrect or missing .env usually causes broken image URLs.
Check the browser console for network errors pointing to the wrong URL.
8. Using the Lovable Backend Interface
You can inspect and manage data (actors, presets, favorites, etc.) from the backend UI:

View/edit actors
View/edit presets and collections
Inspect favorites, stories, and more
This is all handled by Lovable Cloud — no separate Supabase account or dashboard needed.

9. Summary
You can run the project locally without Docker.
The database and images stay in the Lovable backend and are accessed via .env env vars.
Cloning the repo + .env + npm run dev is enough to see all actors and images locally.