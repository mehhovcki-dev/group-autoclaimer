import os
from aiosonic import HTTPClient, HttpResponse

async def verify_version():
    headers={
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    client = HTTPClient()
    response: HttpResponse = await client.get(
        "https://api.github.com/repos/mehhovcki-dev/mehhovcki-autoclaimer/branches/main", 
        headers=headers
    )

    if response.ok:
        latest_github_version = response.json()['commit']['sha']
    else:
        return False
    
    if os.path.exists("config/version.txt"):
        with open("config/version.txt", "r") as f:
            current_version = f.read()
    else:
        return False

    if current_version != "":
        if current_version == latest_github_version:
            return True
        else:
            return False
    else:
        f.close()
        with open("config/version.txt", "w") as f:
            f.write(latest_github_version)

        return True