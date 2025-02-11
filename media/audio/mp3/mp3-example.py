from pydub import AudioSegment

# Загрузка MP3-файла
file_path = 'City Ruins.mp3'  # Путь к вашему MP3-файлу
audio = AudioSegment.from_mp3(file_path)
print(audio)
# Изменение громкости (например, увеличение на 5 дБ)
louder_audio = audio + 5  # Увеличение громкости на 5 дБ

# Применение эффекта увеличения скорости (ускорение на 1.5 раза)
sped_up_audio = audio.speedup(playback_speed=1.5)

# Сохранение измененного аудиофайла
output_file_path = 'output.mp3'
louder_audio.export(output_file_path, format='mp3')  # Можно экспортировать и в другие форматы

print(f'Измененный файл сохранен как {output_file_path}')
