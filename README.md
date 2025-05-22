# 此程式使用gork產生
# ServerMonitorExporter
監控特定處理程序 EXPORTER

# 使用前操作：
使用powershell開啟windows 防火牆log記錄功能  Set-NetFirewallProfile -Profile domain,public,private -LogAllowed false -LogBlocked true

設定 exporter 的 windows防火牆規則(預設8911 port)

可使用nssm掛載成服務(InstallToService.bat已包含開啟防火牆功能)

# 功能
監控特定處理程序 cpu、ram 使用率及 ports 的連線數
監控每日防火牆阻擋次數，每日00:00重計次數


# prometheus 指標
cg_firewall_drop_total：當日防火牆 pfirewall.log 中的 DROP 記錄總數

cg_process_cpu_percent：處理程序 CPU 使用率 (%)

cg_process_memory_usage_bytes：處理程序記憶體使用量 (Bytes)

cg_process_disk_read_bytes_per_second：處理程序硬碟讀取速率 (Bytes/s)

cg_process_disk_write_bytes_per_second：處理程序硬碟寫入速率 (Bytes/s)

cg_port_connection_count：指定埠號的 TCP 連接數量


# 版本
### V1.1版
變更prometheus指標
預設 YAML 配置文件路徑

### v1.2版
新增處理程序即時讀寫指標

# 使用nssm註冊成服務
語法如批次檔
