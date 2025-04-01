# UFC Pick'em App

A Flask web app for picking UFC fights, tracking scores, uploading avatars, and more.

## 🚀 Features
- User registration, login, and email verification
- Admin fight creation panel
- Pick winners + method of victory
- Underdog scoring system
- Leaderboard and user profiles
- Avatar upload (auto-crop and resize)
- Invite friends via email
- Mobile-friendly design
- Background fight sync (TheSportsDB)

## ⚙️ Local Setup

```bash
git clone https://github.com/bt012314/ufc-pickem.git
cd ufc-pickem
python -m venv venv
source venv/bin/activate    # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
flask db upgrade
flask run
