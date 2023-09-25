# random_otaku_dance_generator  
基于python-ffmpeg的随舞音频文件生成器  
## 程序说明  
### otaku_dance.py  
根据csv表格内的信息，将 **songs** 文件夹内的原始乐曲文件按音频时长切割后添加淡入淡出效果，并在开头加上miku的5秒倒数音频，输出的结果保存在 **output** 文件夹内  
### random_otaku.py  
根据csv表格内的信息，将上述生成的 **output** 文件夹内的音频以随机顺序打乱后拼接在一起，输出 ffmpeg 拼接需要使用的打乱后的歌单顺序 **songlist.txt** 以及最终随舞所使用的音频文件 **output_audio.mp3**  
## 使用方法  
本程序运行需要 **ffmpeg-python** 模块以及 **ffmpeg** 的可执行文件  
后者已包含在目录下，前者需要使用pip进行安装  
```
pip install ffmpeg-python
```
请参考 **songs.csv** 文件填写信息，并将乐曲文件放置于 **songs** 文件夹下  
随后在主目录下创建 **cache** 文件夹与 **output** 文件夹  
最后依次运行 **otaku_dance.py** 与 **random_otaku.py** 即可  
```
python otaku_dance.py
python random_otaku.py
```  
## 致谢  
由 [FFmpeg](https://github.com/FFmpeg/FFmpeg) 提供的开源音频处理程序  
由 [金块(GolDenSiR)](https://space.bilibili.com/19838508) 调的初音未来倒计时音频  
## 附录  
### songs - day1.csv  
2023 南宁秋典 day1 烤随舞歌单(可自行改名替换songs.csv)  
### songs - day2.csv  
2023 南宁秋典 day2 烤随舞歌单(同上)  