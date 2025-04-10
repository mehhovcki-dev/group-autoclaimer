import os
import random
import time
import aiohttp
import json as library
from datetime import datetime, timezone
from src.settings.customization import log_info
from src.core.request import send_webhook

def format_number(number) -> str:
    return f"{number:,}"

def format_webhook_json(data: dict, **kwargs) -> dict:
    if isinstance(data, dict):
        return {k: format_webhook_json(v, **kwargs) for k, v in data.items()}
    elif isinstance(data, list):
        return [format_webhook_json(item, **kwargs) for item in data]
    elif isinstance(data, str):
        return data.format(**{k: v for k, v in kwargs.items() if k in data})
    return data

async def detect(group_id, user_id, claim_time: str, headers: dict):
    async with aiohttp.ClientSession(headers=headers) as session:
        Dmembers, Drobux, Dpending, Dclothing, Dgames, Dvisits, Dugc = 0, 0, 0, 0, 0, 0, 0
        begin_time: float = time.time()
        try:
            async with session.get(f"https://groups.roblox.com/v1/groups/{group_id}") as group_response:
                group_data = await group_response.json()
                Dmembers = group_data.get('memberCount')
                group_name = group_data.get('name')
        except:
            Dmembers = "failed"

        async with session.get(f"https://economy.roblox.com/v1/groups/{group_id}/currency") as robux_response:
            json = await robux_response.json()
            Drobux = json.get('robux') or 0

        async with session.get(f"https://economy.roblox.com/v1/groups/{group_id}/revenue/summary/month") as pending_response:
            json = await pending_response.json()
            Dpending = json.get('pendingRobux') or 0 

        cursor = ""
        while cursor is not None:
            try:
                url = f"https://catalog.roblox.com/v1/search/items?category=Clothing&creatorName={group_name}&salesTypeFilter=1&limit=120&cursor={cursor}"
                async with session.get(url) as clothing_response:
                    json = await clothing_response.json()
                    Dclothing += len(json.get('data', []))
                    cursor = json.get("nextPageCursor", None)
            except:
                Dclothing = "failed"

        cursor = ""
        while cursor is not None:
            try:
                url = f"https://catalog.roblox.com/v1/search/items?category=Accessories&subcategory=Accessories&creatorName={group_name}&salesTypeFilter=1&limit=120&cursor={cursor}"
                async with session.get(url) as ugc_response:
                    json = await ugc_response.json()
                    Dugc += len(json.get('data', []))
                    cursor = json.get("nextPageCursor", None)
            except:
                Dugc = "failed"

        cursor = ""
        while cursor is not None:
            try:
                url = f"https://games.roblox.com/v2/groups/{group_id}/gamesV2?accessFilter=Public&cursor={cursor}&limit=50&sortOrder=Desc"
                async with session.get(url) as games_response:
                    json = await games_response.json()
                    if json.get('data'):
                        for game in json.get('data'):
                            Dgames += 1
                            Dvisits += game.get('placeVisits', 0)
                    cursor = json.get("nextPageCursor", None)
            except:
                Dgames = "failed"

        end_time: float = time.time()

        with open("config/config.json", "r", encoding="utf-8") as f:
            config = library.load(f)
        include_ping = False
        detections = config["detections"]

        if isinstance(Drobux, int) and int(Drobux) >= detections["funds"]:
            include_ping = True
        if isinstance(Dpending, int) and int(Dpending) >= detections["pending"]:
            include_ping = True
        if isinstance(Dmembers, int) and int(Dmembers) >= detections["members"]:
            include_ping = True
        if isinstance(Dclothing, int) and int(Dclothing) >= detections["clothing"]:
            include_ping = True
        if isinstance(Dgames, int) and int(Dgames) >= detections["games"]:
            include_ping = True
        if isinstance(Dvisits, int) and int(Dvisits) >= detections["visits"]:
            include_ping = True
        if isinstance(Dugc, int) and int(Dugc) >= detections["ugc"]:
            include_ping = True

        with open("config/visual.json", "r", encoding="utf-8") as f:
            content = library.load(f)
        webhook_payload = format_webhook_json(
            content["webhook"]["account"]["detection"],
            group_id=group_id,
            members=Dmembers,
            robux=Drobux,
            pending=Dpending,
            clothing=Dclothing,
            games=Dgames,
            visits=Dvisits,
            ugc=Dugc,
            claim_time=claim_time,
            detect_time=round(end_time - begin_time, 3),
            link=f"https://www.roblox.com/groups/{group_id}/mehhovcki-group-autoclaimer"
        )
        await send_webhook(webhook_payload)
        if include_ping:
            if os.path.exists("user_id.txt"):
                with open("user_id.txt", "r") as file:
                    await send_webhook({"content": f"<@{file.read()}>"})
        log_info(f"succesfully finished detections for {group_id} in {round(end_time - begin_time, 3)}!", "info")
        await session.close()