import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.seasonal import seasonal_decompose
from sklearn.linear_model import LinearRegression
import numpy as np

# Seaborn stil seçimi
sns.set(style="whitegrid")
sns.set_palette("muted")

# Veri yükleme
file_path = '../data/Samsung Dataset.csv'
data = pd.read_csv(file_path)

# Tarih sütununu datetime formatına dönüştürme
data['Date'] = pd.to_datetime(data['Date'])
data.set_index('Date', inplace=True)

# 1. Veri Yükleme ve Hazırlık
data = data.asfreq('B')  # İş günlerine göre frekans ayarlama
data['Volume'] = data['Volume'].ffill()  # Hacim verilerindeki eksik değerleri ileri doldurma

# 2. Tarihsel Eğilimlerin Belirlenmesi
data['Volume_MA30'] = data['Volume'].rolling(window=30).mean()

plt.figure(figsize=(14, 7))
sns.lineplot(data=data, x=data.index, y='Volume', label='Hacim', color='blue')
sns.lineplot(data=data, x=data.index, y='Volume_MA30', label='30 Günlük Hareketli Ortalama', color='orange')
plt.xlabel('Tarih')
plt.ylabel('Hacim')
plt.title('Hacim ve 30 Günlük Hareketli Ortalama')
plt.legend()
plt.savefig('./volume_ma30.png')
plt.show()

# 3. Hacim Tahminleri (2024-2031)

# Lineer Regresyon ile Tahmin
data['Year'] = data.index.year
yearly_volume = data.groupby('Year')['Volume'].sum().reset_index()

X = yearly_volume[['Year']]
y = yearly_volume['Volume']

model = LinearRegression()
model.fit(X, y)

# 2024-2031 yılları için tahmin yapma
future_years = pd.DataFrame({'Year': np.arange(2024, 2032)})
future_volumes = model.predict(future_years)

# Sonuçları görselleştirme
plt.figure(figsize=(14, 7))
sns.lineplot(data=yearly_volume, x='Year', y='Volume', label='Gerçek Hacim', color='blue')
sns.lineplot(data=future_years, x='Year', y=future_volumes, label='Tahmin Edilen Hacim', linestyle='--', color='red')
plt.xlabel('Yıl')
plt.ylabel('Toplam Hacim')
plt.title('2024-2031 Yılları Arası Tahmin Edilen Toplam Hacim')
plt.legend()
plt.savefig('./linear_regression_forecast.png')
plt.show()

# Tahmin sonuçları
future_years['Tahmin Edilen Hacim'] = future_volumes
print(future_years)

# 4. ARIMA Modeli ile Hacim Tahmini
# ARIMA modeli kurma ve tahmin (son 2 yıl için)
model_arima = SARIMAX(data['Volume'], order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
model_fit_arima = model_arima.fit(disp=False)

# 2024-2031 yılları için tahmin yapma
forecast_arima = model_fit_arima.get_forecast(steps=8*12)
forecast_index_arima = pd.date_range(start=data.index[-1], periods=8*12, freq='ME')
forecast_series_arima = pd.Series(forecast_arima.predicted_mean, index=forecast_index_arima)
forecast_arima_df = forecast_series_arima.reset_index()
forecast_arima_df.columns = ['Date', 'Forecast']

# Sonuçları görselleştirme
plt.figure(figsize=(14, 7))
sns.lineplot(data=data, x=data.index, y='Volume', label='Gerçek Hacim', color='blue')
sns.lineplot(data=forecast_arima_df, x='Date', y='Forecast', label='ARIMA Tahmini', linestyle='--', color='red')
plt.xlabel('Tarih')
plt.ylabel('Toplam Hacim')
plt.title('2024-2031 Yılları Arası ARIMA ile Tahmin Edilen Toplam Hacim')
plt.legend()
plt.savefig('./arima_forecast.png')
plt.show()

# 5. Mevsimsellik ve Trend Analizi
# Additif model kullanarak mevsimsel decompose işlemi
decomposition = seasonal_decompose(data['Volume'], model='additive', period=365)
fig = decomposition.plot()
fig.set_size_inches(14, 7)
plt.savefig('./seasonal_trend_decomposition.png')
plt.show()

# 6. Günlük ve Aylık Getiri Hesaplamaları
data['Daily_Return'] = data['Volume'].pct_change()
data['Monthly_Return'] = data['Volume'].resample('ME').ffill().pct_change()

plt.figure(figsize=(14, 7))
sns.lineplot(data=data, x=data.index, y='Daily_Return', label='Günlük Getiri', color='blue')
plt.xlabel('Tarih')
plt.ylabel('Günlük Getiri')
plt.title('Zaman İçinde Günlük Getiriler')
plt.legend()
plt.savefig('./daily_returns.png')
plt.show()

plt.figure(figsize=(14, 7))
data_monthly = data.resample('ME').last()
sns.lineplot(data=data_monthly, x=data_monthly.index, y='Monthly_Return', label='Aylık Getiri', color='blue')
plt.xlabel('Tarih')
plt.ylabel('Aylık Getiri')
plt.title('Zaman İçinde Aylık Getiriler')
plt.legend()
plt.savefig('./monthly_returns.png')
plt.show()

# 7. Volatilite Analizi
data['Volatility'] = data['Daily_Return'].rolling(window=30).std()

plt.figure(figsize=(14, 7))
sns.lineplot(data=data, x=data.index, y='Volatility', label='30 Günlük Volatilite', color='blue')
plt.xlabel('Tarih')
plt.ylabel('Volatilite')
plt.title('Zaman İçinde 30 Günlük Volatilite')
plt.legend()
plt.savefig('./volatility_analysis.png')
plt.show()
