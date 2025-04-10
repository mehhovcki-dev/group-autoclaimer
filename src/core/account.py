import aiohttp
import json
import time
from src.core.request import send_webhook, return_token
index = -1

with open("config/accounts.txt", "r") as file:
    cookies = [cookie.strip() for cookie in file.readlines()]

if len(cookies) == 0:
    print("[ERROR] please add accounts to the file config/accounts.txt")
    exit(1)

with open("config/visual.json", "r", encoding="utf-8") as f:
    content = json.load(f)
switch_logging = content["webhook"]["account"]["logging"]

def format_webhook_json(data: dict, **kwargs) -> dict:
    if isinstance(data, dict):
        return {k: format_webhook_json(v, **kwargs) for k, v in data.items()}
    elif isinstance(data, list):
        return [format_webhook_json(item, **kwargs) for item in data]
    elif isinstance(data, str):
        return data.format(**{k: v for k, v in kwargs.items() if k in data})
    return data

def format_time(duration: float) -> str:
    if duration >= 1:
        return f"{duration:.2f}s"
    else:
        return f"{int(duration * 1000)}ms"

async def account_validation(session: aiohttp.ClientSession, cookie: str):
    try:
        response = await session.get(
            "https://users.roblox.com/v1/users/authenticated", 
            headers={"cookie": f".ROBLOSECURITY={cookie}"}, 
            timeout=15
        )

        if response.status == 200:
            data = await response.json()
            data["cookie"] = cookie

            return data
    except:
        return {}

async def trash_groups(session: aiohttp.ClientSession, data: dict):
    try:
        response = await session.get(
            f"https://groups.roblox.com/v1/users/{data['id']}/groups/roles?includeLocked=true",
            headers={"cookie": f".ROBLOSECURITY={data['cookie']}"},
            timeout=15
        )

        if response.status == 200:
            data = await response.json()
            trash = [group["group"]["id"] for group in data["data"] if group["role"]["rank"] != 255]

            return len(trash) < 100, trash
    except:
        return False, []

async def switch():
    global index
    
    async with aiohttp.ClientSession() as session:
        while True:
            index += 1

            if index >= len(cookies):
                index = 0

            start_time: float = time.time()
            data = await account_validation(session, cookies[index - 1])
            if data != {}:
                headers = await return_token(data["cookie"])
                valid, trash = await trash_groups(session, data)

                if valid:
                    end_time: float = time.time()
                    webhook_payload = format_webhook_json(
                        switch_logging["switch"].copy(),
                        name=data["displayName"],
                        id=data["id"],
                        time=format_time(end_time - start_time)
                    )

                    data["time"] = format_time(end_time - start_time)
                    await send_webhook(webhook_payload)
                    return headers, data, trash
