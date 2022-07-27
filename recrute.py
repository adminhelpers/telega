import os

if __name__ == '__main__':
    files = ["time_rise.py", "main.py"]  # файлы, которые нужно запустить
    for file in files:
        os.system(f'python {file}')
