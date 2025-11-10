# DSA508 Assignment: MFlix Database Analysis & Dashboard

## Student Submission

This project provides a comprehensive analysis of the MFlix movie streaming database with an interactive dashboard.

---

## 📁 Project Structure

```
test-2/
├── README.md                        # This file
├── requirements.txt                 # Python dependencies
├── problem1_eda_analysis.ipynb      # Problem 1: EDA and topic modeling
├── problem2_narrative.md            # Problem 2: Business narrative
├── streamlit_dashboard.py           # Problem 2: Interactive dashboard
└── Sample_mflix/                    # Original data files
    ├── movies.json
    ├── comments.json
    ├── theaters.json
    ├── users.json
    └── sessions.json
```

---

## 🚀 Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Internet connection (for Azure Cosmos DB access)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Download NLTK Data (Required for Problem 1)

```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

---

## 📊 Problem 1: Running the EDA Notebook

### Launch Jupyter Notebook

```bash
jupyter notebook
```

Open `problem1_eda_analysis.ipynb` and run all cells (`Cell` → `Run All`).

### What's Included

- **Part A**: Comprehensive EDA with MongoDB aggregation pipelines
- **Part B**: Temporal and genre analysis with text analytics
- **Part C**: Topic modeling (LDA & NMF) with narrative interpretation

---

## 🎬 Problem 2: Running the Dashboard

### Launch the Dashboard

```bash
streamlit run streamlit_dashboard.py
```

The dashboard will open automatically at `http://localhost:8501`

### Dashboard Features

1. **Overview** - Key metrics and rating distributions
2. **Movie Analytics** - Top rated movies and genre performance
3. **Temporal Trends** - Production and rating trends by decade
4. **Geographic View** - Interactive map of theater locations
5. **User Engagement** - Comment metrics and most discussed movies
6. **Search Movies** - Filter by title, genre, and year

### Business Narrative

See `problem2_narrative.md` for comprehensive business context and dashboard purpose.

---

## 🔗 Azure Cosmos DB Connection

The project connects to Azure Cosmos DB (MongoDB API):
- **Database**: `Sample_mflix`
- **Collections**: movies, comments, users, theaters, sessions
- Connection string is embedded in the code

---

## 📦 Deliverables

### Problem 1 ✅
- Comprehensive EDA with descriptive statistics
- Temporal analysis of ratings and production trends
- Genre-based text analysis with word clouds
- Topic modeling (LDA and NMF)
- Narrative interpretation with business insights

### Problem 2 ✅
- Azure Cosmos DB with MFlix data
- Streamlit dashboard with 6 interactive pages
- Multiple visualizations (charts, maps, tables)
- Business narrative document
- Real-time cloud database connection

---

## 🛠️ Technologies Used

- **Database**: Azure Cosmos DB (MongoDB API), PyMongo
- **Analysis**: Pandas, NumPy, Scikit-learn, NLTK
- **Visualization**: Matplotlib, Seaborn, Plotly, Folium, WordCloud
- **Dashboard**: Streamlit
- **Development**: Jupyter Notebook

---

## 🐛 Troubleshooting

### Issue: MongoDB connection timeout
- Check internet connection
- Verify firewall isn't blocking MongoDB ports

### Issue: Missing NLTK data
- Run: `python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"`

### Issue: Dashboard won't start
- Ensure Streamlit is installed: `pip install streamlit`
- Try: `python -m streamlit run streamlit_dashboard.py`

---

## 📝 Notes

- Virtual environment (`env/` folder) and NLTK data (`nltk_data/` folder) are not part of the submission—these are generated locally during setup
- All analysis can be reproduced by following the setup instructions above

---

**Course**: DSA508 - Big Data Platforms & Analytics  
**Date**: November 2024
