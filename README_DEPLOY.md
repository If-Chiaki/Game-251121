# 部署指南 (Render)

这个项目已经配置好可以直接部署到 Render 平台。

## 步骤 1: 准备代码
1. 确保你已经将这些文件上传到了你的 GitHub 仓库。

## 步骤 2: 在 Render 上创建服务
1. 注册/登录 [Render.com](https://render.com)。
2. 点击 **"New +"** 按钮，选择 **"Web Service"**。
3. 连接你的 GitHub 仓库。
4. 在配置页面填写以下信息：
    *   **Name**: `game-classic` (或者你喜欢的名字)
    *   **Runtime**: `Python 3`
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. 选择 **"Free"** 套餐。
6. 点击 **"Create Web Service"**。

## 步骤 3: 等待部署
Render 会自动下载依赖并启动服务。等待几分钟，直到看到 "Live" 状态。
你会获得一个类似 `https://game-classic.onrender.com` 的网址。

## 步骤 4: 开始游戏
1. 将网址发给你的朋友。
2. 大家在浏览器中打开，输入名字加入。
3. 至少 2 人加入后，点击“开始游戏”。

## 本地测试
如果你想先在本地运行：
1. 安装 Python。
2. 运行 `pip install -r requirements.txt`。
3. 运行 `uvicorn main:app --reload`。
4. 打开浏览器访问 `http://127.0.0.1:8000`。
