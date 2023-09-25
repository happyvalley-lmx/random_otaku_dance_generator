import ffmpeg
import csv
import subprocess

# 拼接不同音频
def concatenate_audio(input_file1, input_file2, output_file):
    try:
        # 使用FFmpeg的命令行工具来拼接两个音频文件
        cmd = [
            'ffmpeg',
            '-i', input_file1,
            '-i', input_file2,
            '-filter_complex', f'[0:a][1:a]concat=n=2:v=0:a=1[outa]',
            '-map', '[outa]',
            '-b:a', '320k',
            # '-c', 'copy',
            output_file
        ]
        subprocess.run(cmd, check=True)
        
        print(f'音频文件已拼接并保存到 {output_file}')
    except Exception as e:
        print(f'拼接音频文件时出现错误: {str(e)}')

# 裁剪乐曲
def cut_song(input_file, output_file, start_time, end_time):
    try:
        ffmpeg.input(input_file, ss=start_time, to=end_time).output(output_file, acodec="copy").run(overwrite_output=True)
        print(f"剪切成功：{output_file}")
    except ffmpeg.Error as e:
        print(f"剪切失败：{str(e)}")

# 添加开头两秒淡入
def add_fade_in_effects(input_file, output_file):
    try:
        # 添加开头的淡入效果（持续2秒）
        ffmpeg.input(input_file).filter("afade", t="in", st=0, d=2).output(output_file, audio_bitrate=327680).run(overwrite_output=True)
        print(f"添加淡入淡出效果成功：{output_file}")
    except ffmpeg.Error as e:
        print(f"添加淡入淡出效果失败：{str(e)}")
        
def add_fade_out_effects(input_file, output_file, end_time):
    try:
        # 添加结尾淡出效果（持续3秒）
        ffmpeg.input(input_file).filter("afade", t="out", st=int(end_time)-3, d=3).output(output_file, audio_bitrate=327680).run(overwrite_output=True)
        print(f"添加淡入淡出效果成功：{output_file}")
    except ffmpeg.Error as e:
        print(f"添加淡入淡出效果失败：{str(e)}")

# 剪切、增加米库开头倒数并淡入淡出文件函数
def cut_and_fade(input_file_raw, output_file, start_time, end_time):
    input_file = f"songs/{input_file_raw}"
    temp_file = f"cache/temp_{input_file_raw}.mp3"
    cut_song(input_file, temp_file, start_time, end_time)

    temp_nomiku_in = f"cache/temp_nomiku_in_{input_file_raw}"
    add_fade_in_effects(temp_file, temp_nomiku_in)
    temp_nomiku_out = f"cache/temp_nomiku_out_{input_file_raw}"
    add_fade_out_effects(temp_nomiku_in, temp_nomiku_out, end_time-start_time)

    concatenate_audio("songs/mix.mp3", temp_nomiku_out, output_file)
    

# 使用csv处理
def process_csv(csv_file, output_dir, fade_duration=2):
    with open(csv_file, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # 跳过标题行
        for row in reader:
            song_file = row[0]  # 歌曲文件名
            start_time = float(row[1])  # 开始时间（秒）
            end_time = float(row[2])  # 结束时间（秒）
            
            # 构建输出文件路径
            output_file = f"{output_dir}/out_{song_file}"
            
            # 调用剪切和淡入函数
            cut_and_fade(song_file, output_file, start_time, end_time)

csv_file = "songs.csv"  # 输入CSV文件名
output_directory = "output"  # 输出文件目录
fade_duration = 2  # 淡入持续时间（秒）

process_csv(csv_file, output_directory, fade_duration)
