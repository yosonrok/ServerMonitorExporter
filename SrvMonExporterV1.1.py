from prometheus_client import start_http_server, Gauge
import time
import os
import psutil
from datetime import datetime
import yaml

# 功能
# 監控特定處理程序 cpu、ram 使用率及 ports 的連線數
# 監控每日防火牆阻擋次數，每日00:00重計次數
# V1.1版
# 變更prometheus指標
# 預設 YAML 配置文件路徑
CONFIG_FILE_PATH = 'config.yaml'


# 讀取 YAML 配置
def load_config():
    """讀取 YAML 配置文件"""
    try:
        with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
            if not config:
                raise ValueError("YAML 文件為空")
            return config
    except FileNotFoundError:
        print(f"錯誤：配置文件 {CONFIG_FILE_PATH} 不存在")
        return None
    except Exception as e:
        print(f"讀取 YAML 配置文件時發生錯誤：{e}")
        return None


# 定義 Prometheus 指標
def init_metrics(server_name):
    """初始化所有 Prometheus 指標"""
    metrics = {
        'drop_count': Gauge(
            'cg_firewall_drop_total',
            '當日防火牆 pfirewall.log 中的 DROP 記錄總數',
            ['server_name']
        ),
        'cpu_usage': Gauge(
            'cg_process_cpu_percent',
            '進程 CPU 使用率 (%)',
            ['server', 'process_name']
        ),
        'memory_usage': Gauge(
            'cg_process_memory_usage_bytes',
            '進程記憶體使用量 (Bytes)',
            ['server', 'process_name']
        ),
        'port_connection_count': Gauge(
            'cg_port_connection_count',
            '指定端口的 TCP 連接數量',
            ['server', 'port']
        )
    }
    return metrics


# 防火牆日誌文件路徑
LOG_FILE_PATH = r'C:\Windows\System32\LogFiles\Firewall\pfirewall.log'


def count_drop_entries():
    """讀取 pfirewall.log 文件並計算當日 DROP 動作的總數"""
    try:
        drop_count = 0
        current_date = datetime.now().strftime('%Y-%m-%d')

        if not os.path.exists(LOG_FILE_PATH):
            print(f"錯誤：日誌文件 {LOG_FILE_PATH} 不存在")
            return 0

        with open(LOG_FILE_PATH, 'r', encoding='utf-8') as file:
            for line in file:
                if line.startswith('#') or not line.strip():
                    continue
                fields = line.split()
                if len(fields) < 2:
                    continue
                log_date = fields[0]
                if ' DROP ' in line and log_date == current_date:
                    drop_count += 1
        return drop_count
    except Exception as e:
        print(f"讀取日誌文件時發生錯誤：{e}")
        return 0


def count_port_connections(port):
    """統計指定端口的 TCP 連接數"""
    count = 0
    for conn in psutil.net_connections(kind='inet'):
        if conn.laddr and conn.laddr.port == port:
            count += 1
    return count


def update_metrics(config, metrics):
    """更新所有 Prometheus 指標"""
    server_name = config.get('server_name', 'unknown')
    process_names = [p['name'] for p in config.get('monitor', {}).get('processes', [])]
    monitored_ports = config.get('monitor', {}).get('ports', [])

    # 防火牆 DROP 計數計數器
    firewall_counter = 0

    while True:
        # 更新防火牆指標（每 60 秒）
        if firewall_counter % 60 == 0:
            drop_count = count_drop_entries()
            metrics['drop_count'].labels(server_name=server_name).set(drop_count)
            print(f"已更新防火牆指標：當日 DROP 總數 = {drop_count} (伺服器：{server_name})")

        # 更新遊戲監控指標（每 5 秒）
        # 監控進程 CPU 和記憶體
        for proc_name in process_names:
            found = False
            for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_info']):
                if proc.info['name'] == proc_name:
                    found = True
                    metrics['cpu_usage'].labels(server=server_name, process_name=proc_name).set(
                        proc.cpu_percent(interval=0.1)
                    )
                    metrics['memory_usage'].labels(server=server_name, process_name=proc_name).set(
                        proc.info['memory_info'].rss
                    )
                    break
            if not found:
                metrics['cpu_usage'].labels(server=server_name, process_name=proc_name).set(0)
                metrics['memory_usage'].labels(server=server_name, process_name=proc_name).set(0)

        # 監控端口連接數
        for port in monitored_ports:
            connection_count = count_port_connections(port)
            metrics['port_connection_count'].labels(server=server_name, port=str(port)).set(connection_count)

        # 睡眠 5 秒，計數器增加
        time.sleep(5)
        firewall_counter += 5


if __name__ == '__main__':
    # 載入配置文件
    config = load_config()
    if not config:
        print("無法啟動 Exporter：缺少有效的 YAML 配置")
        exit(1)

    # 獲取端口（僅從 exporter.port 獲取，預設 8911）
    port = config.get('exporter', {}).get('port', 8911)
    server_name = config.get('server_name', 'unknown')

    # 初始化指標
    metrics = init_metrics(server_name)

    # 啟動 Prometheus Exporter
    print(f"正在啟動 Prometheus Exporter，監聽端口 {port}，伺服器名稱：{server_name}...")
    start_http_server(port)

    try:
        update_metrics(config, metrics)
    except KeyboardInterrupt:
        print("Exporter 已停止")