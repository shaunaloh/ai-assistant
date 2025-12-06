# AI Assistant for Singapore Weather & Household Income Analysis

## 🌐 Live Demo

**Access the application here:** [https://ai-assistant-bfys.onrender.com](https://ai-assistant-bfys.onrender.com)

## Problem Statement

In Singapore's tropical climate, weather conditions can change rapidly, and understanding forecast patterns is crucial for daily planning. Additionally, tracking household income trends over time provides valuable insights for policy-making and public understanding of economic progress.

This AI Assistant addresses two key challenges:

### 1. Weather Forecast Accessibility & Visualization
Civil servants and the public need:
- **Quick access to accurate weather forecasts** across different time horizons (immediate, daily, and extended forecasts)
- **Geospatial visualization of weather patterns** - particularly important in rainy Singapore where localized weather conditions vary significantly across different zones
- **Intelligent routing** to the appropriate forecast type based on natural language queries
- **Interactive maps** showing real-time weather conditions across Singapore's various areas

### 2. Household Income Trend Analysis
Policy makers and researchers need:
- **Clear visualization of household income trends** from 2000 to 2024
- **Comparative analysis** between average and median incomes across different household types
- **Year-specific insights** to understand economic changes at specific points in time
- **Statistical summaries** including growth rates and trend analysis

## Solution

An intelligent chatbot powered by Google Gemini AI that:
- Routes queries to specialized agents (weather or household income analysis)
- Provides multi-timeframe weather forecasts (2-hour, 24-hour, and 4-day)
- Generates interactive geospatial maps showing weather zones across Singapore
- Creates data visualizations (line charts, bar charts, correlation matrices)
- Delivers actionable insights with both visual and textual analysis

## Data Sources

### Weather Forecast Data
- **Source**: Data.gov.sg - Weather Forecast APIs
- **Link**: [https://data.gov.sg/datasets?coverage=&topics=environment&resultId=d_3f9e064e25005b0e42969944ccaf2e7a](https://data.gov.sg/datasets?coverage=&topics=environment&resultId=d_3f9e064e25005b0e42969944ccaf2e7a)
- **APIs Used**:
  - 2-Hour Weather Forecast (area-based, immediate conditions)
  - 24-Hour Weather Forecast (general daily outlook)
  - 4-Day Weather Outlook (extended forecast)

### Household Income Data
- **Source**: Singapore Department of Statistics (SingStat)
- **Link**: [https://tablebuilder.singstat.gov.sg/table/CT/17986](https://tablebuilder.singstat.gov.sg/table/CT/17986)
- **Dataset**: Average and Median Monthly Household Employment Income (Including Employer CPF Contributions) Among Resident and Resident Employed Households, 2000 - 2024
- **Metrics**: Average and Median income for both Resident Households and Resident Employed Households

## Features

- 🤖 **AI-Powered Query Routing** - Automatically determines whether user needs weather or income analysis
- 🌦️ **Multi-Timeframe Weather Forecasts** - 2-hour, 24-hour, and 4-day forecasts
- 🗺️ **Interactive Weather Maps** - Folium-based geospatial visualization with color-coded zones
- 📊 **Data Visualizations** - Line charts, bar charts, and correlation heatmaps
- 📈 **Trend Analysis** - 25 years of household income data (2000-2024)
- 💬 **Natural Language Interface** - Chat-based interaction with markdown-formatted responses
- 💾 **Conversation History** - SQLite database stores chat history

## Technology Stack

- **Backend**: Flask (Python)
- **AI/LLM**: Google Gemini API (gemini-2.0-flash)
- **Data Processing**: Pandas, NumPy
- **Visualization**: Matplotlib, Seaborn, Folium
- **Database**: SQLite with SQLAlchemy
- **Frontend**: HTML, CSS, JavaScript (AJAX)
- **APIs**: Data.gov.sg Weather APIs, SingStat CSV data (downloaded locally)

## Setup Instructions

### Prerequisites
- Python 3.10 or higher
- Github
- Google Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))

### Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/shaunaloh/ai-assistant.git
   cd ai-assistant
   ```

2. **Create and activate a virtual environment**
   
   **Windows (PowerShell):**
   ```powershell
   python -m venv ai_assistant_env
   .\ai_assistant_env\Scripts\Activate
   ```
   
   **macOS/Linux:**
   ```bash
   python3 -m venv ai_assistant_env
   source ai_assistant_env/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the project root directory:
   ```bash
   # .env
   GEMINI_API_KEY=your_gemini_api_key_here (not listing it here for security reasons)
   GOOGLE_MODEL=gemini-2.0-flash (or any of the Gemini models available)
   ```
   
   Replace `your_gemini_api_key_here` with your actual Gemini API key.

5. **Verify data files**
   
   Ensure the household income data file exists:
   ```
   data/household_income.csv
   ```
   
   This file should contain downloaded SingStat household income data from 2000-2024.

6. **Run the application**
   ```bash
   python backend/app.py
   ```
   
   The application will start on `http://localhost:8000`

7. **Access the application**
   
   Open your web browser and navigate to:
   ```
   http://localhost:8000
   ```

### Project Structure
```
ai-assistant/
├── backend/
│   ├── app.py              # Flask application and routes
│   ├── agents.py           # Separate AI agents for weather and income analysis
│   ├── database.py         # Database configuration
│   ├── models.py           # SQLAlchemy models
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── index.html          # Main chat interface
│   └── static/
│       ├── styles.css      # Styling
│       └── img/            # Generated visualizations
├── data/
│   └── household_income.csv # Household income dataset
├── .env                    # Environment variables (create this)
├── .gitignore             # Git ignore rules
├── render.yaml            # Render deployment config
└── README.md              # This file
```

### Example Queries

**Weather Forecasts:**
- "What's the weather for the next 2 hours?"
- "Show me tomorrow's weather forecast"
- "What's the weather like for the next 4 days?"
- "Show me a weather map of Singapore"

**Household Income Analysis:**
- "Show household income trends over time"
- "What was the household income in 2020?"


### Development Notes

- The SQLite database (`chat.db`) will be created automatically on first run
- Generated visualizations are saved in `frontend/static/img/`
- Weather maps are saved in `frontend/static/`
- Chat history persists across sessions via the database