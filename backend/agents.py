from flask import Flask, request, jsonify
from google import genai
import requests
import os
import folium
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize the LLM client
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable is not set. Please check your .env file.")
client = genai.Client(api_key=api_key)

# Data analysis helper functions
def load_household_data(dataset_type: str) -> pd.DataFrame:
    """Load household income or expenditure data from CSV files."""
    try:
        if dataset_type == "income":
            df = pd.read_csv("data/household_income.csv", skiprows=10)
            
            # First row contains the sub-headers (Average/Median)
            subheaders = df.iloc[0].fillna('')
            
            # Create proper column names by combining main header with sub-header
            new_columns = []
            for i, col in enumerate(df.columns):
                subheader = str(subheaders.iloc[i]).strip()
                
                if col.startswith('Unnamed') and subheader and subheader != 'nan':
                    # For unnamed columns, use the parent column name + subheader
                    # Find the previous non-unnamed column
                    parent_col = None
                    for j in range(i-1, -1, -1):
                        if not df.columns[j].startswith('Unnamed'):
                            parent_col = df.columns[j]
                            break
                    if parent_col:
                        new_columns.append(f"{parent_col} - {subheader}")
                    else:
                        new_columns.append(subheader)
                elif subheader and subheader != 'nan' and subheader != '':
                    new_columns.append(f"{col} - {subheader}")
                else:
                    new_columns.append(col)
            
            # Remove any empty string columns
            df.columns = new_columns
            df = df.loc[:, df.columns != '']
            
            # Clean up column names - replace Median1/ with Median
            df.columns = [col.replace('Median1/', 'Median') for col in df.columns]
            
            # Remove the sub-header row
            df = df.iloc[1:].reset_index(drop=True)
            
            # Convert Year column to numeric
            df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
            df = df.dropna(subset=['Year'])
            
            # Convert other numeric columns
            for col in df.columns:
                if col != 'Year':
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        else:
            return None
        
        # Clean column names
        df.columns = df.columns.str.strip()
        # Drop rows where all values are NaN
        df = df.dropna(how='all')
        return df
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return None

def analyze_data(df: pd.DataFrame, analysis_type: str) -> str:
    """Perform analysis on the dataset."""
    if df is None or df.empty:
        return "No data available for analysis"
    
    try:
        if analysis_type == "summary":
            # Get summary statistics for numeric columns only
            numeric_df = df.select_dtypes(include=['float64', 'int64'])
            if numeric_df.empty:
                return "No numeric data available for summary statistics"
            
            summary = numeric_df.describe()
            
            # Format as a more readable string
            result = "Summary Statistics:\n\n"
            for col in summary.columns:
                # Skip columns with NaN values or zero count
                if pd.isna(summary[col]['count']) or summary[col]['count'] == 0:
                    continue
                    
                result += f"📊 {col}\n"
                result += f"   Count: {summary[col]['count']:.0f}\n"
                result += f"   Mean: ${summary[col]['mean']:,.2f}\n"
                result += f"   Std Dev: ${summary[col]['std']:,.2f}\n"
                result += f"   Min: ${summary[col]['min']:,.2f}\n"
                result += f"   25%: ${summary[col]['25%']:,.2f}\n"
                result += f"   Median: ${summary[col]['50%']:,.2f}\n"
                result += f"   75%: ${summary[col]['75%']:,.2f}\n"
                result += f"   Max: ${summary[col]['max']:,.2f}\n\n"
            
            return result.strip()
        
        elif analysis_type == "trend":
            # Analyze trends over time (if year column exists)
            if 'year' in df.columns.str.lower():
                year_col = [col for col in df.columns if 'year' in col.lower()][0]
                numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
                if len(numeric_cols) > 0:
                    trends = f"Trends over time:\n"
                    for col in numeric_cols[:3]:  # Limit to first 3 numeric columns
                        if df[col].notna().sum() > 1:
                            first_val = df[col].iloc[0]
                            last_val = df[col].iloc[-1]
                            change = ((last_val - first_val) / first_val * 100) if first_val != 0 else 0
                            trends += f"{col}: {change:.2f}% change\n"
                    return trends
            return "No time-based data found for trend analysis"
        
        elif analysis_type == "correlation":
            # Calculate correlations between numeric columns
            numeric_df = df.select_dtypes(include=['float64', 'int64'])
            if numeric_df.shape[1] > 1:
                corr = numeric_df.corr()
                return f"Correlation Matrix:\n{corr.to_string()}"
            return "Not enough numeric columns for correlation analysis"
        
        return "Analysis type not supported"
    except Exception as e:
        return f"Error during analysis: {str(e)}"

