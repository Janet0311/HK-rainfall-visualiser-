import os
import datetime
import json
import requests
import dotenv
from lxml import html
import matplotlib.pyplot as plt
import drawsvg as draw

# Import our custom utilities


print("All libraries imported successfully!")

# Display the loaded environment variables
dotenv.load_dotenv()

# Let's look at our scraping utilities
import inspect



# --- Rainfall Monthly Rate Table from monthlyElement.xml ---
def load_rainfall_data(xml_path):
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()
    data = json.loads(content)
    rf = None
    for section in data['stn']['data']:
        if section.get('code') == 'RF':
            rf = section
            break
    if not rf:
        raise ValueError('Rainfall data (RF) not found in file.')
    monthdata = rf['monthData']
    years = []
    rainfall = []
    for row in monthdata:
        year = row[0]
        vals = []
        for v in row[1:]:
            v = v.strip()
            if v in ("Trace", "", "***"):
                vals.append(0.0)
            else:
                try:
                    vals.append(float(v))
                except Exception:
                    vals.append(0.0)
        years.append(year)
        rainfall.append(vals)
    return years, rainfall

def print_rainfall_table(years, rainfall, year):
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    if year not in years:
        print(f"Year {year} not found in rainfall data.")
        return
    idx = years.index(year)
    print(f"\nRainfall Monthly Rate Table for {year}")
    print("Month\t" + "\t".join(months))
    print("Rain(mm)\t" + "\t".join(f"{v:.1f}" for v in rainfall[idx]))

def plot_rainfall_for_year(years, rainfall, year):
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    if year not in years:
        print(f"Year {year} not found in rainfall data.")
        return
    idx = years.index(year)
    plt.figure(figsize=(6, 4))
    manager = plt.get_current_fig_manager()
    try:
        manager.window.setGeometry(100, 100, 800, 500)
    except Exception:
        pass
    vals = rainfall[idx]
    max_idx = vals.index(max(vals))
    min_idx = vals.index(min(vals))
    colors = ['#b8b8b8'] * 12  # gray for others
    colors[max_idx] = '#ea801c'  # orange for highest
    colors[min_idx] = '#1a80bb'  # blue for lowest
    bars = plt.bar(months, vals, color=colors)
    # Add legend for colors
    import matplotlib.patches as mpatches
    orange_patch = mpatches.Patch(color='#ea801c', label='Highest Month')
    blue_patch = mpatches.Patch(color='#1a80bb', label='Lowest Month')
    plt.legend(handles=[orange_patch, blue_patch], loc='upper right')
    plt.title(f"Monthly Rainfall in Hong Kong ({year})", fontsize=16, fontweight='bold')
    plt.xlabel("Month", fontsize=12)
    plt.ylabel("Rainfall (mm)", fontsize=12)
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.show()
    print(f"\nRainfall Statistics:")
    vals = rainfall[idx]
    print(f"Highest: {max(vals):.1f} mm")
    print(f"Lowest: {min(vals):.1f} mm")
    print(f"Average: {sum(vals)/len(vals):.1f} mm")
    print(f"Range: {max(vals)-min(vals):.1f} mm")

if __name__ == "__main__":
    xml_path = os.path.join(os.path.dirname(__file__), 'data', 'monthlyElement.xml')
    years, rainfall = load_rainfall_data(xml_path)
    min_year = min(years)
    max_year = max(years)
    while True:
        print(f"\nChoose a year to view rainfall data (from {min_year} to {max_year})")
        choice = input("Enter year (or 'q' to quit): ").strip()
        if choice.lower() == 'q':
            print("Exiting.")
            break
        if choice not in years:
            print("Invalid year. Please try again.")
            continue
        year = choice
        print_rainfall_table(years, rainfall, year)
        plot_rainfall_for_year(years, rainfall, year)
