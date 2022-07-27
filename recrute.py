import subprocess


if __name__ == '__main__':
    files = ["time_rise.py", "main.py"]  # файлы, которые нужно запустить
    for file in files:
        subprocess.Popen(args=["start", "python", file], shell=True, stdout=subprocess.PIPE)