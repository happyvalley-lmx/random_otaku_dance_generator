# random_otaku_dance_generator
基于python-ffmpeg的随舞音频文件生成器
## 程序说明
### otaku_dance.py
根据csv表格内的信息，将 **songs** 文件夹内的原始乐曲文件按音频时长切割后添加淡入淡出效果，并在开头加上miku的5秒倒数音频，输出的结果保存在 **output** 文件夹内
### random_otaku.py
根据csv表格内的信息，将上述生成的 **output** 文件夹内的音频以随机顺序打乱后拼接在一起，输出 ffmpeg 拼接需要使用的打乱后的歌单顺序 **songlist.txt** 以及最终随舞所使用的音频文件 **output_audio.mp3**
### integrated_manager.py
可视化GUI版本的随舞音频生成器，提供图形界面方便管理和编辑歌曲列表。主要功能包括：
- CSV文件的可视化编辑（添加、删除、编辑曲目）
- 音频预览功能，支持播放、暂停和时间定位
- 时间设置功能，可以直接在预览时设置开始和结束时间
- 实时进度显示和处理状态反馈
- 文件自动复制功能，选择外部文件时会自动复制到songs目录
- 一键生成最终音频文件

## 使用方法

本程序运行需要 **ffmpeg-python** 模块以及 **ffmpeg** 的可执行文件
后者已包含在目录下，前者需要使用pip进行安装
```
pip install ffmpeg-python pygame mutagen
```
### 图形界面方式（推荐）
运行集成管理器：
```
python integrated_manager.py
```
在图形界面中：
1. 使用"添加曲目"按钮添加歌曲并设置开始/结束时间
2. 使用音频预览功能精确调整时间点
3. 使用"生成音频"按钮一键完成整个处理流程

### 命令行方式
请参考 **songs.csv** 文件填写信息，并将乐曲文件放置于 **songs** 文件夹下
随后在主目录下创建 **cache** 文件夹与 **output** 文件夹
最后依次运行 **otaku_dance.py** 与 **random_otaku.py** 即可
```
python otaku_dance.py
python random_otaku.py
```


### 自动副歌(高潮)提取示例

仓库新增了一个基于谱聚类的副歌提取模块 `chorus_extractor.py`，以及演示脚本 `scripts/extract_chorus.py`。

依赖（建议创建 venv 后安装）:

```
pip install librosa numpy scipy scikit-learn
```

示例运行:

```
python scripts/extract_chorus.py sample.mp3
```

批量标记songs文件夹内的歌曲并输出到csv：
···
python scripts/batch_extract_chorus.py
···

脚本会输出检测到的副歌时间区间（秒）。此实现参考自文章 https://developer.aliyun.com/article/1119679 ，步骤包括：CQT -> 节拍同步 -> 自相关邻接矩阵与MFCC相邻矩阵融合 -> 拉普拉斯特征向量 -> KMeans 聚类 -> 选取能量最高的类别的最后一个片段作为副歌候选。


## 致谢
由 [FFmpeg](https://github.com/FFmpeg/FFmpeg) 提供的开源音频处理程序
由 [金块(GolDenSiR)](https://space.bilibili.com/19838508) 调的初音未来倒计时音频
## 附录
### songs - day1.csv
2023 南宁秋典 day1 烤随舞歌单(可自行改名替换songs.csv)
### songs - day2.csv
2023 南宁秋典 day2 烤随舞歌单(同上)
