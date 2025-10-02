import os
import datetime
import json
import requests
import dotenv
from lxml import html
import matplotlib.pyplot as plt
import drawsvg as draw
import pygame as pg

# --- Rainfall Chart Plotting ---
import ast

def load_rainfall_data(xml_path):
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()
    start = content.find('"code":"RF"')
    if start == -1:
        raise ValueError('Rainfall data (RF) not found in file.')
    monthdata_start = content.find('"monthData":[', start)
    if monthdata_start == -1:
        raise ValueError('monthData not found for RF.')
    bracket_count = 0
    i = monthdata_start + len('"monthData":[')
    while i < len(content):
        if content[i] == '[':
            bracket_count += 1
        elif content[i] == ']':
            if bracket_count == 0:
                break
            bracket_count -= 1
        i += 1
    monthdata_str = content[monthdata_start + len('"monthData":'):i+1]
    monthdata = ast.literal_eval(monthdata_str)
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

def plot_rainfall_for_year(xml_path, year):
    years, rainfall = load_rainfall_data(xml_path)
    if year not in years:
        raise ValueError(f"Year {year} not found in rainfall data.")
    idx = years.index(year)
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    vals = rainfall[idx]
    max_idx = vals.index(max(vals))
    min_idx = vals.index(min(vals))
    color_orange = '#ea801c'
    color_blue = '#1a80bb'
    color_gray = '#b8b8b8'
    colors = [color_gray] * 12
    colors[max_idx] = color_orange
    colors[min_idx] = color_blue
    fig, ax = plt.subplots(figsize=(10,5))
    bars = ax.bar(months, vals, color=colors)
    ax.set_title(f"Monthly Rainfall in Hong Kong ({year})")
    ax.set_xlabel("Month")
    ax.set_ylabel("Rainfall (mm)")
    import matplotlib.patches as mpatches
    orange_patch = mpatches.Patch(color=color_orange, label='Highest Month')
    blue_patch = mpatches.Patch(color=color_blue, label='Lowest Month')
    ax.legend(handles=[orange_patch, blue_patch], loc='upper right', frameon=False)
    plt.tight_layout()
    return fig, ax

def show_and_download_menu(xml_path):
    years, _ = load_rainfall_data(xml_path)
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
        fig, ax = plot_rainfall_for_year(xml_path, choice)
        plt.show()
        save = input("Download this chart as PNG? (y/n): ").strip().lower()
        if save == 'y':
            out_dir = "rainfall_charts"
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            out_path = os.path.join(out_dir, f"rainfall_{choice}.png")
            fig.savefig(out_path)
            print(f"Chart saved to {out_path}")
        plt.close(fig)

if __name__ == "__main__":
    try:
        xml_path = os.path.join(os.path.dirname(__file__), 'data', 'monthlyElement.xml')
        show_and_download_menu(xml_path)
    except Exception as e:
        print(f"Error: {e}")
