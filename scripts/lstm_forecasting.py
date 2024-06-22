import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM
import math
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Veri yükleme
file_path = '../data/Samsung Dataset.csv'
data = pd.read_csv(file_path)

# Tarih sütununu datetime formatına dönüştürme
data['Date'] = pd.to_datetime(data['Date'])
data.set_index('Date', inplace=True)

# Kapanış fiyatını seçme
closing_price = data['Close'].values.reshape(-1, 1)

# Verileri ölçeklendirme
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(closing_price)

# Eğitim ve test verilerini ayırma
train_size = int(len(scaled_data) * 0.8)
test_size = len(scaled_data) - train_size
train_data, test_data = scaled_data[0:train_size, :], scaled_data[train_size:len(scaled_data), :]

def create_dataset(dataset, time_step=1):
    dataX, dataY = [], []
    for i in range(len(dataset) - time_step - 1):
        a = dataset[i:(i + time_step), 0]
        dataX.append(a)
        dataY.append(dataset[i + time_step, 0])
    return np.array(dataX), np.array(dataY)

# Zaman adımı
time_step = 100

# Eğitim ve test verisetleri oluşturma
X_train, y_train = create_dataset(train_data, time_step)
X_test, y_test = create_dataset(test_data, time_step)

# Verileri LSTM girişine uygun hale getirme
X_train = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)
X_test = X_test.reshape(X_test.shape[0], X_test.shape[1], 1)

# LSTM modeli oluşturma
model = Sequential()
model.add(LSTM(50, return_sequences=True, input_shape=(time_step, 1)))
model.add(LSTM(50, return_sequences=False))
model.add(Dense(25))
model.add(Dense(1))

# Modeli derleme
model.compile(optimizer='adam', loss='mean_squared_error')

# Modeli eğitme
model.fit(X_train, y_train, validation_data=(X_test, y_test), batch_size=32, epochs=5)

# Tahminleri yapma
train_predict = model.predict(X_train)
test_predict = model.predict(X_test)

# Verileri ters ölçeklendirme
train_predict = scaler.inverse_transform(train_predict)
test_predict = scaler.inverse_transform(test_predict)
y_train = scaler.inverse_transform(y_train.reshape(-1, 1))
y_test = scaler.inverse_transform(y_test.reshape(-1, 1))

# RMSE hesaplama
train_rmse = math.sqrt(mean_squared_error(y_train, train_predict))
test_rmse = math.sqrt(mean_squared_error(y_test, test_predict))

# MAE hesaplama
train_mae = mean_absolute_error(y_train, train_predict)
test_mae = mean_absolute_error(y_test, test_predict)

# MAPE hesaplama
epsilon = 1e-10
train_mape = np.mean(np.abs((y_train - train_predict) / (y_train + epsilon))) * 100
test_mape = np.mean(np.abs((y_test - test_predict) / (y_test + epsilon))) * 100

# R² hesaplama
train_r2 = r2_score(y_train, train_predict)
test_r2 = r2_score(y_test, test_predict)

# Doğruluk (Accuracy) hesaplama
train_accuracy = np.mean(np.sign(y_train[1:] - y_train[:-1]) == np.sign(train_predict[1:] - train_predict[:-1]))
test_accuracy = np.mean(np.sign(y_test[1:] - y_test[:-1]) == np.sign(test_predict[1:] - test_predict[:-1]))

print(f'Train RMSE: {train_rmse}')
print(f'Test RMSE: {test_rmse}')
print(f'Train MAE: {train_mae}')
print(f'Test MAE: {test_mae}')
print(f'Train MAPE: {train_mape}')
print(f'Test MAPE: {test_mape}')
print(f'Train R²: {train_r2}')
print(f'Test R²: {test_r2}')
print(f'Train Accuracy: {train_accuracy}')
print(f'Test Accuracy: {test_accuracy}')

# Tahmin sonuçlarını görselleştirme
train_predict_plot = np.empty_like(scaled_data)
train_predict_plot[:, :] = np.nan
train_predict_plot[time_step:len(train_predict) + time_step, :] = train_predict

test_predict_plot = np.empty_like(scaled_data)
test_predict_plot[:, :] = np.nan
test_predict_plot[len(train_predict) + (time_step * 2) + 1:len(scaled_data) - 1, :] = test_predict

plt.figure(figsize=(14, 7))
plt.plot(scaler.inverse_transform(scaled_data), label='Gerçek Fiyat')
plt.plot(train_predict_plot, label='Eğitim Tahmini')
plt.plot(test_predict_plot, label='Test Tahmini')
plt.xlabel('Tarih')
plt.ylabel('Fiyat')
plt.title('Gerçek ve Tahmin Edilen Hisse Fiyatları')
plt.legend()
plt.grid(True)
plt.savefig('../results/lstm_predictions.png')
plt.show()

# Gelecek 30 gün için tahmin yapma
x_input = test_data[len(test_data) - time_step:].reshape(1, -1)
temp_input = list(x_input)
temp_input = temp_input[0].tolist()

lst_output = []
n_steps = time_step
i = 0
while (i < 30):
    if (len(temp_input) > time_step):
        x_input = np.array(temp_input[1:])
        x_input = x_input.reshape(1, -1)
        x_input = x_input.reshape((1, n_steps, 1))
        yhat = model.predict(x_input, verbose=0)
        temp_input.extend(yhat[0].tolist())
        temp_input = temp_input[1:]
        lst_output.extend(yhat.tolist())
        i = i + 1
    else:
        x_input = x_input.reshape((1, n_steps, 1))
        yhat = model.predict(x_input, verbose=0)
        temp_input.extend(yhat[0].tolist())
        lst_output.extend(yhat.tolist())
        i = i + 1

# Gelecek 30 günün tahmin edilen fiyatları
future_predictions = scaler.inverse_transform(lst_output)
print(f'Gelecek 30 günün tahmin edilen fiyatları:\n {future_predictions}')

# Gelecek tahminleri görselleştirme
last_date = data.index[-1]
future_dates = pd.date_range(last_date, periods=31, freq='B')[1:]

plt.figure(figsize=(14, 7))
plt.plot(data.index, scaler.inverse_transform(scaled_data), label='Gerçek Fiyat')
plt.plot(future_dates, future_predictions, label='Tahmin Edilen Gelecek Fiyat', linestyle='--')
plt.xlabel('Tarih')
plt.ylabel('Fiyat')
plt.title('Gelecek 30 Günün Tahmin Edilen Fiyatları')
plt.legend()
plt.grid(True)
plt.savefig('../results/future_predictions.png')
plt.show()

# Modelin performansı ile ilgili ek analizler
plt.figure(figsize=(14, 7))
plt.hist((y_test.flatten() - test_predict.flatten()), bins=50, color='gold', edgecolor='black')
plt.title('Hata Dağılımı (Test Verisi)')
plt.xlabel('Hata (Gerçek - Tahmin)')
plt.ylabel('Frekans')
plt.grid(True)
plt.savefig('../results/error_distribution.png')
plt.show()

# Trend analizleri
plt.figure(figsize=(14, 7))
plt.plot(future_dates, future_predictions, label='Tahmin Edilen Gelecek Fiyat', color='red')
plt.axhline(y=np.mean(future_predictions), color='blue', linestyle='--', label='Ortalama Tahmin')
plt.xlabel('Tarih')
plt.ylabel('Fiyat')
plt.title('Gelecek 30 Günün Trend Analizi')
plt.legend()
plt.grid(True)
plt.savefig('../results/future_trend_analysis.png')
plt.show()
