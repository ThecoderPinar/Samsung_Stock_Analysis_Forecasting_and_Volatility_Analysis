import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.seasonal import seasonal_decompose
from scipy.stats import zscore
from prophet import Prophet
from ruptures import Binseg

# Seaborn stil seçimi
sns.set(style="whitegrid")
sns.set_palette("muted")

# Veri yükleme
file_path = '../data/Samsung Dataset.csv'
data = pd.read_csv(file_path)

# Tarih sütununu datetime formatına dönüştürme
data['Date'] = pd.to_datetime(data['Date'])
data.set_index('Date', inplace=True)

# Frekans bilgisi ekleme ve eksik değerleri doldurma
data = data.asfreq('B')
data = data.fillna(method='ffill')

# 1. Eksik Değerlerin Tespiti
missing_values = data.isnull().sum()
print("Eksik Değerler:\n", missing_values)

# 2. Temel İstatistiklerin Hesaplanması
basic_statistics = data.describe()
print("Temel İstatistikler:\n", basic_statistics)

# 3. Korelasyon Matrisi
correlation_matrix = data.corr()
print("Korelasyon Matrisi:\n", correlation_matrix)

# 4. Aykırı Değerlerin Tespiti (Z-Score ile)
z_scores = zscore(data[['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']])
abs_z_scores = abs(z_scores)
outliers = (abs_z_scores > 3).any(axis=1)
data_outliers = data[outliers]
print("Aykırı Değerler:\n", data_outliers)

# 5. Zaman Serisi Grafikleri
plt.figure(figsize=(14, 7))
sns.lineplot(data=data, x=data.index, y='Close', label='Kapanış Fiyatı', color='gold')
sns.lineplot(data=data, x=data.index, y='Adj Close', label='Düzeltilmiş Kapanış Fiyatı', color='orange')
plt.xlabel('Tarih')
plt.ylabel('Fiyat')
plt.title('Zaman İçinde Kapanış ve Düzeltilmiş Kapanış Fiyatı')
plt.legend()
plt.grid(True)
plt.savefig('../results/close_adj_close.png')
plt.show()

# 6. Hareketli Ortalamalar (20 ve 100 Günlük)
data['MA20'] = data['Close'].rolling(window=20).mean()
data['MA100'] = data['Close'].rolling(window=100).mean()

plt.figure(figsize=(14, 7))
sns.lineplot(data=data, x=data.index, y='Close', label='Kapanış Fiyatı', color='gold')
sns.lineplot(data=data, x=data.index, y='MA20', label='20 Günlük Hareketli Ortalama', color='orange')
sns.lineplot(data=data, x=data.index, y='MA100', label='100 Günlük Hareketli Ortalama', color='red')
plt.xlabel('Tarih')
plt.ylabel('Fiyat')
plt.title('20 ve 100 Günlük Hareketli Ortalamalar ile Kapanış Fiyatı')
plt.legend()
plt.grid(True)
plt.savefig('../results/moving_averages.png')
plt.show()

# 7. Veriyi Son 2 Yıl ile Sınırlandırma
data_last_2_years = data[data.index >= '2022-01-01']

# 8. SARIMA Modeli Kurma ve Tahmin (Son 2 Yıl İçin)
model_last_2_years = SARIMAX(data_last_2_years['Close'], order=(1, 1, 1), seasonal_order=(1, 1, 0, 12))
model_fit_last_2_years = model_last_2_years.fit(disp=False)

forecast_last_2_years = model_fit_last_2_years.get_forecast(steps=30)
forecast_index_last_2_years = pd.date_range(start=data_last_2_years.index[-1], periods=30, freq='B')
forecast_series_last_2_years = pd.Series(forecast_last_2_years.predicted_mean, index=forecast_index_last_2_years)

# 9. Basit Hareketli Ortalama ile Tahmin
last_30_days_mean = data_last_2_years['Close'].iloc[-30:].mean()
forecast_simple_moving_average = [last_30_days_mean] * 30
forecast_index_simple_moving_average = pd.date_range(start=data_last_2_years.index[-1], periods=30, freq='B')
forecast_series_simple_moving_average = pd.Series(forecast_simple_moving_average, index=forecast_index_simple_moving_average)

# Tahmin verilerini DataFrame'e dönüştürme
forecast_df = pd.DataFrame({
    'Date': forecast_series_simple_moving_average.index,
    'Forecast': forecast_series_simple_moving_average.values
})

plt.figure(figsize=(14, 7))
sns.lineplot(data=data_last_2_years, x=data_last_2_years.index, y='Close', label='Kapanış Fiyatı (Son 2 Yıl)', color='gold')
sns.lineplot(data=forecast_df, x='Date', y='Forecast', label='Tahmin (Basit Hareketli Ortalama)', linestyle='--', color='red')
plt.xlabel('Tarih')
plt.ylabel('Fiyat')
plt.title('Kapanış Fiyatı ve Basit Hareketli Ortalama Tahmini')
plt.legend()
plt.grid(True)
plt.savefig('../results/simple_moving_average_forecast.png')
plt.show()

# 10. Mevsimsellik ve Trend Analizi
decomposition = seasonal_decompose(data['Close'], model='multiplicative', period=365)
fig = decomposition.plot()
fig.set_size_inches(14, 7)
plt.savefig('../results/seasonal_decomposition.png')
plt.show()

# 11. Günlük ve Aylık Getiri Hesaplamaları
data['Daily_Return'] = data['Close'].pct_change()
data['Monthly_Return'] = data['Close'].resample('ME').ffill().pct_change()

plt.figure(figsize=(14, 7))
sns.lineplot(data=data, x=data.index, y='Daily_Return', label='Günlük Getiri', color='gold')
plt.xlabel('Tarih')
plt.ylabel('Günlük Getiri')
plt.title('Zaman İçinde Günlük Getiriler')
plt.legend()
plt.grid(True)
plt.savefig('../results/daily_returns.png')
plt.show()

