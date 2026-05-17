# 🌾 Smart KisanJal Platform

A multilingual (English, Hindi, Marathi, Gujarati, Bengali, Tamil) web platform for Indian farmers to access government schemes, get smart irrigation recommendations, and manage complaints — fully error-free and production-ready.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the App
```bash
streamlit run app.py
```

Opens at `http://localhost:8501`

---

## 🔐 Default Credentials

| Role   | Username / Phone | Password |
|--------|-----------------|----------|
| Admin  | `admin`         | `admin`  |
| Farmer | Any 10-digit number | Set during registration |

---

## 📁 Project Structure

```
smart_kisan/
├── app.py                 # Main entry point & routing
├── auth.py                # Login & registration
├── farmer_dashboard.py    # All farmer features
├── admin_dashboard.py     # All admin features
├── ai_logic.py            # Rule-based AI recommendations
├── database.py            # SQLite setup & CRUD helpers
├── translations.py        # 6-language translation strings + data constants
├── i18n_utils.py          # Localisation utilities
├── requirements.txt
└── smart_kisan.db         # Auto-created SQLite database
```

---

## ✨ Features

### Farmer Features
- 🌐 6 languages: English, Hindi, Marathi, Gujarati, Bengali, Tamil
- 👤 Profile with completeness progress bar
- 💧 Smart Irrigation Planner (crop + soil + water-source aware)
- 🔄 **Crop Rotation Advisor** with visual cycle timeline *(was missing — now fixed)*
- 🏛️ Government Scheme Matching (state / crop / category aware)
- 📋 Complaint system with auto AI priority + department routing
- 📚 Tutorial with pro tips for new users

### Admin Features
- 📊 Overview dashboard with 4 live metric cards + 4 charts
- 📋 Complaint management: filter by status / priority / state, update & reassign
- 🏛️ Scheme management: add, edit, delete
- 🗺️ Map views: complaint heatmap, water scarcity zones, scheme adoption
- 📜 **Activity Log** with action summaries *(was missing — now fixed)*

---

## 🐛 Bugs Fixed

| # | File | Bug | Fix |
|---|------|-----|-----|
| 1 | `farmer_dashboard.py` | **Crop Rotation tab was entirely missing** from `nav_items` — clicking "Crop Rotation" did nothing | Added `("rotation", lambda x: _show_rotation(farmer, x))` to nav |
| 2 | `admin_dashboard.py` | **Activity Log tab missing** — 5th tab never rendered | Added `with tabs[4]: _show_activity_log(lang)` |
| 3 | `translations.py` | **`DEPARTMENTS` list** missing `"State Disaster Management"` and `"Ministry of Jal Shakti"` — caused `ValueError` crash when admin updated any complaint routed by AI to those departments | Added both entries |
| 4 | `translations.py` | `get_text()` had no English fallback — raised `KeyError` on missing keys in non-English langs | Added double-fallback: `TRANSLATIONS['en'].get(key, key)` |
| 5 | All dashboards | Sidebar & metric emoji icons were empty strings (stripped during original editing) | Restored all icons: 👨‍🌾 🌾 💧 🔄 🏛️ 📋 etc. |
| 6 | `admin_dashboard.py` | `DEPARTMENTS.index(c["department"])` crashed with `ValueError` when complaint dept wasn't in the old short list | Added `curr_dept = c["department"] if c["department"] in DEPARTMENTS else DEPARTMENTS[0]` guard |
| 7 | All files | Filter dict lookups used `[]` — could `KeyError` on unexpected translated values | Changed all to `.get(key, default)` |

---

## 🌐 Deploy on Streamlit Cloud

1. Push this folder to GitHub  
2. Go to [share.streamlit.io](https://share.streamlit.io)  
3. Connect your repo, set main file to `app.py`  
4. Deploy!

> **Note:** For persistent data on Streamlit Cloud use a hosted DB (Supabase free tier) instead of SQLite.

---

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit + custom CSS (light green theme) |
| Database | SQLite (local) |
| Maps | Folium + streamlit-folium |
| Charts | Plotly Express / Graph Objects |
| Auth | bcrypt password hashing |
| AI | Rule-based expert system (no API needed) |
| i18n | 6-language custom translation engine |