def create_visualization(df: pd.DataFrame, viz_type: str, dataset_name: str) -> str:
    """Create visualizations and save as image files."""
    if df is None or df.empty:
        return "No data available for visualization"
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{dataset_name}_{viz_type}_{timestamp}.png"
        filepath = os.path.join("frontend", "static", "img", filename)
        
        plt.figure(figsize=(12, 7))
        
        if viz_type == "line":
            # Line plot for trends over time
            # Check if Year column exists for x-axis
            x_axis = df['Year'] if 'Year' in df.columns else df.index
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
            # Exclude Year from plotting
            numeric_cols = [col for col in numeric_cols if col != 'Year']
            
            if len(numeric_cols) > 0:
                for col in numeric_cols[:3]:  # Plot first 3 numeric columns
                    if df[col].notna().sum() > 1:
                        plt.plot(x_axis, df[col], marker='o', label=col, linewidth=2, markersize=6)
                
                plt.xlabel('Year' if 'Year' in df.columns else 'Index', fontsize=12)
                plt.ylabel('Value ($)', fontsize=12)
                plt.title(f'{dataset_name.title()} Trends Over Time', fontsize=14, fontweight='bold')
                plt.legend(fontsize=10, loc='best')
                plt.grid(True, alpha=0.3)
                plt.xticks(rotation=45)
        
        elif viz_type == "bar":
            # Bar plot
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
            if len(numeric_cols) > 0:
                df[numeric_cols[0]].head(10).plot(kind='bar', color='steelblue')
                plt.xlabel('Category')
                plt.ylabel('Value')
                plt.title(f'{dataset_name.title()} Bar Chart')
                plt.xticks(rotation=45, ha='right')
        
        elif viz_type == "correlation":
            # Correlation heatmap
            numeric_df = df.select_dtypes(include=['float64', 'int64'])
            if numeric_df.shape[1] > 1:
                corr = numeric_df.corr()
                sns.heatmap(corr, annot=True, cmap='coolwarm', center=0)
                plt.title(f'{dataset_name.title()} Correlation Matrix')
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=100, bbox_inches='tight')
        plt.close()
        
        return f"PLOT:img/{filename}"
    except Exception as e:
        plt.close()
        return f"Error creating visualization: {str(e)}"

def singstat_agent(query: str) -> str:
    """Handles household income data queries using local CSV files - analyzes and visualizes income data."""
    
    # Determine what the user wants
    def determine_intent(user_query: str) -> dict:
        """Use LLM to determine user's intent for data analysis."""
        prompt = f"""Analyze this query about Singapore household income data and determine:
1. Task: "visualize" (always use this for graphs/plots/charts/trends over time), "summary" (statistics only), "correlation" (correlation analysis only)
2. Plot type: "line" (for trends/time series), "bar" (for comparisons), or "correlation" (for correlation heatmap)

User query: {user_query}

Respond in format: task|plot_type
Example: visualize|line
Note: If user asks about trends over time, use visualize|line"""

        try:
            response = client.models.generate_content(
                model="models/gemini-2.0-flash",
                contents=prompt
            )
            parts = response.text.strip().lower().split('|')
            return {
                'task': parts[0] if len(parts) > 0 else 'visualize',
                'plot_type': parts[1] if len(parts) > 1 else 'line'
            }
        except Exception as e:
            print(f"Error determining intent: {str(e)}")
            return {'task': 'visualize', 'plot_type': 'line'}
    
    intent = determine_intent(query)
    
    # Load household income dataset
    df = load_household_data('income')
    
    if df is None:
        return "Failed to load household data"
    
    # Perform the requested task
    if intent['task'] == 'visualize' and intent['plot_type'] != 'none':
        # Generate visualization
        plot_result = create_visualization(df, intent['plot_type'], 'income')
        
        # Add basic analysis text with proper separator
        analysis_text = ""
        
        if intent['plot_type'] == 'line' and 'Year' in df.columns:
            # Add trend analysis
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
            numeric_cols = [col for col in numeric_cols if col != 'Year']
            
            if len(numeric_cols) > 0:
                analysis_text = f"\n\n📈 Key Insights for Income:\n"
                for col in numeric_cols[:3]:
                    if df[col].notna().sum() > 1:
                        first_val = df[col].dropna().iloc[0]
                        last_val = df[col].dropna().iloc[-1]
                        first_year = df[df[col].notna()]['Year'].iloc[0]
                        last_year = df[df[col].notna()]['Year'].iloc[-1]
                        change = ((last_val - first_val) / first_val * 100) if first_val != 0 else 0
                        
                        analysis_text += f"\n• {col}:"
                        analysis_text += f"\n   Changed from ${first_val:,.2f} ({int(first_year)}) to ${last_val:,.2f} ({int(last_year)})"
                        analysis_text += f"\n   Growth: {change:+.1f}%"
                        analysis_text += f"\n   Average: ${df[col].mean():,.2f}\n"
        
        elif intent['plot_type'] == 'bar':
            # Add summary for bar charts
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
            if len(numeric_cols) > 0:
                col = numeric_cols[0]
                analysis_text = f"\n\n📊 Summary for {col}:"
                analysis_text += f"\n• Highest: ${df[col].max():,.2f}"
                analysis_text += f"\n• Lowest: ${df[col].min():,.2f}"
                analysis_text += f"\n• Average: ${df[col].mean():,.2f}"
        
        # Use special separator that frontend can parse
        if plot_result.startswith("PLOT:"):
            return plot_result + "|TEXT|" + analysis_text
        return plot_result + analysis_text
    else:
        return analyze_data(df, intent['task'])

