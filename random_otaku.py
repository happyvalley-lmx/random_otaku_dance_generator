import csv
import subprocess
import random

# 保存songlist(歌曲列表)
def save_to_txt(file_list, output_file):
    with open(output_file, 'w', encoding='UTF-8') as file:
        for item in file_list:
            file.write(f"file '{item}'\n")

# 拼接不同音频
def concatenate_audio(output_file):
    try:
        # 使用FFmpeg的命令行工具来拼接两个音频文件
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', 'songlist.txt',
            '-c', 'copy',
            output_file
        ]
        subprocess.run(cmd, check=True)
        
        print(f'音频文件已拼接并保存到 {output_file}')
    except Exception as e:
        print(f'拼接音频文件时出现错误: {str(e)}')

# 使用csv处理
def process_csv(csv_file):
    with open(csv_file, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # 跳过标题行
        song_list = []
        for row in reader:
            song_list.append("output/out_"+row[0])
    return song_list

csv_file = "songs.csv"  # 输入CSV文件名
song_list = process_csv(csv_file)
random.shuffle(song_list)

# 使用示例：
slst_file = "songlist.txt"
save_to_txt(song_list, slst_file)

output_file = 'output_audio.mp3'
concatenate_audio(output_file)
print(f"已根据乐曲csv表格随机打乱顺序，合并生成随舞文件为: {output_file}")