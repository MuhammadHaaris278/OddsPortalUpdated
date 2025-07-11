# ⚽ OddsPortal Sports Odds Scraper

A professional-grade web application built with **Streamlit** that scrapes football (and other sports) match odds from [OddsPortal](https://www.oddsportal.com/) for the next 24 hours.  
Users can view, preview, and download results in **CSV**, **JSON**, and other formats, all through a slick UI.

---

## 🌐 Features

✅ Sticky navbar with scrollable sections  
✅ Hero section with animated introduction  
✅ Sport-based folder organization with icons (e.g. ⚽ Football, 🏀 Basketball)  
✅ Responsive grid layout for file downloads  
✅ CSV/JSON live preview in the browser  
✅ AOS (Animate On Scroll) UI animations  
✅ Professional dark-themed Streamlit interface  
✅ Clean footer with contact info  

---

## 🚀 Tech Stack

- **Frontend:** Streamlit (with HTML/CSS customizations)  
- **Backend:** Python scraping logic (`core/main.py`)  
- **Animations:** AOS.js (Animate On Scroll)  
- **File Preview:** pandas for data previews  
- **Output Format:** CSV / JSON / Text  

---

## 📦 Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/oddsportal-scraper.git
cd oddsportal-scraper

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```

---

## 🔧 Usage

```bash
# Run the Streamlit app
streamlit run app.py
```

Then open in browser: `http://localhost:8501`

---

## 🗂 Folder Structure

```
.
├── app.py                 # Main Streamlit app
├── core/
│   └── main.py            # Scraper logic (entry point: main())
├── output/                # Scraped files are saved here (auto-organized)
├── requirements.txt
└── README.md
```

---

## 🧪 Sample Use Case

- Scrape football odds daily
- Download CSV to feed into your betting model
- Quickly preview the scraped data in-browser
- Great for sports traders, data analysts, and scrapers
