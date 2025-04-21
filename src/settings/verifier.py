import requests

def verify_version():
    try:
        request = requests.get("https://raw.githubusercontent.com/mehhovcki-dev/group-autoclaimer/refs/heads/main/config/version.txt")
        if request.status_code == 200:
            latest_version = request.text.split("\n")[0]
            change_log = request.text.split("\n")[1:]

            with open("config/version.txt", "r") as file:
                current_version = file.read().split("\n")[0]

            if latest_version != current_version:
                return False, change_log
    except Exception as e:
        print(e)
        pass
    return True, ""
