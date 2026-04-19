
import os
import requests
from datetime import datetime
from flask import Flask, render_template, jsonify

app = Flask(__name__)

# GitHub API Configuration
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = "CzPhantom10/secure-devops-pipeline"
API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs"
API_KEY = "12345"

# Set up headers for GitHub API
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"


def fetch_workflow_runs():
    """
    Fetch workflow runs from GitHub API
    Returns: dict with latest run and last 5 runs
    """
    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("workflow_runs"):
            return {"error": "No workflow runs found", "latest": None, "runs": []}
        
        runs = data["workflow_runs"]
        
        # Extract latest run
        latest = runs[0] if runs else None
        
        # Extract last 5 runs
        last_five = runs[:5]
        
        return {
            "error": None,
            "latest": latest,
            "runs": last_five
        }
    except requests.exceptions.RequestException as e:
        return {
            "error": f"Failed to fetch workflow data: {str(e)}",
            "latest": None,
            "runs": []
        }


def calculate_security_score(conclusion):
    """
    Calculate security score based on pipeline status
    Returns: dict with score and color
    """
    if conclusion == "success":
        return {"score": 100, "color": "success"}
    elif conclusion == "failure":
        return {"score": 50, "color": "danger"}
    elif conclusion == "cancelled":
        return {"score": 60, "color": "warning"}
    else:  # in_progress
        return {"score": 75, "color": "info"}


def extract_failure_reason(run_data):
    """
    Extract failure reason from workflow run data
    Returns: failure reason string or default message
    """
    conclusion = run_data.get("conclusion", "")
    
    if conclusion == "failure":
        # Try to get detailed reason from run status
        name = run_data.get("name", "")
        head_branch = run_data.get("head_branch", "")
        
        # Return a descriptive failure message
        if "security" in name.lower() or "scan" in name.lower():
            return "Security scan detected vulnerabilities in the pipeline"
        elif "test" in name.lower():
            return "Test suite failed - code quality check did not pass"
        else:
            return "Hardcoded secret detected by security scanner"
    
    return None


def format_datetime(iso_string):
    """Convert ISO 8601 datetime to readable format"""
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return iso_string


def get_status_color(conclusion):
    """Return Bootstrap color class based on workflow conclusion"""
    if conclusion == "success":
        return "success"
    elif conclusion == "failure":
        return "danger"
    elif conclusion == "cancelled":
        return "warning"
    else:
        return "secondary"


@app.route("/")
def dashboard():
    """Render the DevSecOps Dashboard"""
    data = fetch_workflow_runs()
    
    latest_run = data.get("latest")
    runs = data.get("runs", [])
    error = data.get("error")
    
    # Calculate security score and get alert info from latest run
    security_score = None
    alert_type = None
    alert_message = None
    failure_reason = None
    
    if latest_run:
        conclusion = latest_run.get("conclusion", "in_progress")
        score_info = calculate_security_score(conclusion)
        security_score = score_info
        
        # Determine alert type and message
        if conclusion == "success":
            alert_type = "success"
            alert_message = "✅ All Systems Secure"
        elif conclusion == "failure":
            alert_type = "danger"
            alert_message = "🚨 SECURITY ALERT: Pipeline Failed"
            failure_reason = extract_failure_reason(latest_run)
    
    # Process runs for display
    processed_runs = []
    for run in runs:
        processed_runs.append({
            "name": run.get("name", "Unknown"),
            "status": run.get("conclusion", "in_progress"),
            "status_color": get_status_color(run.get("conclusion")),
            "created_at": format_datetime(run.get("created_at", "")),
            "updated_at": format_datetime(run.get("updated_at", "")),
            "run_number": run.get("run_number", "N/A")
        })
    
    latest_info = None
    if latest_run:
        latest_info = {
            "name": latest_run.get("name", "Unknown"),
            "status": latest_run.get("conclusion", "in_progress"),
            "status_color": get_status_color(latest_run.get("conclusion")),
            "created_at": format_datetime(latest_run.get("created_at", "")),
            "run_number": latest_run.get("run_number", "N/A")
        }
    
    return render_template(
        "index.html",
        latest=latest_info,
        runs=processed_runs,
        error=error,
        repo=GITHUB_REPO,
        security_score=security_score,
        alert_type=alert_type,
        alert_message=alert_message,
        failure_reason=failure_reason
    )


@app.route("/api/refresh")
def refresh_data():
    """API endpoint to refresh workflow data (for AJAX calls)"""
    data = fetch_workflow_runs()
    
    if data.get("error"):
        return jsonify({"error": data["error"]}), 500
    
    latest_run = data.get("latest")
    runs = data.get("runs", [])
    
    security_score = None
    alert_type = None
    alert_message = None
    failure_reason = None
    
    latest_info = None
    if latest_run:
        conclusion = latest_run.get("conclusion", "in_progress")
        score_info = calculate_security_score(conclusion)
        security_score = score_info
        
        # Determine alert type and message
        if conclusion == "success":
            alert_type = "success"
            alert_message = "✅ All Systems Secure"
        elif conclusion == "failure":
            alert_type = "danger"
            alert_message = "🚨 SECURITY ALERT: Pipeline Failed"
            failure_reason = extract_failure_reason(latest_run)
        
        latest_info = {
            "name": latest_run.get("name", "Unknown"),
            "status": latest_run.get("conclusion", "in_progress"),
            "status_color": get_status_color(latest_run.get("conclusion")),
            "created_at": format_datetime(latest_run.get("created_at", ""))
        }
    
    runs_list = []
    for run in runs:
        runs_list.append({
            "name": run.get("name", "Unknown"),
            "status": run.get("conclusion", "in_progress"),
            "created_at": format_datetime(run.get("created_at", "")),
            "run_number": run.get("run_number", "N/A")
        })
    
    return jsonify({
        "latest": latest_info,
        "runs": runs_list,
        "security_score": security_score,
        "alert_type": alert_type,
        "alert_message": alert_message,
        "failure_reason": failure_reason
    })


if __name__ == "__main__":
    app.run(debug=True, host="localhost", port=5000)