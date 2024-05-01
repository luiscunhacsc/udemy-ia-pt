# Nota: No caso de erro de importação de módulos, instale-os com o comando:
# pip install pandas yfinance pandas_ta fredapi python-dotenv

import pandas as pd
import yfinance as yf
import pandas_ta as ta
from fredapi import Fred
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()  # Carrega as variáveis de ambiente do arquivo .env (chave para a API do FRED)

# Set your FRED API key
fred_api_key = os.getenv('FRED_API_KEY')
fred = Fred(api_key=fred_api_key)

# Define date range (yyyy-mm-dd format)
user_start_date = "1990-01-02"
end_date = "2024-04-26"

# Calculate the pre-start date for technical indicators to initialize properly
# Assuming 90 days are enough to populate the required data for the indicators
pre_start_date = datetime.strptime(user_start_date, "%Y-%m-%d") - timedelta(days=90)
pre_start_date = pre_start_date.strftime("%Y-%m-%d")

# Fetch S&P 500 data from Yahoo Finance
sp500 = yf.download('^GSPC', start=pre_start_date, end=end_date)

# Fetch VIX and USDX data from Yahoo Finance
vix = yf.download('^VIX', start=pre_start_date, end=end_date)
usdx = yf.download('DX-Y.NYB', start=pre_start_date, end=end_date)

# Fetch EFFR, UNRATE, UMCSENT from FRED
effr = fred.get_series('DFF', pre_start_date, end_date)
unrate = fred.get_series('UNRATE', pre_start_date, end_date)
umcsent = fred.get_series('UMCSENT', pre_start_date, end_date)

# Reindex DataFrames to match trading days
vix = vix.reindex(sp500.index)
usdx = usdx.reindex(sp500.index)
effr = effr.reindex(sp500.index)
unrate = unrate.reindex(sp500.index)
umcsent = umcsent.reindex(sp500.index)

# Fill missing UNRATE and UMCSENT values with the last known value
usdx['Close'] = usdx['Close'].fillna(method='ffill').fillna(method='bfill')
unrate = unrate.fillna(method='ffill')
umcsent = umcsent.fillna(method='ffill')

# Calculate MACD, RSI, and ATR technical indicators
macd = ta.macd(sp500['Close'])
rsi = ta.rsi(sp500['Close'])
atr = ta.atr(sp500['High'], sp500['Low'], sp500['Close'], length=14)

# Merge all data into a single DataFrame, starting from the user-specified start date
data = pd.concat([
    sp500['Open'],
    sp500['Close'],
    macd['MACD_12_26_9'],
    rsi,
    atr,
    vix['Close'],
    usdx['Close'],
    effr,
    unrate,
    umcsent
], axis=1).loc[user_start_date:end_date]

# Rename columns
data.columns = [
    'Open', 'Close', 'MACD', 'RSI', 'ATR', 'VIX', 'USDX', 'EFFR', 'UNRATE', 'UMCSENT'
]

# Check for missing values and provide detailed feedback if found
if data.isnull().any().any():
    missing_info = data[data.isnull().any(axis=1)]
    missing_details = ", ".join([
        f"{column}: {list(missing_info.index[missing_info[column].isnull()])}"
        for column in missing_info.columns if missing_info[column].isnull().any()
    ])
    raise ValueError(f"Data contains missing values at index with details: {missing_details}")
else:
    data.to_csv('updated_sp500_data.csv')
