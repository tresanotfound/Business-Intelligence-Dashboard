# Business-Intelligence-Dashboard
This is a Business Intelligence (BI) Dashboard repository
[BI Dashboard Link](https://businessintelligence-dashboard.streamlit.app/)

## Description
The **Marketing Intelligence Dashboard** (ie BI Dashboard) is a Streamlit application designed to consolidate, visualize, and analyze marketing data from multiple platforms. It allows businesses to track performance metrics, compare campaign effectiveness across channels, and make data-driven marketing decisions efficiently.

## Purpose
The main objectives of this project are:
- Centralize marketing data from platforms like Google, Facebook, and TikTok.  
- Generate key performance indicators (KPIs) and metrics for business analysis.  
- Provide interactive visualizations to support quick decision-making.  
- Serve as a prototype for integrating marketing analytics in business intelligence workflows.

## Folder Structure
business-intelligence-dashboard/:
-├── data/                         # Input CSV files
-│ ├── Google.csv
-│ ├── Facebook.csv
-│ ├── TikTok.csv
-│ └── business.csv 
-├── app.py                        # Main Streamlit application
-├── data_prep.py                  # Data cleaning & metric calculations
-├── requirements.txt              # Python dependencies
-├── README.md                     # Project documentation
-├── LICENSE                       # Project license (optional)
-├── .gitignore                    # Git ignore rules


## Approach
1. **Data Collection:** Import marketing data from multiple CSV files.  
2. **Data Cleaning & Preparation:**  
   - Standardize column names and formats.  
   - Handle missing or inconsistent data.  
   - Calculate essential metrics and KPIs.  
3. **Visualization:**  
   - Use Streamlit to create interactive charts, tables, and dashboards.  
   - Provide insights at both platform-level and overall business performance.  
4. **Deployment:**  
   - Hosted on Streamlit Community Cloud for easy sharing and access.  

## Technology Used
- **Python** – Core programming language.  
- **Streamlit** – Framework for building interactive web apps.  
- **Pandas & NumPy** – Data manipulation and processing.  
- **Matplotlib / Seaborn** – Data visualization.  
- **Git & GitHub** – Version control and repository management.  

## Installation & Setup
1. **Clone the repository:**
git clone https://github.com/tresanotfound/Business-Intelligence-Dashboard.git
2. **Create a virtual environment:**
python -m venv venv
source venv/bin/activate
3. **Install dependencies:**
pip install -r requirements.txt
4. **Run the Streamlit app:**
streamlit run app.py