def generate_weather_map() -> str:
    """Generate a folium map showing 2-hour weather forecast for Singapore."""
    api_url = "https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast"
    
    try:
        response = requests.get(api_url)
        if response.status_code != 200:
            return "Failed to fetch weather data for map"
        
        data = response.json()
        items = data.get("data", {}).get("items", [])
        area_metadata = data.get("data", {}).get("area_metadata", [])
        
        if not items or not area_metadata:
            return "No weather data available for map"
        
        forecasts = items[0].get("forecasts", [])
        
        # Create map centered on Singapore
        singapore_map = folium.Map(
            location=[1.3521, 103.8198],
            zoom_start=11,
            tiles="OpenStreetMap"
        )
        
        # Color mapping for weather conditions
        weather_colors = {
            "Fair": "green",
            "Partly Cloudy": "lightgreen",
            "Cloudy": "gray",
            "Light Rain": "lightblue",
            "Moderate Rain": "blue",
            "Heavy Rain": "darkblue",
            "Showers": "blue",
            "Light Showers": "lightblue",
            "Heavy Showers": "darkblue",
            "Thundery Showers": "red",
            "Heavy Thundery Showers": "darkred"
        }
        
        # Create a dictionary for quick forecast lookup
        forecast_dict = {f.get("area"): f.get("forecast") for f in forecasts}
        
        # Add markers for each area
        for area in area_metadata:
            area_name = area.get("name")
            location = area.get("label_location", {})
            lat = location.get("latitude")
            lon = location.get("longitude")
            
            if lat and lon and area_name in forecast_dict:
                forecast = forecast_dict[area_name]
                color = weather_colors.get(forecast, "gray")
                
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=8,
                    popup=f"<b>{area_name}</b><br>{forecast}",
                    color=color,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.6
                ).add_to(singapore_map)
        
        # Save map to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        map_filename = f"weather_map_{timestamp}.html"
        map_path = os.path.join("frontend", "static", map_filename)
        singapore_map.save(map_path)
        
        return f"MAP:{map_filename}"
    
    except Exception as e:
        return f"Error generating map: {str(e)}"

