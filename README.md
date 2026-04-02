# 🤖 tg-auto-heart

一个基于 [Telethon](https://github.com/LonamiWebs/Telethon) 的 Telegram 群组管理机器人，支持禁言、踢人、解禁、AI 总结、随机夸人、广告检测与答题验证等功能，以 systemd 服务方式常驻运行。

---

## ✨ 功能特性

| 指令 | 说明 |
|------|------|
| `禁言 N 秒/分钟/小时/天` | 临时禁言被回复用户，最短 30 秒，最长 366 天 |
| `禁言 永久` | 永久禁言被回复用户 |
| `,踢` | 踢出并封禁被回复用户，同时清除其历史消息 |
| `解禁` | 解除被回复用户的所有限制 |
| `解除拉黑` | 同解禁，解除封禁状态 |
| `真棒` | 随机发送一条夸奖语给被回复用户 |
| `总结最近 N 条` | 调用 AI 对最近 N 条消息进行总结 |
| 广告检测与答题验证 | 可对低活跃用户消息进行 AI 广告识别，并触发限时答题验证 |
| `状态` | 查询机器人运行状态 |
| `用户ID/用户名 + 指令` | 不回复消息时，直接指定目标用户 ID 或 @用户名执行指令 |

> 所有操作仅限 `CONTROL_USER_IDS` 中配置的管理员使用。
> 机器人发出的操作反馈消息会在 30 秒后自动删除。

---

## 🗂️ 项目结构

```
tg-auto-heart/
├── tg_auto_heart.py        # 主程序
├── requirements.txt        # Python 依赖
├── tg-auto-heart.service   # systemd 服务配置
└── README.md
```

---

## 🚀 部署教程

### 系统要求

- Debian 11/12 或 Ubuntu 20.04/22.04/24.04
- Python 3.10+
- root 或 sudo 权限

---

### Debian 部署步骤

```bash
# 1. 更新系统并安装依赖
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv git

# 2. 创建项目目录
mkdir -p /opt/tg-auto-heart
cd /opt/tg-auto-heart

# 3. 克隆项目
git clone https://github.com/YOUR_USERNAME/tg-auto-heart.git .

# 4. 创建虚拟环境并安装依赖
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

# 5. 配置参数（编辑主程序顶部的配置区域）
nano tg_auto_heart.py
# 填写：API_ID、API_HASH、TARGET_CHAT_ID、CONTROL_USER_IDS
# 如需 AI 总结功能，还需填写：AI_API_BASE、AI_API_KEY

# 6. 首次运行，完成 Telegram 登录授权（仅需一次）
.venv/bin/python tg_auto_heart.py
# 按提示输入手机号和验证码，授权完成后 Ctrl+C 退出

# 7. 安装 systemd 服务
cp tg-auto-heart.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable tg-auto-heart
systemctl start tg-auto-heart

# 8. 查看运行状态
systemctl status tg-auto-heart
```

---

### Ubuntu 部署步骤

Ubuntu 与 Debian 步骤基本一致，以下列出差异点：

```bash
# 1. 更新系统并安装依赖
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git

# 2. 创建项目目录（使用 sudo）
sudo mkdir -p /opt/tg-auto-heart
sudo chown $USER:$USER /opt/tg-auto-heart
cd /opt/tg-auto-heart

# 3. 克隆项目
git clone https://github.com/YOUR_USERNAME/tg-auto-heart.git .

# 4. 创建虚拟环境并安装依赖
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

# 5. 配置参数
nano tg_auto_heart.py
# 填写：API_ID、API_HASH、TARGET_CHAT_ID、CONTROL_USER_IDS
# 如需 AI 总结功能，还需填写：AI_API_BASE、AI_API_KEY

# 6. 首次运行，完成 Telegram 登录授权（仅需一次）
.venv/bin/python tg_auto_heart.py
# 按提示输入手机号和验证码，授权完成后 Ctrl+C 退出

# 7. 安装 systemd 服务
sudo cp tg-auto-heart.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tg-auto-heart
sudo systemctl start tg-auto-heart

# 8. 查看运行状态
sudo systemctl status tg-auto-heart
```

> **Ubuntu 注意事项**：
> - Ubuntu 22.04+ 默认 Python 为 `python3`，无需额外安装
> - 如遇 `externally-managed-environment` 错误，使用虚拟环境（已在步骤 4 中处理）
> - UFW 防火墙默认不影响 Telegram 出站连接，无需额外配置

---

## ⚙️ 配置说明

编辑 `tg_auto_heart.py` 顶部的配置区域：

```python
# ===== 必填配置 =====
API_ID = 0                          # 从 https://my.telegram.org 获取
API_HASH = "your_api_hash_here"     # 从 https://my.telegram.org 获取
SESSION = "/opt/tg-auto-heart/tg_hub"  # Session 文件路径
TARGET_CHAT_ID = -100XXXXXXXXXX     # 目标群组 ID（负数，带 -100 前缀）
CONTROL_USER_IDS = {123456789}      # 管理员 Telegram 用户 ID 集合

# ===== AI 总结功能（可选）=====
AI_API_BASE = "https://your-ai-api-endpoint/anthropic"  # AI API 地址
AI_API_KEY  = "your_ai_api_key_here"                    # AI API Key
AI_MODEL    = "claude-3-5-haiku-20241022"               # 使用的模型
```

### 如何获取 API_ID 和 API_HASH

1. 访问 [https://my.telegram.org](https://my.telegram.org)
2. 登录你的 Telegram 账号
3. 进入 **API development tools**
4. 创建应用，获取 `api_id` 和 `api_hash`

### 如何获取群组 ID

在群组中发送任意消息，然后通过 [@userinfobot](https://t.me/userinfobot) 或 Telegram Web 的 URL 获取群组 ID。群组 ID 通常为负数，超级群组以 `-100` 开头。

### 如何获取用户 ID

向 [@userinfobot](https://t.me/userinfobot) 发送消息，它会返回你的用户 ID。

---

## 🔧 常用运维命令

```bash
# 查看实时日志
journalctl -u tg-auto-heart -f

# 重启服务
systemctl restart tg-auto-heart

# 停止服务
systemctl stop tg-auto-heart

# 查看服务状态
systemctl status tg-auto-heart
```

---

## 📦 依赖

- [Telethon](https://github.com/LonamiWebs/Telethon) >= 1.42.0
- Python 3.10+

---

## 📄 License

MIT License

---

## 🙏 致谢

- [Telethon](https://github.com/LonamiWebs/Telethon) — 优秀的 Telegram MTProto 客户端库
