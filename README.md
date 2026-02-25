# QQ表情包管理器

一个功能强大的QQ表情包管理工具，支持收藏表情和市场表情的智能分类、整理和格式转换。

## 功能特性

### 核心功能
- **收藏表情管理**
  - 自动扫描QQ收藏表情目录
  - 按表情类型智能分类（静态/动态）
  - 支持批量导出和整理

- **市场表情管理**
  - 自动识别已下载的QQ市场表情
  - 按表情包分组管理
  - 支持表情预览和导出

- **格式转换**
  - 支持GIF、PNG、JPG等常见格式
  - 微信表情格式转换
  - 批量格式转换功能

### 界面特性
- **现代化UI设计**
  - 采用PyQt5构建的现代化界面
  - 侧边栏导航 + 卡片式布局
  - 支持浅色/深色主题切换

- **用户友好**
  - 直观的操作界面
  - 实时进度显示
  - 详细的操作日志

## 项目结构

```
qq-emoji-manager/
├── core/                   # 核心功能模块
│   ├── database.py        # 数据库管理
│   ├── favorite_emoji.py  # 收藏表情管理
│   ├── market_emoji.py    # 市场表情管理
│   └── qq_path_detector.py # QQ路径检测
├── new_ui/                 # 用户界面模块
│   ├── main_window.py     # 主窗口
│   ├── settings_page.py   # 设置页面
│   ├── components.py      # UI组件
│   ├── styles.py          # 样式定义
│   └── workers.py         # 后台工作线程
├── utils/                  # 工具模块
│   ├── clipboard.py       # 剪贴板操作
│   ├── format_converter.py # 格式转换器
│   ├── logger.py          # 日志管理
│   └── path_manager.py    # 路径管理
├── data/                   # 数据目录
├── main.py                 # 程序入口
├── build.py                # 统一打包脚本
├── build.spec              # PyInstaller配置
├── nuitka-config.cfg       # Nuitka配置
├── requirements.txt        # 依赖项
└── README.md              # 项目说明
```

## 安装步骤

### 环境要求
- Python 3.8+
- Windows 操作系统（支持Windows 10/11）

### 安装依赖

1. 克隆仓库
```bash
git clone https://github.com/yourusername/qq-emoji-manager.git
cd qq-emoji-manager
```

2. 创建虚拟环境（推荐）
```bash
python -m venv venv
```

3. 激活虚拟环境
```bash
# Windows
venv\Scripts\activate
```

4. 安装依赖
```bash
pip install -r requirements.txt
```

## 使用方法

### 启动程序
```bash
python main.py
```

### 基本操作

1. **首次使用**
   - 程序会自动检测QQ安装路径
   - 如未检测到，可在设置页面手动配置

2. **收藏表情管理**
   - 点击"收藏表情"页面
   - 点击"扫描表情"按钮
   - 选择需要导出的表情
   - 点击"导出选中"或"导出全部"

3. **市场表情管理**
   - 点击"市场表情"页面
   - 程序自动扫描已下载的表情包
   - 选择表情包查看详情
   - 支持批量导出

4. **格式转换**
   - 点击"格式转换"页面
   - 选择源文件或目录
   - 选择目标格式
   - 点击"开始转换"

### 设置选项
- **QQ路径设置**: 手动指定QQ安装目录
- **导出路径**: 设置默认导出目录
- **主题切换**: 切换浅色/深色主题

## 打包发布

项目提供了统一的打包脚本 `build.py`，支持 PyInstaller 和 Nuitka 两种打包方式。

### 打包命令

```bash
# 使用 PyInstaller 打包（目录模式，推荐）
python build.py

# 使用 PyInstaller 打包（单文件模式）
python build.py --onefile

# 使用 Nuitka 打包（需要安装 C 编译器）
python build.py --nuitka

# 清理构建产物
python build.py --clean

# 生成所有打包版本
python build.py --all
```

### 打包工具对比

| 工具 | 优点 | 缺点 |
|------|------|------|
| PyInstaller (目录) | 启动快、兼容性好 | 文件数量多 |
| PyInstaller (单文件) | 分发方便 | 启动较慢、体积大 |
| Nuitka | 性能最优、体积小 | 编译时间长、需要C编译器 |

### 打包产物

打包后的文件位于 `dist/` 目录：
- `dist/QQEmojiManager/` - PyInstaller 目录模式
- `dist/QQEmojiManager.exe` - PyInstaller 单文件模式
- `dist/nuitka/` - Nuitka 打包结果

## 技术栈

- **GUI框架**: PyQt5 >= 5.15.0
- **图像处理**: Pillow >= 9.0.0
- **Windows API**: pywin32 >= 300

## 开发计划

- [ ] 添加表情搜索功能
- [ ] 支持云端备份
- [ ] 添加表情编辑功能
- [ ] 支持自定义分类

## 贡献指南

欢迎提交Issue和Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 致谢

- 感谢PyQt5提供的强大GUI框架
- 感谢Pillow提供的图像处理能力

## 联系方式

如有问题或建议，欢迎通过以下方式联系：
- 提交 GitHub Issue
- 发送邮件至 [1269814800@qq.com]

---

**注意**: 本工具仅供学习和个人使用，请遵守QQ相关服务条款。
