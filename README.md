# ajjj-ads

## 项目简介

本项目用于自动解析指定目录（如 `~/Downloads/ajjj/`）下的所有视频文件，识别并统计视频中的广告（包括软性广告），输出每个广告的出现文件、时间、商品名称等信息。适用于中文普通话视频。

## 功能流程
1. 遍历目标目录下所有视频文件（如 mp4、mkv、avi 等）
2. 提取视频音频
3. 音频转文字（ASR，支持中文普通话）
4. 使用 Ollama 本地 Qwen2 7B Instruct 模型分析文本，判断广告及商品信息
5. 汇总统计所有广告信息，输出为 CSV 文件

## 依赖环境
- Python 3.8 及以上
- ffmpeg（需本地安装，命令行可用）
- [openai-whisper](https://github.com/openai/whisper)
- pandas
- requests
- tqdm
- Ollama（本地已安装并可用，需有 Qwen2 7B Instruct 模型）

## 安装方法
1. 安装 Python 依赖：
   ```bash
   pip install -r requirements.txt
   ```
2. 安装并配置好 ffmpeg（[下载地址](https://ffmpeg.org/download.html)）
3. 安装并启动 Ollama，并拉取 Qwen2 7B Instruct 模型：
   ```bash
   ollama pull qwen2:7b-instruct
   ollama serve
   ```

## 使用方法
1. 修改 `main.py` 中的 `VIDEO_DIR` 路径为你的视频目录（如 `~/Downloads/ajjj/`）。
2. 运行主程序：
   ```bash
   python main.py
   ```
3. 结果会输出到 `output/ads_summary.csv`，包含每个广告的文件名、出现时间、商品名称、广告类型等信息。

## 输出说明
- 输出文件：`output/ads_summary.csv`
- 字段说明：
  - 文件名
  - 广告出现时间（如有）
  - 商品名称
  - 广告类型（硬广/软广）
  - 广告文本片段

## 常见问题
- 如遇 ffmpeg、whisper、ollama 未安装或命令不可用，请先确保其已正确安装并配置环境变量。
- Ollama 需保证本地服务已启动，且 Qwen2 7B Instruct 模型已拉取。

## 联系方式
如有问题或建议，请联系作者。 