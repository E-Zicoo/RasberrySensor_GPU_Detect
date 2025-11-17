#(restart monitor.py)

- Operation 頁新增「重新啟動 monitor.py」按鈕
- 伺服器端提供 `/api/restart_monitor`，會：
  1) 嘗試讀取 `collector/monitor.pid` 殺掉舊行程
  2) `cd` 到 `COLLECTOR_DIR`（.env 設定或預設為專案下的 collector）
  3) 以背景行程啟動 `python3 monitor.py`，將 PID 寫入 `monitor.pid`，log 在 `monitor.log`

## 設定
- `.env` 內可設定：
  - `ENV_DB_PATH=/full/path/to/gpu.sqlite`
  - `COLLECTOR_DIR=/home/pi/topic_work/envsite4/collector`  # 設成你的 collector 絕對路徑

## 常用指令
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
sqlite3 gpu.sqlite < init_db.sql
python app.py
```

前往 `/operation`：
- 調整量測參數 → 儲存到 `config.json`
- 查看/重新啟動 monitor.py（會寫入 PID 與 log 檔）
