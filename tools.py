"""Tools que Gemini llama para consultar BARCO y todos los servicios del VPS."""
import io
import os
import requests
import boto3
from botocore.client import Config

BASE    = os.environ.get("BARCO_BASE_URL", "http://your-vps-ip")
TIMEOUT = int(os.environ.get("BARCO_TIMEOUT", "8"))

MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
MINIO_PORT       = os.environ.get("MINIO_PORT", "30091")

# ── MinIO client ───────────────────────────────────────────────────────────────
def _minio():
    return boto3.client(
        "s3",
        endpoint_url=f"{BASE}:{MINIO_PORT}",
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )

# ── BARCO Trading ──────────────────────────────────────────────────────────────

def get_trading_status() -> dict:
    """Estado completo del trading: PnL, capital, precios en vivo, modo (LIVE/PAPER)."""
    try:
        r = requests.get(f"{BASE}:30835/api/status", timeout=TIMEOUT)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def get_trading_health() -> dict:
    """Health del sistema BARCO: ticks procesados, mercados activos."""
    try:
        r = requests.get(f"{BASE}:30835/health", timeout=TIMEOUT)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# ── VecFrachZ Señales ──────────────────────────────────────────────────────────

def get_all_signals() -> dict:
    """Todas las señales activas BUY/SELL/HOLD con confianza para BTC, ETH, SOL, BNB, XRP, AVAX."""
    try:
        r = requests.get(f"{BASE}:30818/signals", timeout=TIMEOUT)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def get_signal_for_symbol(symbol: str, price: float) -> dict:
    """Señal VecFrachZ para un símbolo específico con su precio actual.
    Args:
        symbol: símbolo sin USDT, ej: BTC, ETH, SOL, BNB, XRP, AVAX
        price: precio actual en USDT
    """
    try:
        r = requests.post(f"{BASE}:30818/price", json={"symbol": symbol, "price": price}, timeout=TIMEOUT)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def get_vecfrachz_health() -> dict:
    """Estado de VecFrachZ: alpha, theta, DFS, símbolos tracked, conexión Kafka."""
    try:
        r = requests.get(f"{BASE}:30818/health", timeout=TIMEOUT)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# ── Memory Search (Milvus) ─────────────────────────────────────────────────────

def search_memory(query: str, top_k: int = 5) -> dict:
    """Busca en la memoria semántica del sistema (320+ vectores en Milvus/fastembed).
    Args:
        query: pregunta o tema a buscar en memoria
        top_k: número de resultados (máximo 10)
    """
    try:
        r = requests.post(f"{BASE}:8901/search", json={"query": query, "top_k": min(top_k, 10)}, timeout=TIMEOUT)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def get_memory_health() -> dict:
    """Estado del sistema de memoria: vectores almacenados, backend, dimensiones."""
    try:
        r = requests.get(f"{BASE}:8901/health", timeout=TIMEOUT)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# ── SwarmOrchestrator ──────────────────────────────────────────────────────────

def run_market_analysis() -> dict:
    """Análisis completo de mercado via SwarmOrchestrator FASE 15: precios, grids, PnL."""
    try:
        r = requests.post(f"{BASE}:30814/run-workflow", json={"workflow": "market_analysis"}, timeout=15)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def get_swarm_health() -> dict:
    """Estado del SwarmOrchestrator: agentes registrados (aichat, aider), conexión Milvus."""
    try:
        r = requests.get(f"{BASE}:30814/health", timeout=TIMEOUT)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# ── OmniRoute ─────────────────────────────────────────────────────────────────

def route_query(query: str) -> dict:
    """Enruta una query por OmniRoute: clasifica intención y devuelve contexto de BARCO.
    Args:
        query: pregunta en lenguaje natural
    """
    try:
        r = requests.post(f"{BASE}:30816/route", json={"query": query, "context": ""}, timeout=TIMEOUT)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# ── Bridge AncloFlutter ────────────────────────────────────────────────────────

def send_notification(title: str, body: str) -> dict:
    """Envía notificación push al dispositivo AncloFlutter conectado.
    Args:
        title: título de la notificación
        body: mensaje de la notificación
    """
    try:
        r = requests.post(f"{BASE}:31900/notify", json={"title": title, "body": body}, timeout=TIMEOUT)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def get_bridge_status() -> dict:
    """Estado del bridge AncloFlutter: dispositivos conectados, tareas acumuladas."""
    try:
        r = requests.get(f"{BASE}:31900/health", timeout=TIMEOUT)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# ── InferAI Gateway ────────────────────────────────────────────────────────────

def get_inferai_status() -> dict:
    """Estado del gateway InferAI: keys activas, requests totales."""
    try:
        r = requests.get(f"{BASE}:30815/health", timeout=TIMEOUT)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# ── Ancora — Memoria de agentes ───────────────────────────────────────────────

def ancora_get_context() -> dict:
    """Lee el contexto y memoria completa del sistema de agentes (Ancora).
    Contiene observaciones, hechos y ciclos de agentes guardados."""
    try:
        r = requests.get(f"{BASE}:31437/context", timeout=TIMEOUT)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def ancora_get_recent() -> dict:
    """Obtiene las observaciones más recientes del sistema: code graphs, ciclos de agentes, hechos."""
    try:
        r = requests.get(f"{BASE}:31437/observations/recent", timeout=TIMEOUT)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def ancora_search(query: str) -> dict:
    """Busca en la memoria de agentes (Ancora) por texto.
    Args:
        query: término o frase a buscar en las observaciones guardadas
    """
    try:
        r = requests.get(f"{BASE}:31437/search", params={"q": query}, timeout=TIMEOUT)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def ancora_add_observation(content: str, title: str = "", obs_type: str = "fact") -> dict:
    """Guarda una nueva observación en la memoria del sistema de agentes (Ancora).
    Args:
        content: contenido de la observación a guardar
        title: título opcional de la observación
        obs_type: tipo — fact, event, code, analysis (default: fact)
    """
    try:
        r = requests.post(f"{BASE}:31437/observations",
            json={"title": title, "content": content, "type": obs_type, "workspace": "default"},
            timeout=TIMEOUT)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# ── MinIO — Almacenamiento de archivos ────────────────────────────────────────