def datagov_agent(query: str) -> str:
    """Handles weather forecast queries from Data.gov.sg (24-hour, 2-hour, and 4-day forecasts)."""
    
    # Check if user wants a map
    def wants_map(user_query: str) -> bool:
        """Determine if user wants a visual map."""
        query_lower = user_query.lower()
        map_keywords = ["map", "show me", "visualize", "visual", "display", "geospatial", "geographic"]
        return any(keyword in query_lower for keyword in map_keywords)
    
    if wants_map(query):
        return generate_weather_map()
    
    # Use LLM to determine which forecast type to use
    def determine_forecast_type(user_query: str) -> str:
        """Use Gemini LLM to determine which weather forecast API to call."""
        prompt = f"""You are a weather forecast assistant. Analyze the user's query and determine which type of weather forecast they want.

Available forecast types:
1. "2hour" - Very short-term forecast, next 2 hours, immediate weather, current conditions by area, next hour
2. "4day" - Multi-day outlook, tomorrow, next few days, extended forecast, weekend weather, next day
3. "24hour" - General/today's weather, default forecast

User query: {user_query}

Respond with ONLY one word: either "2hour", "4day", or "24hour"."""

        try:
            response = client.models.generate_content(
                model="models/gemini-1.5-flash",
                contents=prompt
            )
            forecast_type = response.text.strip().lower()
            if forecast_type in ["2hour", "4day", "24hour"]:
                return forecast_type
            else:
                return "24hour"  # default
        except Exception as e:
            print(f"Error determining forecast type: {str(e)}")
            return "24hour"  # default
    
    forecast_type = determine_forecast_type(query)
    
    try:
        if forecast_type == "2hour":
            # 2-hour forecast
            api_url = "https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast"
            response = requests.get(api_url)
            if response.status_code == 200:
                data = response.json()
                items = data.get("data", {}).get("items", [])
                if items:
                    forecasts = items[0].get("forecasts", [])
                    if forecasts:
                        # Group forecasts by weather condition
                        forecast_dict = {}
                        for f in forecasts:
                            forecast_type = f.get('forecast', 'Unknown')
                            area = f.get('area', 'Unknown')
                            if forecast_type not in forecast_dict:
                                forecast_dict[forecast_type] = []
                            forecast_dict[forecast_type].append(area)
                        
                        # Format output
                        result = "2-hour forecast:\n"
                        for forecast_type, areas in forecast_dict.items():
                            result += f"{forecast_type}: {', '.join(areas[:5])}"
                            if len(areas) > 5:
                                result += f" and {len(areas) - 5} more areas"
                            result += "\n"
                        return result.strip()
                    else:
                        return "No 2-hour forecast data available"
                else:
                    return "No 2-hour forecast items available"
            else:
                return f"Failed to fetch 2-hour forecast. Status code: {response.status_code}"
                
        elif forecast_type == "4day":
            # 4-day outlook
            api_url = "https://api-open.data.gov.sg/v2/real-time/api/four-day-outlook"
            response = requests.get(api_url)
            if response.status_code == 200:
                data = response.json()
                records = data.get("data", {}).get("records", [])
                if records:
                    forecasts = records[0].get("forecasts", [])
                    if forecasts:
                        outlook_list = []
                        for f in forecasts:
                            day = f.get("day", "Unknown")
                            temp_low = f.get("temperature", {}).get("low", "N/A")
                            temp_high = f.get("temperature", {}).get("high", "N/A")
                            forecast_text = f.get("forecast", {}).get("summary", "N/A")
                            outlook_list.append(f"{day}: {forecast_text}, {temp_low}-{temp_high}°C")
                        return "4-day outlook:\n" + "\n".join(outlook_list)
                    else:
                        return "No forecast data available in 4-day outlook"
                else:
                    return "No 4-day outlook records available"
            else:
                return f"Failed to fetch 4-day outlook. Status code: {response.status_code}"
                
        else:  # "24hour" or default
            # Default 24-hour forecast
            api_url = "https://api.data.gov.sg/v1/environment/24-hour-weather-forecast"
            response = requests.get(api_url)
            if response.status_code == 200:
                data = response.json()
                forecast = data.get("items", [{}])[0].get("general", {}).get("forecast", "No forecast available")
                return f"24-hour forecast: {forecast}"
            else:
                return f"Failed to fetch 24-hour forecast. Status code: {response.status_code}"
                
    except Exception as e:
        return f"An error occurred while fetching data: {str(e)}"

# Define the LLM Router using Gemini
def llm_router(query):
    """Use Gemini LLM to route the query to the appropriate agent."""
    prompt = f"""You are a routing assistant. Given a user query, determine which agent should handle it.

Available agents:
1. "singstat" - Handles household income data queries from SingStat
2. "datagov" - Handles weather forecast queries from Data.gov.sg

User query: {query}

Respond with ONLY one word: either "singstat" or "datagov". If the query doesn't match either agent, respond with "unknown"."""

    try:
        response = client.models.generate_content(
            model="models/gemini-2.0-flash",
            contents=prompt
        )
        route = response.text.strip().lower()
        if route in ["singstat", "datagov"]:
            return route
        else:
            return "unknown"
    except Exception as e:
        print(f"Error in routing: {str(e)}")
        return "unknown"

@app.route("/query", methods=["POST"])
def handle_query():
    user_query = request.json.get("query")
    if not user_query:
        return jsonify({"error": "Query is required"}), 400

    # Route the query
    agent = llm_router(user_query)
    if agent == "singstat":
        result = singstat_agent(user_query)
    elif agent == "datagov":
        result = datagov_agent(user_query)
    else:
        # Use Gemini LLM for general queries
        try:
            response = client.models.generate_content(
                model="models/gemini-2.0-flash",
                contents=user_query
            )
            result = response.text if response.text else "No response from model"
        except Exception as e:
            result = f"Error generating response: {str(e)}"

    return jsonify({"response": result})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)