plt.figure(figsize=(14, 7))
data_monthly = data.resample('ME').last()
sns.lineplot(data=data_monthly, x=data_monthly.index, y='Monthly_Return', label='Aylık Getiri', color='gold')
plt.xlabel('Tarih')
plt.ylabel('Aylık Getiri')
plt.title('Zaman İçinde Aylık Getiriler')
plt.legend()
plt.grid(True)
plt.savefig('../results/monthly_returns.png')
plt.show()

# 12. Volatilite Analizi
data['Volatility'] = data['Daily_Return'].rolling(window=30).std()

plt.figure(figsize=(14, 7))
sns.lineplot(data=data, x=data.index, y='Volatility', label='30 Günlük Volatilite', color='gold')
plt.xlabel('Tarih')
plt.ylabel('Volatilite')
plt.title('Zaman İçinde 30 Günlük Volatilite')
plt.legend()
plt.grid(True)
plt.savefig('../results/volatility_analysis.png')
plt.show()

# 13. Aylık Ortalama Fiyat Analizi
data['Monthly_Avg'] = data['Close'].resample('ME').mean()

plt.figure(figsize=(14, 7))
sns.lineplot(data=data, x=data.index, y='Monthly_Avg', label='Aylık Ortalama Fiyat', color='gold')
plt.xlabel('Tarih')
plt.ylabel('Ortalama Fiyat')
plt.title('Zaman İçinde Aylık Ortalama Fiyat')
plt.legend()
plt.grid(True)
plt.savefig('../results/monthly_avg_price.png')
plt.show()

# 14. Yıllık Ortalama Fiyat Analizi
data['Yearly_Avg'] = data['Close'].resample('YE').mean()

plt.figure(figsize=(14, 7))
sns.lineplot(data=data, x=data.index, y='Yearly_Avg', label='Yıllık Ortalama Fiyat', color='gold')
plt.xlabel('Tarih')
plt.ylabel('Ortalama Fiyat')
plt.title('Zaman İçinde Yıllık Ortalama Fiyat')
plt.legend()
plt.grid(True)
plt.savefig('../results/yearly_avg_price.png')
plt.show()

# 15. İleri Düzey Tahmin: Prophet Kütüphanesi ile
# Model için tarih ve kapanış fiyatı sütunlarını Prophet formatına getirme
prophet_data = data[['Close']].reset_index()
prophet_data.columns = ['ds', 'y']

# Prophet modelini kurma ve tahmin
prophet_model = Prophet()
prophet_model.fit(prophet_data)

# Geleceğe yönelik tahminler oluşturma
future = prophet_model.make_future_dataframe(periods=365)
forecast = prophet_model.predict(future)

# Tahmin sonuçlarını görselleştirme
plt.figure(figsize=(14, 7))
prophet_model.plot(forecast)
plt.title('Prophet ile Tahmin')
plt.xlabel('Tarih')
plt.ylabel('Fiyat')
plt.savefig('../results/prophet_forecast.png')
plt.show()

# Prophet bileşen grafiği
plt.figure(figsize=(14, 7))
prophet_model.plot_components(forecast)
plt.title('Prophet Bileşen Grafiği')
plt.savefig('../results/prophet_components.png')
plt.show()

# 16. Trend Değişimi Analizi (Change Point Detection)
# Kapanış fiyatları üzerinde trend değişim noktalarını bulma
signal = data['Close'].values
algo = Binseg(model="l2").fit(signal)
result = algo.predict(n_bkps=10)

# Trend değişimlerini görselleştirme
plt.figure(figsize=(14, 7))
plt.plot(data.index, data['Close'], label='Kapanış Fiyatı', color='gold')
for bkpt in result[:-1]:  # Son nokta dışındaki değişim noktaları
    plt.axvline(x=data.index[bkpt], color='red', linestyle='--')
plt.xlabel('Tarih')
plt.ylabel('Fiyat')
plt.title('Trend Değişim Noktaları')
plt.legend()
plt.grid(True)
plt.savefig('../results/trend_change_points.png')
plt.show()

# 17. Hisse Senedi Fiyatlarının KDE (Kernel Density Estimation) Analizi
plt.figure(figsize=(14, 7))
sns.kdeplot(data=data['Close'], fill=True, color='gold')  # fill parametresi shade yerine kullanıldı
plt.xlabel('Fiyat')
plt.ylabel('Yoğunluk')
plt.title('Kapanış Fiyatlarının KDE Analizi')
plt.grid(True)
plt.savefig('../results/kde_analysis.png')
plt.show()

# 18. Hacim Verilerinin Zaman İçindeki Değişimi
plt.figure(figsize=(14, 7))
sns.lineplot(data=data, x=data.index, y='Volume', label='Hacim', color='gold')
plt.xlabel('Tarih')
plt.ylabel('Hacim')
plt.title('Hacim Verilerinin Zaman İçindeki Değişimi')
plt.legend()
plt.grid(True)
plt.savefig('../results/volume_over_time.png')
plt.show()

# 19. Hisse Senedi Fiyatları Arasındaki Korelasyon Matrisi
plt.figure(figsize=(14, 7))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', linewidths=0.5)
plt.title('Hisse Senedi Fiyatları Arasındaki Korelasyon Matrisi')
plt.savefig('../results/correlation_matrix.png')
plt.show()

# Sonuçlar
print("Temel İstatistikler:\n", basic_statistics)
print("Korelasyon Matrisi:\n", correlation_matrix)
print("Basit Hareketli Ortalama Tahminleri:\n", forecast_series_simple_moving_average.head())
