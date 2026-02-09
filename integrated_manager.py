import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import os
import threading
import ffmpeg
import random
import time
import shutil
import pygame
from mutagen import File as MutagenFile

class OtakuDanceGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("乐谷的随舞音频生成器 可视化版 (2026020902)")
        self.root.geometry("1200x750")

        # 确保基础目录存在
        if not os.path.exists("songs"):
            os.makedirs("songs")
        if not os.path.exists("output"):
            os.makedirs("output")
        if not os.path.exists("cache"):
            os.makedirs("cache")

        # 数据存储
        self.song_data = []

        # 创建界面
        self.create_widgets()

        # 加载默认CSV文件
        if os.path.exists("songs.csv"):
            self.load_csv("songs.csv")

    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # 左侧控制面板
        left_frame = ttk.LabelFrame(main_frame, text="歌曲管理", padding="10")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))

        # 表格
        columns = ('文件名', '开始时间', '结束时间', '备注')
        self.tree = ttk.Treeview(left_frame, columns=columns, show='headings', height=15)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=80)

        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # 按钮框架
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))

        ttk.Button(button_frame, text="添加曲目", command=self.add_song).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="删除曲目", command=self.delete_song).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="编辑曲目", command=self.edit_song).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="加载工程(CSV)", command=self.load_csv_dialog).grid(row=0, column=3, padx=5)
        ttk.Button(button_frame, text="保存工程(CSV)", command=self.save_csv_dialog).grid(row=0, column=4, padx=5)

        # 总时长显示标签
        self.duration_label = ttk.Label(left_frame, text="")
        self.duration_label.grid(row=2, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))

        # 右侧控制面板
        right_frame = ttk.LabelFrame(main_frame, text="操作", padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Button(right_frame, text="生成音频", command=self.generate_audio).grid(row=0, column=0, pady=10, sticky=(tk.W, tk.E))

        self.progress_text = tk.Text(right_frame, height=25, width=60)
        self.progress_text.grid(row=1, column=0, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))

        progress_scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.progress_text.yview)
        self.progress_text.configure(yscrollcommand=progress_scrollbar.set)
        progress_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))

        self.progress_bar = ttk.Progressbar(right_frame, mode='determinate', length=400)
        self.progress_bar.grid(row=2, column=0, columnspan=2, pady=5, sticky=(tk.W, tk.E))

        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)

    # --- 线程安全的 UI 更新辅助函数 ---
    def log_progress(self, message):
        """线程安全地向文本框写入日志"""
        def _update():
            self.progress_text.insert(tk.END, message)
            self.progress_text.see(tk.END)
        self.root.after(0, _update)

    def update_progress_bar(self, value):
        """线程安全地更新进度条"""
        self.root.after(0, lambda: self.progress_bar.configure(value=value))

    def load_csv(self, filename):
        try:
            self.song_data = []
            self.tree.delete(*self.tree.get_children())
            
            # 增加 utf-8-sig 支持（兼容 Excel 保存的 CSV）
            encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312']
            data_read = False

            for encoding in encodings:
                try:
                    with open(filename, 'r', encoding=encoding, newline='') as file:
                        reader = csv.reader(file)
                        headers = next(reader, None) # 跳过标题
                        for row in reader:
                            if row: # 避免空行
                                self.song_data.append(row)
                                self.tree.insert('', 'end', values=row)
                    data_read = True
                    break
                except UnicodeDecodeError:
                    continue
                except Exception:
                    continue

            if not data_read:
                raise Exception("无法识别文件编码")

            self.update_duration_display()  # 更新总时长显示

        except FileNotFoundError:
            messagebox.showwarning("警告", f"文件 {filename} 不存在，将创建新文件。")
        except Exception as e:
            messagebox.showerror("错误", f"加载CSV文件时出错: {str(e)}")

    def load_csv_dialog(self):
        filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if filename:
            self.load_csv(filename)

    def save_csv_dialog(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if filename:
            self.save_csv(filename)

    def save_csv(self, filename):
        try:
            with open(filename, 'w', encoding='utf-8-sig', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['文件名', '开始时间', '结束时间', '备注'])
                for row in self.song_data:
                    writer.writerow(row)
            messagebox.showinfo("成功", f"文件已保存至 {filename}")
        except Exception as e:
            messagebox.showerror("错误", f"保存出错: {str(e)}")

    def get_mix_duration(self):
        """获取mix.mp3的时长"""
        mix_path = "songs/mix.mp3"
        if os.path.exists(mix_path):
            try:
                audio = MutagenFile(mix_path)
                if audio and audio.info:
                    return audio.info.length
            except Exception:
                pass
            try:
                import pygame
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                sound = pygame.mixer.Sound(mix_path)
                return sound.get_length()
            except Exception:
                pass
        return 0  # 如果没有mix.mp3，则时长为0

    def calculate_single_song_duration(self, start_time_str, end_time_str):
        """计算单首歌曲的时长（结束时间-开始时间）"""
        try:
            start_time = float(start_time_str)
            end_time = float(end_time_str)
            return max(0, end_time - start_time)  # 确保时长不为负数
        except ValueError:
            return 0

    def calculate_total_duration(self):
        """计算总时长：(乐曲数量*(单曲平均时长+mix.mp3的时长))"""
        if not self.song_data:
            return 0
        
        # 计算所有歌曲的总时长
        total_song_duration = 0
        for row in self.song_data:
            if len(row) >= 3:  # 确保有足够的列
                start_time = row[1]
                end_time = row[2]
                single_duration = self.calculate_single_song_duration(start_time, end_time)
                total_song_duration += single_duration
        
        # 计算平均单曲时长
        avg_song_duration = total_song_duration / len(self.song_data) if self.song_data else 0
        
        # 获取mix.mp3的时长
        mix_duration = self.get_mix_duration()
        
        # 总时长 = 歌曲数量 * (平均单曲时长 + mix.mp3时长)
        total_duration = len(self.song_data) * (avg_song_duration + mix_duration)
        
        return total_duration

    def update_duration_display(self):
        """更新总时长显示"""
        total_duration = self.calculate_total_duration()
        hours = int(total_duration // 3600)
        minutes = int((total_duration % 3600) // 60)
        seconds = int(total_duration % 60)
        duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        song_count = len(self.song_data)
        self.duration_label.config(text=f"当前曲目数: {song_count}  /  总时长: {duration_str}")

    def add_song(self):
        dialog = SongDialog(self.root, "添加曲目", use_file_dialog=True)
        if dialog.result:
            self.song_data.append(dialog.result)
            self.tree.insert('', 'end', values=dialog.result)
            self.update_duration_display()  # 更新总时长显示

    def delete_song(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请选择要删除的曲目")
            return
        for item in selected_items:
            index = self.tree.index(item)
            self.tree.delete(item)
            del self.song_data[index]
        self.update_duration_display()  # 更新总时长显示

    def edit_song(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请选择要编辑的曲目")
            return
        item = selected_items[0]
        values = self.tree.item(item, 'values')
        dialog = SongDialog(self.root, "编辑曲目", values)
        if dialog.result:
            self.tree.item(item, values=dialog.result)
            index = self.tree.index(item)
            self.song_data[index] = dialog.result
            self.update_duration_display()  # 更新总时长显示

    def generate_audio(self):
        self.save_csv("songs.csv")
        thread = threading.Thread(target=self._generate_audio_internal)
        thread.daemon = True
        thread.start()

    def _generate_audio_internal(self):
        try:
            # 清空进度文本
            self.root.after(0, lambda: self.progress_text.delete(1.0, tk.END))

            csv_file = "songs.csv"
            output_directory = "output"
            fade_duration = 2

            with open(csv_file, newline='', encoding='utf-8-sig') as csvfile:
                reader = csv.reader(csvfile)
                next(reader, None)
                rows = list(reader)
                song_count = len(rows)

            self.total_songs = song_count
            self.current_song = 0
            self.root.after(0, lambda: self.progress_bar.configure(maximum=song_count))

            self.log_progress(">>> 开始处理音频...\n")
            
            # 第一步：裁剪处理
            for i, row in enumerate(rows):
                if not row: continue
                song_file = row[0]
                try:
                    start_time = float(row[1])
                    end_time = float(row[2])
                except ValueError:
                    self.log_progress(f"警告：歌曲 {song_file} 时间格式错误，跳过。\n")
                    continue
                
                output_file = f"{output_directory}/out_{song_file}"
                self.cut_and_fade(song_file, output_file, start_time, end_time)

                self.current_song += 1
                self.update_progress_bar(self.current_song)
                self.log_progress(f"进度: {self.current_song}/{self.total_songs} - 完成 {song_file}\n")

            # 第二步：随机化列表
            self.log_progress(">>> 正在随机化播放列表...\n")
            song_files = [f"output/out_{row[0]}" for row in rows if os.path.exists(f"output/out_{row[0]}")]
            random.shuffle(song_files)

            # 第三步：生成列表文件
            self.save_to_txt(song_files, "songlist.txt")

            # 第四步：拼接
            final_output = f'output_audio_{int(time.time())}.mp3'
            self.log_progress(">>> 开始最终拼接...\n")
            self.concatenate_audio_from_list(final_output)

            self.log_progress(f"*** 全部完成！文件已保存为: {final_output} ***\n")
            self.root.after(0, lambda: messagebox.showinfo("完成", "随舞音频生成完成~"))

        except Exception as e:
            self.log_progress(f"\n!!! 严重错误: {str(e)}\n")

    def cut_song(self, input_file, output_file, start_time, end_time):
        try:
            # 修正：duration 应该是 end - start
            duration = end_time - start_time
            if duration <= 0:
                raise ValueError("结束时间必须大于开始时间")
            
            (
                ffmpeg
                .input(input_file, ss=start_time, t=duration)
                .output(output_file, acodec="copy")
                .run(overwrite_output=True, quiet=True)
            )
            # self.log_progress(f"剪切成功：{output_file}\n") # 日志太长可注释
        except ffmpeg.Error as e:
            self.log_progress(f"剪切失败 [{input_file}]: {e.stderr.decode() if e.stderr else str(e)}\n")
            raise

    def add_fade_in_effects(self, input_file, output_file):
        try:
            (
                ffmpeg
                .input(input_file)
                .filter("afade", t="in", st=0, d=2)
                .output(output_file, audio_bitrate='320k')
                .run(overwrite_output=True, quiet=True)
            )
        except ffmpeg.Error as e:
            self.log_progress(f"淡入失败: {str(e)}\n")

    def add_fade_out_effects(self, input_file, output_file, duration):
        try:
            # 确保淡出开始时间不为负
            fade_out_start = max(0, duration - 3)
            (
                ffmpeg
                .input(input_file)
                .filter("afade", t="out", st=fade_out_start, d=3)
                .output(output_file, audio_bitrate='320k')
                .run(overwrite_output=True, quiet=True)
            )
        except ffmpeg.Error as e:
            self.log_progress(f"淡出失败: {str(e)}\n")

    def cut_and_fade(self, input_file_raw, output_file, start_time, end_time):
        input_path = f"songs/{input_file_raw}"
        mix_path = "songs/mix.mp3" # 确保你的文件夹里有这个文件

        if not os.path.exists(input_path):
             self.log_progress(f"错误：找不到文件 {input_path}\n")
             return

        # 定义临时文件路径
        temp_cut = f"cache/temp_cut_{input_file_raw}"
        temp_fade_in = f"cache/temp_in_{input_file_raw}"
        # 这是一个新变量：代表"处理完淡入淡出，但还没加mix"的纯歌曲片段
        temp_song_ready = f"cache/temp_ready_{input_file_raw}" 
        
        # 1. 剪切
        self.cut_song(input_path, temp_cut, start_time, end_time)
        
        # 2. 淡入
        self.add_fade_in_effects(temp_cut, temp_fade_in)
        
        # 3. 淡出 (注意：这里输出到 temp_song_ready，而不是最终文件)
        duration = end_time - start_time
        self.add_fade_out_effects(temp_fade_in, temp_song_ready, duration)
        
        # 4. 拼接 mix.mp3 + 歌曲片段
        if os.path.exists(mix_path):
            # 如果存在 mix.mp3，则拼接：mix在前，歌曲在后
            self.concatenate_audio_2(mix_path, temp_song_ready, output_file)
        else:
            # 如果找不到 mix.mp3，就直接把处理好的歌曲作为输出（防止程序崩溃）
            self.log_progress(f"提示：未找到 {mix_path}，将跳过过渡音效直接输出。\n")
            shutil.copy(temp_song_ready, output_file)

    def concatenate_audio_2(self, f1, f2, out):
        try:
            in1 = ffmpeg.input(f1)
            in2 = ffmpeg.input(f2)
            ffmpeg.concat(in1, in2, v=0, a=1).output(out, ac=2).run(overwrite_output=True, quiet=True)
        except Exception as e:
            self.log_progress(f"拼接失败: {e}\n")

    def save_to_txt(self, file_list, output_file):
        # 转换为绝对路径防止 ffmpeg 找不到
        abs_list = [os.path.abspath(f) for f in file_list]
        with open(output_file, 'w', encoding='UTF-8') as file:
            for item in abs_list:
                # ffmpeg concat protocol 格式要求
                file.write(f"file '{item.replace(os.sep, '/')}'\n")

    def concatenate_audio_from_list(self, output_file):
        try:
            (
                ffmpeg
                .input('songlist.txt', f='concat', safe=0)
                .output(output_file, c='copy')
                .run(overwrite_output=True, quiet=True)
            )
        except Exception as e:
            self.log_progress(f"最终拼接失败: {str(e)}\n")

class SongDialog:
    def __init__(self, parent, title, initial_values=None, use_file_dialog=False):
        self.parent = parent
        self.result = None
        self.use_file_dialog = use_file_dialog
        self.is_playing = False
        self.current_pos = 0.0
        self.audio_length = 0
        self.stop_thread_flag = False
        self.play_start_time = 0
        self.track_start_pos = 0

        # 初始化 mixer
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("650x500") #稍微加宽一点以容纳按钮
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 居中
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))

        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Row 0: 文件名 ---
        ttk.Label(main_frame, text="文件名:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.filename_var = tk.StringVar()
        self.filename_entry = ttk.Entry(main_frame, textvariable=self.filename_var, width=35)
        self.filename_entry.grid(row=0, column=1, pady=5, padx=5)

        if use_file_dialog:
            ttk.Button(main_frame, text="浏览", command=self.browse_file).grid(row=0, column=2, padx=5)

        # --- Row 1: 开始时间 (带跳转) ---
        ttk.Label(main_frame, text="开始时间:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.start_time_var = tk.StringVar(value="0:00")
        self.start_time_entry = ttk.Entry(main_frame, textvariable=self.start_time_var, width=35)
        self.start_time_entry.grid(row=1, column=1, pady=5, padx=5)
        # 跳转按钮
        ttk.Button(main_frame, text="跳转", command=lambda: self.jump_to_entry(self.start_time_var)).grid(row=1, column=2, padx=5)

        # --- Row 2: 结束时间 (带跳转) ---
        ttk.Label(main_frame, text="结束时间:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.end_time_var = tk.StringVar(value="0:00")
        self.end_time_entry = ttk.Entry(main_frame, textvariable=self.end_time_var, width=35)
        self.end_time_entry.grid(row=2, column=1, pady=5, padx=5)
        # 跳转按钮
        ttk.Button(main_frame, text="跳转", command=lambda: self.jump_to_entry(self.end_time_var)).grid(row=2, column=2, padx=5)

        # --- Row 3: 备注 ---
        ttk.Label(main_frame, text="备注:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.comment_var = tk.StringVar()
        self.comment_entry = ttk.Entry(main_frame, textvariable=self.comment_var, width=35)
        self.comment_entry.grid(row=3, column=1, pady=5, padx=5)
        
        # 预览片段按钮
        ttk.Button(main_frame, text="预览片段", command=self.preview_segment).grid(row=3, column=2, padx=5, pady=5)

        # --- Row 4: 音频预览区域 ---
        preview_frame = ttk.LabelFrame(main_frame, text="音频预览", padding="10")
        preview_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)

        self.time_label = ttk.Label(preview_frame, text="00:00 / 00:00")
        self.time_label.grid(row=0, column=0, columnspan=4, pady=5)

        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_scale = ttk.Scale(preview_frame, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.progress_var)
        self.progress_scale.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        self.progress_scale.state(['disabled'])

        self.progress_scale.bind("<ButtonRelease-1>", self.on_slider_release)

        # 控制按钮
        self.play_button = ttk.Button(preview_frame, text="播放", command=self.toggle_playback)
        self.play_button.grid(row=2, column=0, padx=5, pady=5)

        ttk.Button(preview_frame, text="设为开始时间", command=self.set_start_time).grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(preview_frame, text="设为结束时间", command=self.set_end_time).grid(row=2, column=2, padx=5, pady=5)
        
        # 副歌提取按钮
        ttk.Button(preview_frame, text="提取副歌", command=self.extract_chorus).grid(row=2, column=3, padx=5, pady=5)

        # --- Row 5: 底部按钮 ---
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=5, column=0, columnspan=3, pady=20)
        ttk.Button(btn_frame, text="确定", command=self.ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.cancel).pack(side=tk.LEFT, padx=5)

        # 初始化数据
        if initial_values:
            self.filename_var.set(initial_values[0])
            # 这里的 initial_values[1] 是秒数 (例如 "75.5")，我们需要转成 "1:15.50"
            self.start_time_var.set(self.sec_to_mmss(initial_values[1]))
            self.end_time_var.set(self.sec_to_mmss(initial_values[2]))
            self.comment_var.set(initial_values[3])
            
            if initial_values[0]:
                self.load_audio(f"songs/{initial_values[0]}")

        self.filename_var.trace_add("write", lambda *args: self.load_audio(f"songs/{self.filename_var.get().strip()}"))
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.parent.wait_window(self.dialog)

    # --- 辅助工具：时间转换 ---
    def sec_to_mmss(self, seconds_str):
        """将秒数(字符串或浮点)转换为 MM:SS.ss 格式"""
        try:
            total_sec = float(seconds_str)
            m = int(total_sec // 60)
            s = total_sec % 60
            # 如果有小数部分，保留两位小数，否则只显示整数
            if s % 1 == 0:
                return f"{m}:{int(s):02d}"
            else:
                return f"{m}:{s:05.2f}"
        except ValueError:
            return "0:00"

    def mmss_to_sec(self, mmss_str):
        """将 MM:SS 格式或纯数字转换为秒数(浮点)"""
        mmss_str = mmss_str.strip()
        if not mmss_str:
            return 0.0
        try:
            if ":" in mmss_str:
                parts = mmss_str.split(":")
                if len(parts) == 2:
                    return float(parts[0]) * 60 + float(parts[1])
                elif len(parts) == 3: # HH:MM:SS
                    return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
            else:
                return float(mmss_str)
        except ValueError:
            return 0.0
        return 0.0

    # --- 新增：跳转逻辑 ---
    def jump_to_entry(self, entry_var):
        """获取输入框的时间并跳转播放"""
        time_str = entry_var.get()
        target_sec = self.mmss_to_sec(time_str)
        
        if target_sec > self.audio_length:
            target_sec = self.audio_length
            
        self.current_pos = target_sec
        self.progress_var.set(target_sec)
        self.update_time_label()
        
        # 如果当前正在播放，则立即跳转播放；如果暂停，只更新进度条不自动播放
        if self.is_playing:
            self.restart_playback(target_sec)
        else:
            # 停止当前可能存在的任何播放，准备从新位置开始
            pygame.mixer.music.stop()
            # 为了让用户确认跳转成功，可以加载并暂停在那个位置，
            # 但 pygame 不支持 seek 暂停。所以我们只更新界面变量，等用户点播放。
            pass

    def load_audio(self, filepath):
        if os.path.exists(filepath):
            try:
                pygame.mixer.music.load(filepath)
                self.audio_length = 0
                try:
                    audio = MutagenFile(filepath)
                    if audio and audio.info:
                        self.audio_length = audio.info.length
                except: pass
                
                if self.audio_length == 0:
                    try:
                        sound = pygame.mixer.Sound(filepath)
                        self.audio_length = sound.get_length()
                    except: pass
                
                if self.audio_length == 0: self.audio_length = 120

                self.progress_scale.configure(to=self.audio_length)
                self.progress_scale.state(['!disabled'])
                self.update_time_label()
                
            except Exception as e:
                print(f"Load error: {e}")
                self.progress_scale.state(['disabled'])
        else:
            self.progress_scale.state(['disabled'])

    def on_slider_release(self, event):
        if self.audio_length > 0:
            pos = self.progress_scale.get()
            self.current_pos = pos
            self.update_time_label()
            if self.is_playing:
                self.restart_playback(pos)

    def restart_playback(self, start_pos):
        filename = self.filename_var.get().strip()
        filepath = f"songs/{filename}"
        if os.path.exists(filepath):
            pygame.mixer.music.stop()
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play(start=start_pos)
            self.play_start_time = time.time()
            self.track_start_pos = start_pos
            
            # 确保线程正在运行
            if not self.is_playing:
                self.is_playing = True
                self.play_button.config(text="暂停")
                self.stop_thread_flag = False
                threading.Thread(target=self.update_progress, daemon=True).start()

    def toggle_playback(self):
        filepath = f"songs/{self.filename_var.get().strip()}"
        if not os.path.exists(filepath): return

        if not self.is_playing:
            try:
                pygame.mixer.music.load(filepath)
                pygame.mixer.music.play(start=self.current_pos)
                self.is_playing = True
                self.play_button.config(text="暂停")
                self.play_start_time = time.time()
                self.track_start_pos = self.current_pos
                self.stop_thread_flag = False
                threading.Thread(target=self.update_progress, daemon=True).start()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        else:
            self.stop_audio()

    def update_progress(self):
        while self.is_playing and not self.stop_thread_flag:
            if not pygame.mixer.music.get_busy(): break
            elapsed = time.time() - self.play_start_time
            current = self.track_start_pos + elapsed
            if current > self.audio_length: current = self.audio_length
            self.current_pos = current
            self.progress_var.set(current)
            self.update_time_label()
            time.sleep(0.1)
        if self.is_playing:
            self.is_playing = False
            try: self.play_button.config(text="播放")
            except: pass

    def stop_audio(self):
        self.stop_thread_flag = True
        pygame.mixer.music.stop()
        self.is_playing = False
        self.play_button.config(text="播放")

    def update_time_label(self):
        c_min, c_sec = divmod(int(self.current_pos), 60)
        t_min, t_sec = divmod(int(self.audio_length), 60)
        self.time_label.config(text=f"{c_min:02d}:{c_sec:02d} / {t_min:02d}:{t_sec:02d}")

    def set_start_time(self):
        # 将当前秒数转换为 MM:SS 格式填入
        self.start_time_var.set(self.sec_to_mmss(self.current_pos))

    def set_end_time(self):
        # 将当前秒数转换为 MM:SS 格式填入
        self.end_time_var.set(self.sec_to_mmss(self.current_pos))

    def browse_file(self):
        """浏览文件，若不在songs目录则自动复制"""
        # 1. 打开文件选择框，初始目录可以设为 songs，但也允许去别的地方
        file_path = filedialog.askopenfilename(
            title="选择音频文件",
            initialdir="songs", 
            filetypes=[("所有音频", "*.mp3 *.wav *.flac *.m4a")]
        )
        
        if file_path:
            # 获取文件名
            filename = os.path.basename(file_path)
            # 设定目标路径
            target_path = os.path.join("songs", filename)
            
            # 2. 判断路径：如果选中的文件路径 != songs文件夹下的目标路径
            # 使用 abspath 确保路径格式统一以便比较
            if os.path.abspath(file_path) != os.path.abspath(target_path):
                try:
                    # 确保 songs 文件夹存在
                    if not os.path.exists("songs"):
                        os.makedirs("songs")
                    
                    # 3. 复制文件 (copy2 会保留文件元数据)
                    shutil.copy2(file_path, target_path)
                    messagebox.showinfo("提示", f"监测到文件在外部，已自动复制到 songs 文件夹：\n{filename}")
                    
                except Exception as e:
                    messagebox.showerror("复制失败", f"无法复制文件到 songs 目录：\n{str(e)}")
                    return # 复制失败则不更新文件名

            # 4. 更新界面显示（只显示文件名）
            self.filename_var.set(filename)

    def ok(self):
        if not self.filename_var.get(): return
        
        # 1. 获取输入框中的字符串 (可能是 "1:20" 或 "80")
        start_str = self.start_time_var.get()
        end_str = self.end_time_var.get()
        
        # 2. 转换为秒数 (float)
        start_sec = self.mmss_to_sec(start_str)
        end_sec = self.mmss_to_sec(end_str)
        
        # 自动填充逻辑：如果结束时间是0，且知道音频长度，则填满
        if end_sec == 0 and self.audio_length > 0:
            end_sec = self.audio_length

        # 3. 保存回CSV时，使用纯秒数，保持原有数据格式
        self.result = [
            self.filename_var.get(),
            str(round(start_sec, 2)), # 转回字符串，保留2位小数
            str(round(end_sec, 2)),   # 转回字符串，保留2位小数
            self.comment_var.get()
        ]
        self.stop_audio()
        self.dialog.destroy()

    def cancel(self):
        self.stop_audio()
        self.dialog.destroy()

    def extract_chorus(self):
        """提取副歌功能"""
        filename = self.filename_var.get().strip()
        if not filename:
            messagebox.showwarning("警告", "请先选择音频文件")
            return

        filepath = f"songs/{filename}"
        if not os.path.exists(filepath):
            messagebox.showerror("错误", f"找不到音频文件: {filepath}")
            return

        # 创建副歌提取对话框
        ChorusExtractionDialog(self.dialog, filepath, self)

    def preview_segment(self):
        """预览当前设置的片段"""
        filename = self.filename_var.get().strip()
        if not filename:
            messagebox.showwarning("警告", "请先选择音频文件")
            return

        filepath = f"songs/{filename}"
        if not os.path.exists(filepath):
            messagebox.showerror("错误", f"找不到音频文件: {filepath}")
            return

        # 获取开始和结束时间
        try:
            start_time = self.mmss_to_sec(self.start_time_var.get())
            end_time = self.mmss_to_sec(self.end_time_var.get())
        except ValueError:
            messagebox.showerror("错误", "时间格式不正确")
            return

        if start_time >= end_time:
            messagebox.showerror("错误", "结束时间必须大于开始时间")
            return

        # 如果当前正在播放，先停止
        if self.is_playing:
            self.stop_audio()

        # 设置播放位置为开始时间
        self.current_pos = start_time
        self.progress_var.set(start_time)
        self.update_time_label()

        # 开始播放
        try:
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play(start=start_time)
            self.is_playing = True
            self.play_button.config(text="暂停")
            self.play_start_time = time.time()
            self.track_start_pos = start_time
            self.stop_thread_flag = False
            threading.Thread(target=self.update_progress_for_segment, args=(end_time,), daemon=True).start()
        except Exception as e:
            messagebox.showerror("错误", f"播放失败: {str(e)}")

    def update_progress_for_segment(self, end_time):
        """更新进度条并检查是否到达片段结束时间"""
        while self.is_playing and not self.stop_thread_flag:
            if not pygame.mixer.music.get_busy(): break
            elapsed = time.time() - self.play_start_time
            current = self.track_start_pos + elapsed
            if current > self.audio_length: current = self.audio_length
            if current > end_time: current = end_time  # 限制在片段结束时间
            self.current_pos = current
            self.progress_var.set(current)
            self.update_time_label()
            
            # 如果到达片段结束时间，自动停止播放
            if current >= end_time:
                self.stop_audio()
                break
                
            time.sleep(0.1)
        if self.is_playing:
            self.is_playing = False
            try: self.play_button.config(text="播放")
            except: pass

    def on_closing(self):
        self.stop_audio()
        self.dialog.destroy()

class ChorusExtractionDialog:
    def __init__(self, parent, filepath, song_dialog):
        self.parent = parent
        self.filepath = filepath
        self.song_dialog = song_dialog
        self.intervals = []
        
        # 初始化 mixer
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("副歌提取结果(实验性)")
        self.dialog.geometry("700x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 居中
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))

        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        ttk.Label(main_frame, text="检测到的可能是副歌的片段:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(0, 10))

        # 创建树形视图显示片段
        columns = ('序号', '开始时间', '结束时间', '时长')
        self.tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=10)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor=tk.CENTER)

        # 添加滚动条
        tree_scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scrollbar.set)

        self.tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 10))
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 音频预览区域
        preview_frame = ttk.LabelFrame(main_frame, text="音频预览", padding="10")
        preview_frame.pack(fill=tk.X, pady=(0, 10))

        self.time_label = ttk.Label(preview_frame, text="00:00 / 00:00")
        self.time_label.pack()

        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_scale = ttk.Scale(preview_frame, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.progress_var)
        self.progress_scale.pack(fill=tk.X, pady=5, padx=10)
        self.progress_scale.state(['disabled'])
        self.progress_scale.bind("<ButtonRelease-1>", self.on_slider_release)

        # 控制按钮
        control_frame = ttk.Frame(preview_frame)
        control_frame.pack(fill=tk.X, pady=5)

        self.play_button = ttk.Button(control_frame, text="播放", command=self.toggle_playback)
        self.play_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="播放选中片段", command=self.play_selected_segment).pack(side=tk.LEFT, padx=5)

        # 从选中片段设置时间
        selected_time_frame = ttk.Frame(control_frame)
        selected_time_frame.pack(fill=tk.X, pady=2)
        ttk.Button(selected_time_frame, text="设为开始时间", command=self.set_start_time).pack(side=tk.LEFT, padx=5)
        ttk.Button(selected_time_frame, text="设为结束时间", command=self.set_end_time).pack(side=tk.LEFT, padx=5)

        # 手动时间设置区域
        manual_frame = ttk.LabelFrame(main_frame, text="手动时间设置", padding="10")
        manual_frame.pack(fill=tk.X, pady=(10, 0))

        # 开始时间设置
        start_time_frame = ttk.Frame(manual_frame)
        start_time_frame.pack(fill=tk.X, pady=2)
        ttk.Label(start_time_frame, text="开始时间:").pack(side=tk.LEFT)
        self.manual_start_time = tk.StringVar(value="0:00")
        self.manual_start_entry = ttk.Entry(start_time_frame, textvariable=self.manual_start_time, width=15)
        self.manual_start_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(start_time_frame, text="快速选择当前片段开始时间", command=self.set_start_from_selection).pack(side=tk.LEFT, padx=5)

        # 结束时间设置
        end_time_frame = ttk.Frame(manual_frame)
        end_time_frame.pack(fill=tk.X, pady=2)
        ttk.Label(end_time_frame, text="结束时间:").pack(side=tk.LEFT)
        self.manual_end_time = tk.StringVar(value="0:00")
        self.manual_end_entry = ttk.Entry(end_time_frame, textvariable=self.manual_end_time, width=15)
        self.manual_end_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(end_time_frame, text="快速选择当前片段结束时间", command=self.set_end_from_selection).pack(side=tk.LEFT, padx=5)

        # 确认按钮
        confirm_frame = ttk.Frame(manual_frame)
        confirm_frame.pack(fill=tk.X, pady=5)
        ttk.Button(confirm_frame, text="确认时间", command=self.confirm_manual_times).pack(side=tk.LEFT, padx=5)

        # 底部按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="快速应用选中片段", command=self.apply_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="关闭", command=self.cancel).pack(side=tk.RIGHT, padx=5)

        # 初始化音频
        self.is_playing = False
        self.current_pos = 0.0
        self.audio_length = 0
        self.stop_thread_flag = False
        self.play_start_time = 0
        self.track_start_pos = 0
        
        self.load_audio(filepath)
        
        # 开始提取副歌
        self.extract_chorus_async()

    def extract_chorus_async(self):
        """异步提取副歌，避免界面卡顿"""
        self.dialog.config(cursor="wait")
        self.parent.config(cursor="wait")
        self.dialog.update()
        
        # 在新线程中执行提取
        thread = threading.Thread(target=self._extract_chorus_internal)
        thread.daemon = True
        thread.start()

    def _extract_chorus_internal(self):
        """内部执行副歌提取"""
        try:
            # 导入副歌提取模块
            import sys
            from pathlib import Path
            _ROOT = Path(__file__).resolve().parent
            if str(_ROOT) not in sys.path:
                sys.path.insert(0, str(_ROOT))
            from chorus_extractor import extract_chorus_intervals

            # 调用副歌提取函数，请求返回多个候选片段
            self.intervals = extract_chorus_intervals(self.filepath, num_candidates=10)  # 请求最多10个候选片段
            
            # 在主线程中更新UI
            self.dialog.after(0, self._update_ui_with_results)
            
        except ImportError:
            self.dialog.after(0, lambda: messagebox.showerror("错误", "缺少必要的库，请安装: librosa, numpy, scipy, scikit-learn\n命令: pip install librosa numpy scipy scikit-learn"))
            self.dialog.after(0, self.cancel)
        except Exception as e:
            self.dialog.after(0, lambda: messagebox.showerror("错误", f"提取副歌时发生错误: {str(e)}"))
            self.dialog.after(0, self.cancel)
        finally:
            # 恢复光标
            self.dialog.after(0, lambda: self.dialog.config(cursor=""))
            self.dialog.after(0, lambda: self.parent.config(cursor=""))

    def _update_ui_with_results(self):
        """更新UI显示结果"""
        if self.intervals:
            # 清空现有项目
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # 添加检测到的片段
            for i, (start_time, end_time) in enumerate(self.intervals):
                duration = end_time - start_time
                self.tree.insert('', 'end', values=(
                    i+1,
                    f"{self.sec_to_mmss(start_time)}",
                    f"{self.sec_to_mmss(end_time)}",
                    f"{self.sec_to_mmss(duration)}"
                ), tags=(start_time, end_time))  # 使用tags保存原始数值用于后续处理
            
            # 默认选择第一项
            children = self.tree.get_children()
            if children:
                self.tree.selection_set(children[0])
                self.tree.focus(children[0])
        else:
            messagebox.showinfo("提示", "未检测到明显的副歌段落")
            self.cancel()

    def load_audio(self, filepath):
        if os.path.exists(filepath):
            try:
                pygame.mixer.music.load(filepath)
                self.audio_length = 0
                try:
                    audio = MutagenFile(filepath)
                    if audio and audio.info:
                        self.audio_length = audio.info.length
                except: pass
                
                if self.audio_length == 0:
                    try:
                        sound = pygame.mixer.Sound(filepath)
                        self.audio_length = sound.get_length()
                    except: pass
                
                if self.audio_length == 0: self.audio_length = 120

                self.progress_scale.configure(to=self.audio_length)
                self.progress_scale.state(['!disabled'])
                self.update_time_label()
                
            except Exception as e:
                print(f"Load error: {e}")
                self.progress_scale.state(['disabled'])
        else:
            self.progress_scale.state(['disabled'])

    def on_slider_release(self, event):
        if self.audio_length > 0:
            pos = self.progress_scale.get()
            self.current_pos = pos
            self.update_time_label()
            if self.is_playing:
                self.restart_playback(pos)

    def restart_playback(self, start_pos):
        if os.path.exists(self.filepath):
            pygame.mixer.music.stop()
            pygame.mixer.music.load(self.filepath)
            pygame.mixer.music.play(start=start_pos)
            self.play_start_time = time.time()
            self.track_start_pos = start_pos
            
            # 确保线程正在运行
            if not self.is_playing:
                self.is_playing = True
                self.play_button.config(text="暂停")
                self.stop_thread_flag = False
                threading.Thread(target=self.update_progress, daemon=True).start()

    def toggle_playback(self):
        if not os.path.exists(self.filepath): return

        if not self.is_playing:
            try:
                pygame.mixer.music.load(self.filepath)
                pygame.mixer.music.play(start=self.current_pos)
                self.is_playing = True
                self.play_button.config(text="暂停")
                self.play_start_time = time.time()
                self.track_start_pos = self.current_pos
                self.stop_thread_flag = False
                threading.Thread(target=self.update_progress, daemon=True).start()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        else:
            self.stop_audio()

    def play_selected_segment(self):
        """播放选中的片段"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先在上方选择一个片段")
            return

        item = self.tree.item(selection[0])
        values = item['tags']
        start_time = float(values[0])
        
        # 跳转到选中片段的开始位置并播放
        self.current_pos = start_time
        self.progress_var.set(start_time)
        self.update_time_label()
        
        if self.is_playing:
            self.restart_playback(start_time)
        else:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(self.filepath)
            pygame.mixer.music.play(start=start_time)
            self.is_playing = True
            self.play_button.config(text="暂停")
            self.play_start_time = time.time()
            self.track_start_pos = start_time
            self.stop_thread_flag = False
            threading.Thread(target=self.update_progress, daemon=True).start()

    def update_progress(self):
        while self.is_playing and not self.stop_thread_flag:
            if not pygame.mixer.music.get_busy(): break
            elapsed = time.time() - self.play_start_time
            current = self.track_start_pos + elapsed
            if current > self.audio_length: current = self.audio_length
            self.current_pos = current
            self.progress_var.set(current)
            self.update_time_label()
            
            # 检查是否正在播放选中的片段，如果是则检查是否到达片段结束时间
            selection = self.tree.selection()
            if selection:
                item = self.tree.item(selection[0])
                tags = item['tags']  # 使用tags中的原始数值，而不是values中的格式化时间
                end_time = float(tags[1])  # tags[1] 是结束时间的原始浮点值
                # 如果当前播放位置超过了选中片段的结束时间，则自动暂停
                if current >= end_time:
                    self.stop_audio()
                    break
                    
            time.sleep(0.1)
        if self.is_playing:
            self.is_playing = False
            try: self.play_button.config(text="播放")
            except: pass

    def stop_audio(self):
        self.stop_thread_flag = True
        pygame.mixer.music.stop()
        self.is_playing = False
        self.play_button.config(text="播放")

    def update_time_label(self):
        c_min, c_sec = divmod(int(self.current_pos), 60)
        t_min, t_sec = divmod(int(self.audio_length), 60)
        self.time_label.config(text=f"{c_min:02d}:{c_sec:02d} / {t_min:02d}:{t_sec:02d}")

    def apply_selected(self):
        """应用选中的片段到主对话框"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个片段")
            return

        item = self.tree.item(selection[0])
        tags = item['tags']
        # 直接使用tags中保存的原始数值（已经是秒数格式）
        start_time = float(tags[0])
        end_time = float(tags[1])
        
        # 如果当前正在播放，先停止播放
        if self.is_playing:
            self.stop_audio()
        
        # 更新主对话框的时间字段
        self.song_dialog.start_time_var.set(self.song_dialog.sec_to_mmss(start_time))
        self.song_dialog.end_time_var.set(self.song_dialog.sec_to_mmss(end_time))
        
        # 更新主对话框的进度条位置
        self.song_dialog.current_pos = start_time
        self.song_dialog.progress_var.set(start_time)
        self.song_dialog.update_time_label()
        
        self.dialog.destroy()

    def cancel(self):
        self.stop_audio()
        self.dialog.destroy()

    def set_start_from_selection(self):
        """将选中片段的开始时间设置到手动输入框"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个片段")
            return

        item = self.tree.item(selection[0])
        values = item['tags']
        start_time = float(values[0])
        self.manual_start_time.set(self.sec_to_mmss(start_time))

    def set_end_from_selection(self):
        """将选中片段的结束时间设置到手动输入框"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个片段")
            return

        item = self.tree.item(selection[0])
        values = item['tags']
        end_time = float(values[1])
        self.manual_end_time.set(self.sec_to_mmss(end_time))

    def confirm_manual_times(self):
        """确认手动输入的时间并应用到主对话框"""
        try:
            start_time = self.mmss_to_sec(self.manual_start_time.get())
            end_time = self.mmss_to_sec(self.manual_end_time.get())
            
            # 更新主对话框的时间字段
            self.song_dialog.start_time_var.set(self.song_dialog.sec_to_mmss(start_time))
            self.song_dialog.end_time_var.set(self.song_dialog.sec_to_mmss(end_time))
            
            # 更新主对话框的进度条位置
            self.song_dialog.current_pos = start_time
            self.song_dialog.progress_var.set(start_time)
            self.song_dialog.update_time_label()
            
            messagebox.showinfo("成功", "时间已更新到主对话框")
            
        except ValueError:
            messagebox.showerror("错误", "请输入正确的时间格式 (MM:SS 或 秒数)")

        # 如果当前正在播放，先停止播放
        if self.is_playing:
            self.stop_audio()

        self.dialog.destroy()

    # --- 辅助工具：时间转换 ---
    def sec_to_mmss(self, seconds_str):
        """将秒数(字符串或浮点)转换为 MM:SS.ss 格式"""
        try:
            total_sec = float(seconds_str)
            m = int(total_sec // 60)
            s = total_sec % 60
            # 如果有小数部分，保留两位小数，否则只显示整数
            if s % 1 == 0:
                return f"{m}:{int(s):02d}"
            else:
                return f"{m}:{s:05.2f}"
        except ValueError:
            return "0:00"

    def mmss_to_sec(self, mmss_str):
        """将 MM:SS 格式或纯数字转换为秒数(浮点)"""
        mmss_str = mmss_str.strip()
        if not mmss_str:
            return 0.0
        try:
            if ":" in mmss_str:
                parts = mmss_str.split(":")
                if len(parts) == 2:
                    return float(parts[0]) * 60 + float(parts[1])
                elif len(parts) == 3: # HH:MM:SS
                    return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
            else:
                return float(mmss_str)
        except ValueError:
            return 0.0
        return 0.0

    def set_start_time(self):
        # 将当前秒数转换为 MM:SS 格式填入
        self.manual_start_time.set(self.sec_to_mmss(self.current_pos))

    def set_end_time(self):
        # 将当前秒数转换为 MM:SS 格式填入
        self.manual_end_time.set(self.sec_to_mmss(self.current_pos))

    def on_closing(self):
        self.stop_audio()
        self.dialog.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = OtakuDanceGUI(root)
    root.mainloop()