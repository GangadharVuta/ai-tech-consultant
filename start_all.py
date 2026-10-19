import os
import sys
import time
import subprocess
import webbrowser
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

def run_services():
    print("=" * 80)
    print("  AI TECH CONSULTANT - ONE-COMMAND MULTI-SERVICE ORCHESTRATOR")
    print("=" * 80)
    print("Starting all 3 core tasks and unified UI dashboard...")

    processes = []

    try:
        # 1. Start Task 1: Knowledge Brain (Port 8001)
        print("\n[1/4] Starting Task 1 Knowledge Brain API on http://127.0.0.1:8001...")
        p_task1 = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8001"],
            cwd=str(ROOT_DIR / "task1-knowledge-brain")
        )
        processes.append(("Task 1 Knowledge Brain", p_task1))

        # 2. Start Task 2: Inbox Agent (Port 8002)
        print("[2/4] Starting Task 2 TypeScript Inbox Agent on http://127.0.0.1:8002...")
        # Check npm / npx
        npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
        p_task2 = subprocess.Popen(
            [npm_cmd, "start"],
            cwd=str(ROOT_DIR / "task2-inbox-agent")
        )
        processes.append(("Task 2 Inbox Agent", p_task2))

        # 3. Start Task 3: Meeting to Scope (Port 8003)
        print("[3/4] Starting Task 3 Meeting-to-Scope API on http://127.0.0.1:8003...")
        p_task3 = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8003"],
            cwd=str(ROOT_DIR / "task3-meeting-to-scope")
        )
        processes.append(("Task 3 Meeting-to-Scope", p_task3))

        # 4. Start Unified UI Dashboard (Port 8000)
        print("[4/4] Starting Unified System Dashboard on http://127.0.0.1:8000...")
        p_ui = subprocess.Popen(
            [sys.executable, "-m", "http.server", "8000"],
            cwd=str(ROOT_DIR / "ui")
        )
        processes.append(("Unified UI Dashboard", p_ui))

        # Wait for services to bind
        time.sleep(3)
        ui_url = "http://127.0.0.1:8000"
        print("\n" + "=" * 80)
        print(f"  ALL SYSTEMS ONLINE! Opening dashboard in browser: {ui_url}")
        print("  - Task 1 Knowledge Brain API: http://127.0.0.1:8001/docs")
        print("  - Task 2 Inbox Agent API:    http://127.0.0.1:8002/health")
        print("  - Task 3 Meeting to Scope:   http://127.0.0.1:8003/docs")
        print("  - Unified UI Dashboard:      http://127.0.0.1:8000")
        print("=" * 80)
        print("Press Ctrl+C to terminate all services safely.\n")

        webbrowser.open(ui_url)

        # Keep alive
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down all services gracefully...")
        for name, proc in processes:
            print(f"Terminating {name}...")
            proc.terminate()
        print("All processes closed. Goodbye!")

if __name__ == "__main__":
    run_services()
