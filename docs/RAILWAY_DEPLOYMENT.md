# Railway 部署指南

> **KevinRule 台股智能選股系統 - Railway 部署完整流程**
>
> 更新日期: 2025-10-28

---

## 📋 目錄

1. [部署前檢查](#部署前檢查)
2. [環境變數設定](#環境變數設定)
3. [部署步驟](#部署步驟)
4. [驗證部署](#驗證部署)
5. [故障排除](#故障排除)
6. [成本估算](#成本估算)

---

## 部署前檢查

### ✅ 必要文件確認

確認以下文件都已存在於專案根目錄：

```bash
KevinRule/
├── railway.json          ✅ Railway 配置
├── Procfile             ✅ 啟動命令
├── requirements.txt     ✅ Python 依賴
├── .env.example         ✅ 環境變數範本
└── frontend/app.py      ✅ 主應用程式
```

### 📦 配置文件內容

#### `railway.json`
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "streamlit run frontend/app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

#### `Procfile`
```
web: streamlit run frontend/app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
```

---

## 環境變數設定

### 🔑 必填環境變數

在 Railway Dashboard > Settings > Variables 中設定以下環境變數：

#### 1. **FINLAB_API_KEY** (必填)
```
描述: FinLab API Token
來源: https://ai.finlab.tw/
範例: your_finlab_api_key_here
```

#### 2. **ANTHROPIC_API_KEY** (選填)
```
描述: Claude AI API Key（用於智能分析）
來源: https://console.anthropic.com/
範例: sk-ant-api03-...
```

#### 3. **TRADING_ECONOMICS_API_KEY** (選填)
```
描述: Trading Economics API Key（用於經濟日曆）
來源: https://tradingeconomics.com/
範例: your_te_api_key_here
```

#### 4. **LINE_NOTIFY_TOKEN** (選填)
```
描述: LINE Notify Token（用於推播通知）
來源: https://notify-bot.line.me/
範例: your_line_token_here
```

#### 5. **APP_ENV** (選填)
```
描述: 應用環境
預設: production
可選值: development, production
```

---

### 📝 設定步驟

1. **進入 Railway Dashboard**
   ```
   https://railway.app/dashboard
   ```

2. **選擇專案**: KevinRule

3. **進入 Settings > Variables**

4. **添加環境變數**:
   - 點擊 "+ New Variable"
   - 輸入變數名稱和值
   - 點擊 "Add" 保存

5. **重要提示**:
   - ⚠️ 不要在 GitHub 上傳 `.env` 文件！
   - ✅ 使用 Railway 的 Variables 功能
   - 🔒 API Keys 會自動加密儲存

---

## 部署步驟

### 方式 1: GitHub 自動部署（推薦）

#### Step 1: 連接 GitHub Repository

1. 在 Railway Dashboard 中選擇專案 "KevinRule"
2. 點擊 "Settings" > "Source"
3. 點擊 "Connect GitHub Repo"
4. 選擇 **AndyKauo/KevinRule** repository
5. 選擇 **main** branch

#### Step 2: 配置部署設定

1. **Build Settings**:
   ```
   Builder: NIXPACKS
   Build Command: pip install -r requirements.txt
   ```

2. **Deploy Settings**:
   ```
   Start Command: streamlit run frontend/app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
   ```

3. **Environment**:
   ```
   Production
   ```

#### Step 3: 觸發部署

連接 GitHub 後，Railway 會自動：
- ✅ 檢測 `railway.json` 配置
- ✅ 安裝 Python 依賴
- ✅ 執行啟動命令
- ✅ 分配公開 URL

部署通常需要 **3-5 分鐘**。

---

### 方式 2: Railway CLI 手動部署

#### Step 1: 安裝 Railway CLI

```bash
# macOS/Linux
curl -fsSL https://railway.app/install.sh | sh

# Windows
powershell -c "irm https://railway.app/install.ps1 | iex"

# 或使用 npm
npm install -g @railway/cli
```

#### Step 2: 登入 Railway

```bash
railway login
```

#### Step 3: 連結專案

```bash
cd /Users/andykauo/MyWork/KevinRule

# 連結到現有專案
railway link

# 選擇專案 ID: c21b678d-c16c-489b-98ac-081d917d5a94
```

#### Step 4: 部署

```bash
# 部署到 Railway
railway up

# 或指定環境
railway up --environment production
```

#### Step 5: 查看日誌

```bash
# 實時查看部署日誌
railway logs

# 查看特定服務日誌
railway logs --service web
```

---

## 驗證部署

### ✅ 部署成功檢查清單

1. **查看部署狀態**
   - Railway Dashboard > Deployments
   - 狀態應為 "SUCCESS" 🟢

2. **檢查日誌**
   ```bash
   railway logs
   ```

   應看到：
   ```
   You can now view your Streamlit app in your browser.
   Local URL: http://0.0.0.0:$PORT
   ```

3. **訪問應用**
   - Railway 會自動分配 URL
   - 格式: `https://kevinrule-production.up.railway.app`
   - 點擊 "View Deployment" 或 "Open App"

4. **功能測試**
   - ✅ 主頁載入正常
   - ✅ 側邊欄顯示 "🧭 導航"
   - ✅ 主題切換功能正常
   - ✅ 市場總覽頁面顯示數據
   - ✅ 經濟日曆時間軸正常渲染

---

## 故障排除

### 問題 1: 部署失敗 - "Build Error"

**症狀**:
```
ERROR: Could not install packages due to an OSError
```

**解決方案**:
```bash
# 檢查 requirements.txt 是否正確
cat requirements.txt

# 確保版本號正確
streamlit>=1.30.0
finlab>=0.3.0
```

---

### 問題 2: 應用啟動失敗 - "Port Error"

**症狀**:
```
Error: Port $PORT is already in use
```

**解決方案**:
1. 確認 `Procfile` 使用 `$PORT` 變數
2. 不要硬編碼端口號（如 8501）
3. Railway 會自動分配端口

**正確的啟動命令**:
```bash
streamlit run frontend/app.py --server.port=$PORT --server.address=0.0.0.0
```

---

### 問題 3: FinLab API 登入失敗

**症狀**:
```
❌ FinLab API 登入失敗: Invalid API key
```

**解決方案**:
1. 檢查 Railway Variables 中的 `FINLAB_API_KEY`
2. 確認 API Key 沒有多餘空格
3. 前往 https://ai.finlab.tw/ 重新產生 Token
4. 重新部署: `railway up`

---

### 問題 4: 應用運行但無法訪問

**症狀**:
- 部署成功 ✅
- 日誌顯示應用啟動 ✅
- 但無法打開網頁 ❌

**解決方案**:
1. 檢查 Railway 是否分配了公開 URL
   - Settings > Networking > Public Domain
   - 點擊 "Generate Domain" 如果沒有

2. 檢查防火牆設定
   - Railway 預設允許所有入站流量

3. 檢查 Streamlit 配置
   ```bash
   --server.address=0.0.0.0  # 必須綁定所有介面
   --server.headless=true    # 無頭模式
   ```

---

### 問題 5: 經濟日曆顯示異常

**症狀**:
- HTML 代碼直接顯示
- 或時間軸無法滾動

**解決方案**:
1. 確認已推送最新修復到 GitHub:
   ```bash
   git log --oneline -5
   # 應看到: fix: 修復經濟日曆 HTML 顯示問題
   ```

2. 觸發重新部署:
   - Railway Dashboard > Deployments
   - 點擊 "Redeploy"

3. 清除瀏覽器快取後重新載入

---

## 成本估算

### Railway 免費方案限制

- ✅ **500 小時/月** 執行時間
- ✅ **100 GB** 頻寬
- ✅ **1 GB** 記憶體
- ✅ **1 vCPU**
- ✅ **1 GB** 儲存空間

### 適用性評估

**KevinRule 預估用量**:
- 記憶體: ~300 MB（Streamlit + Pandas）
- CPU: ~0.2 vCPU（閒置時）
- 儲存: ~50 MB（代碼 + DuckDB）
- 頻寬: ~5 GB/月（假設 100 次訪問）

✅ **結論**: 免費方案完全足夠！

### 付費方案（如需升級）

| 方案 | 價格 | 特點 |
|-----|------|------|
| Hobby | $5/月 | 更多執行時間、優先支援 |
| Pro | $20/月 | 團隊協作、更高資源 |
| Enterprise | 聯繫銷售 | 專屬支援、SLA 保證 |

---

## 自動化部署（CI/CD）

### GitHub Actions 自動部署

Railway 已內建 GitHub 整合，每次 push 到 `main` 分支會自動觸發部署。

**可選**: 創建 `.github/workflows/deploy.yml` 進行更細緻的控制。

---

## 監控與維護

### 查看應用狀態

```bash
# Railway CLI
railway status

# 查看資源使用
railway resources

# 查看部署歷史
railway deployments
```

### 重啟應用

```bash
# 透過 CLI
railway restart

# 或在 Dashboard 中
Settings > Restart Deployment
```

### 回滾部署

```bash
# 查看部署歷史
railway deployments

# 回滾到特定版本
railway rollback <deployment-id>
```

---

## 安全最佳實踐

### ✅ DO（建議做）

1. **環境變數管理**
   - ✅ 使用 Railway Variables 儲存敏感資訊
   - ✅ 不要在代碼中硬編碼 API Keys

2. **訪問控制**
   - ✅ 考慮添加基本認證（Streamlit 支援）
   - ✅ 使用 Railway 的 Private Networking（付費功能）

3. **監控**
   - ✅ 定期檢查部署日誌
   - ✅ 設置 Railway 通知（部署失敗時）

### ❌ DON'T（不要做）

1. **安全漏洞**
   - ❌ 不要上傳 `.env` 到 GitHub
   - ❌ 不要在 commit 訊息中包含敏感資訊
   - ❌ 不要使用弱密碼/簡單 API Keys

2. **效能問題**
   - ❌ 不要在 Railway 上運行大量計算（改用本地/雲端）
   - ❌ 不要儲存大量數據（Railway 儲存限制）

---

## 快速參考命令

```bash
# 登入 Railway
railway login

# 連結專案
railway link

# 部署
railway up

# 查看日誌
railway logs

# 查看狀態
railway status

# 重啟
railway restart

# 打開應用
railway open

# 查看環境變數
railway vars

# 設置環境變數
railway vars set FINLAB_API_KEY=your_key_here
```

---

## 相關資源

- **Railway 官方文檔**: https://docs.railway.app/
- **Railway CLI 文檔**: https://docs.railway.app/develop/cli
- **Streamlit 部署指南**: https://docs.streamlit.io/deploy
- **KevinRule GitHub**: https://github.com/AndyKauo/KevinRule
- **KevinRule 開發者指南**: [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md)

---

## 📞 支援

如有問題：
1. 查看 [故障排除](#故障排除) 章節
2. 檢查 Railway 日誌: `railway logs`
3. 查看 GitHub Issues: https://github.com/AndyKauo/KevinRule/issues

---

**部署愉快！** 🚀

*最後更新: 2025-10-28*
