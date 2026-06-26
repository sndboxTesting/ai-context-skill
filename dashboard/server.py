#!/usr/bin/env python3
import os
import sys
import logging
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# Ensure widgets are importable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from widgets.goal_status import get_active_goals
from widgets.agent_activity import get_agent_activity
from widgets.memory_health import get_memory_health
from widgets.mcp_status import get_mcp_status
from widgets.anticipation import get_suggestions
from widgets.autolab_status import get_autolab_status

app = FastAPI(title="SuneelWorkSpace Live Dashboard")

# Mount static folder
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")), name="static")

# Ensure logs dir exists
log_dir = "/Users/MAC/SuneelWorkSpace/agent-system/logs"
os.makedirs(log_dir, exist_ok=True)

# Configure logging
logging.basicConfig(
    filename=os.path.join(log_dir, "dashboard.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Serve index.html
@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "<h1>Dashboard UI Not Found</h1>"

# JSON APIs
@app.get("/api/goals")
async def api_goals():
    return get_active_goals()

@app.get("/api/agent")
async def api_agent():
    return get_agent_activity()

@app.get("/api/memory")
async def api_memory():
    return get_memory_health()

@app.get("/api/mcp")
async def api_mcp():
    return get_mcp_status()

@app.get("/api/anticipation")
async def api_anticipation():
    return get_suggestions()[:3]  # Return top 3

@app.get("/api/autolab")
async def api_autolab():
    return get_autolab_status()

@app.get("/api/health")
async def api_health():
    health = get_memory_health()
    # Compute simple score: start at 100, deduct 10 per warning, 30 per error
    score = 100 - (health.get("total_errors", 0) * 30) - (health.get("total_warnings", 0) * 10)
    score = max(0, min(100, score))
    return {"score": score, "status": health.get("status", "healthy")}

# HTMX HTML Widgets
@app.get("/widgets/goals", response_class=HTMLResponse)
async def widget_goals():
    goals = get_active_goals()
    if not goals:
        return "<div class='no-data'>No active goals in progress.</div>"
    
    html = "<ul class='goals-list'>"
    for g in goals:
        priority_class = f"priority-{g['priority'].lower()}"
        html += f"""
        <li class="goal-item">
            <div class="goal-header">
                <span class="goal-title">{g['title']}</span>
                <span class="badge {priority_class}">{g['priority']}</span>
            </div>
            <div class="goal-desc">{g['description']}</div>
            <div class="goal-meta">ID: {g['id']} | Created: {g['created_at'][:10] if g['created_at'] else 'N/A'}</div>
        </li>
        """
    html += "</ul>"
    return html

@app.get("/widgets/agent", response_class=HTMLResponse)
async def widget_agent():
    activity = get_agent_activity()
    status_class = "status-active" if activity["status"] == "active" else "status-idle"
    return f"""
    <div class="agent-card">
        <div class="agent-info">
            <span class="label">Active Agent:</span>
            <span class="value">{activity['active_agent']}</span>
        </div>
        <div class="agent-info">
            <span class="label">Session ID:</span>
            <span class="value font-mono">{activity['session_id']}</span>
        </div>
        <div class="agent-info">
            <span class="label">Status:</span>
            <span class="value {status_class}">{activity['status'].upper()}</span>
        </div>
        <div class="agent-info block">
            <span class="label">Latest Action Summary:</span>
            <div class="summary-box">{activity['last_summary']}</div>
        </div>
    </div>
    """

@app.get("/widgets/memory", response_class=HTMLResponse)
async def widget_memory():
    health = get_memory_health()
    return f"""
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-num">{health['vector_count']}</div>
            <div class="stat-lbl">Vector Memory Chunks</div>
        </div>
        <div class="stat-card">
            <div class="stat-num">{health['total_errors']}</div>
            <div class="stat-lbl">Health Errors</div>
        </div>
        <div class="stat-card">
            <div class="stat-num">{health['total_warnings']}</div>
            <div class="stat-lbl">Health Warnings</div>
        </div>
    </div>
    <div class="meta-info">Last Checked: {health['last_checked']}</div>
    """

@app.get("/widgets/mcp", response_class=HTMLResponse)
async def widget_mcp():
    mcp = get_mcp_status()
    server_class = "status-online" if mcp["server_status"] == "online" else "status-offline"
    proxy_class = "status-online" if mcp["headroom_proxy"] == "online" else "status-offline"
    return f"""
    <div class="mcp-card">
        <div class="agent-info">
            <span class="label">MCP Server Status:</span>
            <span class="value {server_class}">{mcp['server_status'].upper()}</span>
        </div>
        <div class="agent-info">
            <span class="label">Headroom Proxy:</span>
            <span class="value {proxy_class}">{mcp['headroom_proxy'].upper()}</span>
        </div>
        <div class="agent-info">
            <span class="label">Mapped Resources:</span>
            <span class="value font-mono">{mcp['total_resources']}</span>
        </div>
        <div class="agent-info">
            <span class="label">Last Re-indexed:</span>
            <span class="value text-sm">{mcp['last_reindex'][:19] if mcp['last_reindex'] else 'N/A'}</span>
        </div>
    </div>
    """

@app.get("/widgets/anticipation", response_class=HTMLResponse)
async def widget_anticipation():
    sugs = get_suggestions()[:3]
    if not sugs:
        return "<div class='no-data'>No execution suggestions ready.</div>"
    
    html = "<ul class='sug-list'>"
    for s in sugs:
        priority_class = f"priority-{s['priority'].lower()}"
        html += f"""
        <li class="sug-item">
            <div class="sug-header">
                <span class="badge {priority_class}">{s['priority']}</span>
                <span class="sug-score">Confidence: {s['score']}</span>
            </div>
            <div class="sug-desc">{s['description']}</div>
        </li>
        """
    html += "</ul>"
    return html

@app.get("/widgets/health", response_class=HTMLResponse)
async def widget_health():
    health = get_memory_health()
    score = 100 - (health.get("total_errors", 0) * 30) - (health.get("total_warnings", 0) * 10)
    score = max(0, min(100, score))
    
    color_class = "health-green"
    if score < 70:
        color_class = "health-red"
    elif score < 90:
        color_class = "health-yellow"
        
    return f"""
    <div class="health-container">
        <div class="health-ring {color_class}">
            <span class="health-score">{score}</span>
            <span class="health-percent">%</span>
        </div>
        <div class="health-status">System Condition: <strong class="{color_class}">{health['status'].upper()}</strong></div>
    </div>
    """

@app.get("/widgets/header", response_class=HTMLResponse)
async def widget_header():
    activity = get_agent_activity()
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""
    <div class="header-left">
        <h1>SuneelWorkSpace Live Control Center</h1>
        <span class="header-time">System Time: {time_str}</span>
    </div>
    <div class="header-right">
        <span class="last-agent-badge">Last Agent: {activity['active_agent']}</span>
    </div>
    """
