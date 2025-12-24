# start_services.py
import subprocess
import sys
import os

def run_service(command, name):
    """Starts a service in a new terminal window."""
    print(f"Attempting to start {name}...")
    try:
        # For Windows, use 'start' to open a new command prompt
        if sys.platform == "win32":
            # Using 'cmd /k' ensures the window stays open after the command finishes
            subprocess.Popen(f'start "{name}" cmd /k {command}', shell=True)
        # For macOS/Linux, use 'xterm' or 'gnome-terminal' (requires installation)
        else:
            # This is a basic example; users might need to adjust based on their terminal
            subprocess.Popen(["xterm", "-e", command]) 
        print(f"✅ {name} is starting in a new window.")
    except Exception as e:
        print(f"❌ Failed to start {name}. Error: {e}")
        print(f"Please run the following command manually in a new terminal:\n  {command}")

if __name__ == "__main__":
    # Ensure the current working directory is the script's directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print("===========================================")
    print("LAUNCHING BACKEND MICROSERVICES")
    print("===========================================")

    # Command for Auth Service (Port 8001) with auto-reload
    auth_command = "python -m uvicorn backend.run:app --host 0.0.0.0 --port 8001 --reload"
    
    # Command for AI Service (Port 8007) with auto-reload
    ai_command = "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8007 --reload"

    # Start both services
    run_service(auth_command, "Auth Service (Port 8000)")
    run_service(ai_command, "AI Service (Port 8006)")

    print("\nAll services have been launched in separate terminal windows.")
    print("You can close this window.")