def minio_list_buckets() -> dict:
    """Lista todos los buckets de almacenamiento disponibles en MinIO.
    Buckets: sitios-web, dada-trading, dify, emailpay, k3s-backups, vecfrachz-backup"""
    try:
        s = _minio()
        buckets = [b["Name"] for b in s.list_buckets()["Buckets"]]
        return {"buckets": buckets}
    except Exception as e:
        return {"error": str(e)}

def minio_list_objects(bucket: str, prefix: str = "") -> dict:
    """Lista archivos dentro de un bucket de MinIO.
    Args:
        bucket: nombre del bucket (sitios-web, dada-trading, dify, emailpay, etc.)
        prefix: carpeta o prefijo opcional para filtrar (ej: 'barco/', 'GHT-1/')
    """
    try:
        s = _minio()
        resp = s.list_objects_v2(Bucket=bucket, Prefix=prefix)
        objects = [{"key": o["Key"], "size": o["Size"]} for o in resp.get("Contents", [])]
        return {"bucket": bucket, "objects": objects, "count": len(objects)}
    except Exception as e:
        return {"error": str(e)}

def minio_upload_webpage(html_content: str, filename: str, bucket: str = "sitios-web") -> dict:
    """Crea y sube una página web (HTML) a MinIO. La página queda publicada en la URL pública.
    Args:
        html_content: contenido HTML completo de la página
        filename: nombre del archivo con extensión .html (ej: 'guacalita.html', 'barco/nueva.html')
        bucket: bucket destino (default: sitios-web)
    """
    try:
        s = _minio()
        body = html_content.encode("utf-8")
        s.put_object(
            Bucket=bucket,
            Key=filename,
            Body=body,
            ContentType="text/html; charset=utf-8",
            ContentLength=len(body),
        )
        url = f"{BASE}:30091/{bucket}/{filename}"
        return {"ok": True, "url": url, "bucket": bucket, "key": filename, "size": len(body)}
    except Exception as e:
        return {"error": str(e)}

def minio_upload_text(content: str, filename: str, bucket: str = "sitios-web") -> dict:
    """Sube texto plano, JSON, Markdown u otro archivo de texto a MinIO.
    Args:
        content: contenido del archivo
        filename: nombre con extensión (ej: 'reporte.md', 'data.json')
        bucket: bucket destino (default: sitios-web)
    """
    try:
        s = _minio()
        body = content.encode("utf-8")
        s.put_object(Bucket=bucket, Key=filename, Body=body, ContentLength=len(body))
        url = f"{BASE}:30091/{bucket}/{filename}"
        return {"ok": True, "url": url, "bucket": bucket, "key": filename}
    except Exception as e:
        return {"error": str(e)}

def minio_read_object(bucket: str, key: str) -> dict:
    """Lee el contenido de un archivo guardado en MinIO.
    Args:
        bucket: nombre del bucket
        key: ruta del archivo dentro del bucket
    """
    try:
        s = _minio()
        resp = s.get_object(Bucket=bucket, Key=key)
        content = resp["Body"].read().decode("utf-8", errors="replace")
        return {"bucket": bucket, "key": key, "content": content[:3000]}
    except Exception as e:
        return {"error": str(e)}

# ── Aider — Escritura de código ───────────────────────────────────────────────

def aider_code_task(task: str) -> dict:
    """Le pide a Aider (asistente de código IA) que realice una tarea de programación.
    Aider tiene acceso al workspace del servidor y puede crear, editar y ejecutar código.
    Args:
        task: descripción clara de lo que debe hacer (ej: 'create a Python script that calculates fibonacci', 'fix the bug in trading_utils.py')
    """
    try:
        r = requests.post(f"{BASE}:30808/code-task",
            json={"task": task},
            timeout=120)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def aider_run_tests() -> dict:
    """Le pide a Aider que ejecute los tests del workspace actual y reporte resultados."""
    try:
        r = requests.post(f"{BASE}:30808/run-tests", json={}, timeout=30)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# ── Mapa de todas las tools disponibles ───────────────────────────────────────

ALL_TOOLS = [
    # BARCO Trading
    get_trading_status,
    get_trading_health,
    get_all_signals,
    get_signal_for_symbol,
    get_vecfrachz_health,
    # Memory & Intelligence
    search_memory,
    get_memory_health,
    run_market_analysis,
    get_swarm_health,
    route_query,
    # AncloFlutter Bridge (send_notification removed — no active device connection)
    get_bridge_status,
    # InferAI (ya estaba abajo, se mantiene)
    get_inferai_status,
    # Ancora — Memoria de agentes
    ancora_get_context,
    ancora_get_recent,
    ancora_search,
    ancora_add_observation,
    # MinIO — Almacenamiento
    minio_list_buckets,
    minio_list_objects,
    minio_upload_webpage,
    minio_upload_text,
    minio_read_object,
    # Aider — Código
    aider_code_task,
    aider_run_tests,
]

TOOL_MAP = {fn.__name__: fn for fn in ALL_TOOLS}
