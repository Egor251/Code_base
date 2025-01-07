import librosa
import numpy as np
import soundfile as sf  # Для сохранения аудиофайлов
import matplotlib.pyplot as plt


def normalize_audio(file_path):
    audio_data, sample_rate = librosa.load(file_path, sr=None)  # sr=None сохраняет оригинальную частоту дискретизации

    print(f'Частота дискретизации: {sample_rate} Гц')
    print(f'Длина аудиоданных: {len(audio_data)} сэмплов')

    # Обработка: Нормализация аудиосигнала
    normalized_audio = audio_data / np.max(np.abs(audio_data))  # Нормализация в диапазоне [-1, 1]

    # Сохранение измененного аудиофайла
    output_file_path = 'output.wav'
    sf.write(output_file_path, normalized_audio, sample_rate)

    print(f'Измененный файл сохранен как {output_file_path}')


def plot_audio_data(file_path):
    audio_data, sample_rate = librosa.load(file_path, sr=None)  # sr=None сохраняет оригинальную частоту дискретизации

    # Построение графика по массиву audio_data
    plt.figure(figsize=(10, 4))
    plt.plot(audio_data)
    plt.title('Аудио данные')
    plt.xlabel('Сэмплы')
    plt.ylabel('Амплитуда')
    plt.grid(True)
    plt.show()


if __name__ == '__main__':
    file_path = 'sample-15s.wav'  # Путь к вашему WAV-файлу

    normalize_audio(file_path)
