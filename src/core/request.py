import asyncio
import regex
import random
import aiohttp
import json
from datetime import datetime
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from src.settings.customization import log_info

async def send_webhook(data: dict):
    with open("config/config.json", "r", encoding="utf-8") as f:
        content = json.load(f)
    webhooks = content["autoclaim"]["webhooks"]

    async with aiohttp.ClientSession() as session:
        for webhook in webhooks:
            await session.post(webhook, json=data)

async def return_token(cookie):
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Cookie": f"GuestData=UserID=-53928485; .ROBLOSECURITY={cookie}; RBXEventTrackerV2=CreateDate=11/19/2023 12:07:42 PM&rbxid=5189165742&browserid=200781876902;",
        "x-csrf-token": ""
    }

    async with aiohttp.ClientSession() as session:
        while True:
            response = await session.post("https://auth.roblox.com/v2/logout", headers=headers)
            if response.headers.get("x-csrf-token") != None:
                headers["x-csrf-token"] = response.headers.get("x-csrf-token")
                return headers

async def leave_groups(user_id, cookie):
    async with aiohttp.ClientSession() as session:
        headers = await return_token(cookie)
        if headers == None:
            return

        response = await session.get(
            f"https://groups.roblox.com/v1/users/{user_id}/groups/roles?includeLocked=true",
            headers=headers,
            timeout=15
        )

        for group in (await response.json())["data"]:
            if group["role"]["rank"] != 255:
                response = await session.delete(
                    f"https://groups.roblox.com/v1/groups/{group['group']['id']}/users/{user_id}",
                    headers=headers
                )

                headers = await return_token(cookie)
                log_info(f"left {group['group']['name']} ({group['group']['id']}) ({response.status})", "debug")
    # async with aiohttp.ClientSession() as session:
    #     cookies = headers["Cookie"].split("; ")
    #     for cookie in cookies:
    #         if ".ROBLOSECURITY" in cookie:
    #             cookie = cookie.split("=")[1]
    #             break

    #     if cookie == None:
    #         return
    
    #     response = await session.get(
    #         f"https://groups.roblox.com/v1/users/{user_id}/groups/roles?includeLocked=true",
    #         headers=headers,
    #         timeout=15
    #     )

    #     for group in (await response.json())["data"]:
    #         if group["role"]["rank"] != 255:
    #             response = await session.delete(
    #                 f"https://groups.roblox.com/v1/groups/{group['group']['id']}/users/{user_id}",
    #                 headers=headers
    #             )
    #             print(f"left {group['group']['name']} ({group['group']['id']}) ({response.status})")
    #             headers = await return_token(cookie)
    #             await asyncio.sleep(0.5)
