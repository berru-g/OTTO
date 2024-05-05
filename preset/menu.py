import os
import sys
import subprocess

options = {
    "gmail_calendar": ["https://mail.google.com", "https://calendar.google.com"],
    "vscode_github": ["C:\\Program Files\\Microsoft VS Code\\Code.exe", "https://github.com"],
    "youtube": ["https://www.youtube.com"]
}

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in options:
        print("Choisissez une option valide :")
        for option in options:
            print(f"- {option}")
        return

    option = sys.argv[1]
    actions = options[option]

    if isinstance(actions, list):
        for action in actions:
            if action.startswith("http"):
                webbrowser.open(action)
            else:
                subprocess.Popen(action, shell=True)

if __name__ == "__main__":
    main()
