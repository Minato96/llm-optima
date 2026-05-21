import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

# Smaller files = fewer tokens per run (critical for rate limits and cost).
MAX_ROWS_PER_FILE = 400

load_dotenv()
client = OpenAI(api_key=os.getenv("OPEN_AI_API"))
CONFIG_PATH = Path("openai_config.json")

print("1. Fetching datasets (trimmed for demo cost control)...")

print("Downloading Superstore Sales Data...")
try:
    sales_url = (
        "https://raw.githubusercontent.com/yajasarora/"
        "Superstore-Sales-Analysis-with-Tableau/master/Superstore%20sales%20dataset.csv"
    )
    sales_df = pd.read_csv(sales_url, encoding="latin1").head(MAX_ROWS_PER_FILE)
    sales_df.to_csv("real_sales_data.csv", index=False, encoding="utf-8")
    print(f"-> Sales: {len(sales_df)} rows saved.")
except Exception as e:
    print(f"-> Sales failed ({e}); using fallback.")
    pd.DataFrame(
        {"Order": range(200), "Sales": np.random.uniform(10, 1000, 200)}
    ).to_csv("real_sales_data.csv", index=False)

print("Downloading IBM HR Analytics Data...")
try:
    hr_url = (
        "https://raw.githubusercontent.com/Minato96/coin-gecko/refs/heads/main/"
        "WA_Fn-UseC_-HR-Employee-Attrition.csv"
    )
    hr_df = pd.read_csv(hr_url).head(MAX_ROWS_PER_FILE)
    hr_df.to_csv("real_hr_payroll_data.csv", index=False)
    print(f"-> HR: {len(hr_df)} rows saved.")
except Exception as e:
    print(f"-> HR failed ({e}); using fallback.")
    np.random.seed(42)
    pd.DataFrame(
        {
            "EmployeeNumber": range(1, 201),
            "Department": np.random.choice(
                ["Sales", "Research & Development", "Human Resources"], 200
            ),
            "JobRole": np.random.choice(
                ["Executive", "Manager", "Developer", "Analyst"], 200
            ),
            "MonthlyIncome": np.random.normal(6500, 2000, 200).round(2),
            "Attrition": np.random.choice(["Yes", "No"], 200, p=[0.16, 0.84]),
        }
    ).to_csv("real_hr_payroll_data.csv", index=False)
    print("-> HR fallback: 200 rows.")

print("Downloading market data...")
try:
    stock_url = (
        "https://raw.githubusercontent.com/plotly/datasets/master/"
        "finance-charts-apple.csv"
    )
    stock_df = pd.read_csv(stock_url).head(MAX_ROWS_PER_FILE)
    stock_df.to_csv("real_market_data.csv", index=False)
    print(f"-> Market: {len(stock_df)} rows saved.")
except Exception as e:
    print(f"-> Market failed ({e}); using fallback.")
    pd.DataFrame(
        {
            "Date": pd.date_range("2020-01-01", periods=200),
            "AAPL.Close": np.random.normal(150, 10, 200),
        }
    ).to_csv("real_market_data.csv", index=False)

print("\n2. Uploading to OpenAI...")
sales_file = client.files.create(
    file=open("real_sales_data.csv", "rb"), purpose="assistants"
)
hr_file = client.files.create(
    file=open("real_hr_payroll_data.csv", "rb"), purpose="assistants"
)
stock_file = client.files.create(
    file=open("real_market_data.csv", "rb"), purpose="assistants"
)

print("\n3. Creating reusable assistant...")
assistant = client.beta.assistants.create(
    name="Enterprise Financial AI",
    instructions=(
        "You are an enterprise financial analyst. Use pandas for math. "
        "For charts use matplotlib, plt.tight_layout(), plt.show(). "
        "Keep text answers concise."
    ),
    model="gpt-4o-mini",
    tools=[{"type": "code_interpreter"}],
)

config = {
    "assistant_id": assistant.id,
    "file_ids": {
        "sales": sales_file.id,
        "hr": hr_file.id,
        "market": stock_file.id,
    },
}
with CONFIG_PATH.open("w", encoding="utf-8") as f:
    json.dump(config, f, indent=2)

print("\n=== Done. Config written to openai_config.json ===")
print(f"assistant_id = {assistant.id}")
print(f'sales = "{sales_file.id}"')
print(f'hr = "{hr_file.id}"')
print(f'market = "{stock_file.id}"')
print("\nRun: streamlit run app.py")
