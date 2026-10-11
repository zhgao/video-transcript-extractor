# 🎥 AI 视频字幕提取器

**[English](README.md)** | 中文

一个强大的 Web 应用，用前沿 AI 技术提取并总结视频字幕。

## ✨ 功能

- **多平台支持**：YouTube、TikTok 及 1000+ 视频平台
- **智能提取**：优先抓取字幕，失败时自动降级为 AI 转写
- **AI 语音识别**：无字幕视频使用 OpenAI Whisper 转写
- **AI 总结**：使用 Llama 3.2（Ollama）生成简洁总结
- **实时进度**：转写进度实时推送到浏览器
- **精美界面**：干净现代的界面，段落排版美观
- **一键复制**：字幕一键复制到剪贴板

## 🛠️ 技术栈

- **后端**：Flask（Python）
- **语音转文字**：OpenAI Whisper
- **AI 总结**：Ollama（Llama 3.2）
- **视频处理**：yt-dlp
- **字幕接口**：youtube-transcript-api
- **前端**：原生 JavaScript、CSS3

## 📋 前置要求

- Python 3.8+
- ffmpeg
- Ollama
- Chrome 浏览器（用于 cookie 认证）

## 🚀 安装

### 1. 安装系统依赖

```bash
# 安装 ffmpeg
brew install ffmpeg

# 安装 Ollama
brew install ollama
```

### 2. 克隆并配置

```bash
git clone https://github.com/zhgao/video-transcript-extractor.git
cd video-transcript-extractor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. 安装 AI 模型

```bash
ollama pull llama3.2
```

### 4. 配置 YouTube Cookies（可选但推荐）

避免被 YouTube 限流：

1. 安装浏览器扩展："Get cookies.txt LOCALLY"
2. 登录后打开 youtube.com
3. 导出 cookies 为项目目录下的 `cookies.txt`

## 🎯 使用

### 启动应用

```bash
source venv/bin/activate
python app.py
```

浏览器打开：**http://localhost:8080**

### 使用流程

1. **粘贴视频链接**：任意 YouTube、TikTok 或其他支持平台的链接
2. **提取字幕**：
   - 优先抓取现有字幕（快速，约 5 秒）
   - 无字幕时下载音频并用 Whisper AI 转写（约 1–5 分钟）
3. **总结**：点击"✨ Summarize"生成 AI 总结
4. **复制**：一键复制到剪贴板

### 公网部署模式（可选）

设置环境变量 `ACCESS_PASSWORD` 即可开启带密码保护的公网模式：

```bash
ACCESS_PASSWORD=你的密码 BIND_HOST=0.0.0.0 python app.py
```

公网模式自动启用：登录保护、按 IP 限流、SSRF 防护（拒绝内网地址）、访问记录按用户隔离。

## 🔧 内部原理

### 提取流程

```
用户粘贴链接
    ↓
尝试 YouTube 字幕接口（快速）
    ↓（被屏蔽或无字幕）
用 yt-dlp + cookies 尝试
    ↓（无字幕）
下载音频 → Whisper AI 转写
    ↓
展示格式化字幕
```

### AI 转写（Whisper）

无字幕时：

1. 用 yt-dlp 下载音频
2. 转为 MP3 格式
3. Whisper AI 将语音转成文字
4. 实时流式推送到浏览器

### AI 总结（Ollama）

1. 字幕发送到本地 Ollama 服务
2. Llama 3.2 生成 3–5 条要点总结
3. 在高亮总结框中展示

## 📁 项目结构

```
video-transcript-extractor/
├── app.py                 # Flask 后端
├── requirements.txt       # Python 依赖
├── cookies.txt            # YouTube cookies（可选）
├── templates/
│   └── index.html        # 主界面
├── static/
│   ├── script.js         # 前端 JavaScript
│   └── style.css         # 样式
├── venv/                 # 虚拟环境
└── README.md            # 英文说明
```

## 🐛 故障排查

### "YouTube is blocking requests"（YouTube 屏蔽请求）

- 添加 cookies.txt 文件（见安装步骤）
- 两次请求之间间隔几分钟

### "Whisper transcription failed"（Whisper 转写失败）

- 检查 ffmpeg 是否安装：`which ffmpeg`
- 确保磁盘空间足够下载音频

### "Failed to generate summary"（生成总结失败）

- 检查 Ollama 是否运行：`ollama list`
- 确保已安装 llama3.2 模型：`ollama pull llama3.2`

### 页面一直显示 "Extracting transcript..."

- 硬刷新：Cmd+Shift+R
- 清浏览器缓存
- 试试无痕/隐私窗口

## 🔒 隐私与安全

- 所有处理都在本机完成
- 不向外部服务器发送数据（视频平台除外）
- Ollama 完全离线运行
- Cookies 仅用于 YouTube 认证

## 📊 性能

- **字幕提取**：约 5 秒
- **Whisper 转写**：1–5 分钟（取决于视频长度）
- **AI 总结**：10–30 秒
- **模型大小**：Whisper base（约 150MB）、Llama 3.2（约 2GB）

## 🚧 已知限制

- Whisper 转写长视频（>30 分钟）较慢
- 下载视频需要较好的网络
- 某些平台可能屏蔽自动化访问
- 总结质量取决于字幕准确度

## 📝 开源协议

MIT License——欢迎使用和修改！详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- OpenAI Whisper（语音识别）
- Ollama（本地 AI 推理）
- yt-dlp（视频处理）
- Flask（Web 框架）

---

**Built with ❤️ using cutting-edge AI technology**
