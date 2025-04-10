import asyncio
import time
import json
from aiosonic import HTTPClient, Proxy, HttpResponse
session = HTTPClient()

from src.settings.customization import log_info
from src.core.detections import detect
from src.core.request import send_webhook

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

def split_url(url):
    try:
        return int(url.split("/groups/")[1].split("/")[0])
    except (IndexError, ValueError):
        return None

async def get_group_id(message):
    sources = [
        message.content.split(" ")[0],
        *[embed.url for embed in message.embeds],
        *[embed.title for embed in message.embeds],
        *[embed.description for embed in message.embeds],
        *[field.value for embed in message.embeds for field in embed.fields],
        *[field.name for embed in message.embeds for field in embed.fields]
    ]
    
    for source in sources:
        if source and (".com/groups" in source or ".com/communities" in source):
            group_id = split_url(source)
            if group_id is not None:
                return group_id
    
    return None

async def response_handler(group_id, user_id, claim_time, join_request: HttpResponse, claim_request: HttpResponse, headers, retry = False):
    data = {
        "group_id": group_id,
        "time": format_time(claim_time),
        "join": {
            "status": join_request.status_code,
            "json": await join_request.json()
        },
        "claim": {
            "status": claim_request.status_code,
            "json": await claim_request.json()
        },
        "reason": ""
    }

    with open("config/visual.json", "r", encoding="utf-8") as f:
        content = json.load(f)
    visual = content["webhook"]["account"]["claim"]

    if claim_request.status_code == 200:
        data["reason"] = "success"
        webhook_payload = format_webhook_json(
            visual["success"].copy(),
            group_id=group_id,
            time=format_time(claim_time),
            link=f"https://www.roblox.com/groups/{group_id}/mehhovcki-group-autoclaimer"
        )
        await send_webhook(webhook_payload)
        await detect(
            group_id,
            user_id,
            format_time(claim_time),
            headers
        )
    else:
        if claim_request.status_code in [400, 403, 500]:
            if claim_request.status_code == 403:
                reason = await claim_request.json()
                if reason["errors"][0]["code"] == 18:
                    new_claim = await attempt(group_id, headers)
                    if new_claim and not retry:
                        return await response_handler(group_id, user_id, claim_time, join_request, new_claim, headers, True)
                    data["reason"] = "roblox didn't like you"
                else:
                    data["reason"] = "got claimed already"
            else:
                data["reason"] = "got claimed already"
        elif claim_request.status_code == 429:
            data["reason"] = "account is ratelimited"
        elif claim_request.status_code == 401:
            data["reason"] = "got logged out"
        elif claim_request.status_code == 400:
            data["reason"] = "invalid group id"
        else:
            if join_request.status_code in [400, 403, 500]:
                data["reason"] = "got joined already"
            elif join_request.status_code == 429:
                data["reason"] = "account is ratelimited"
            elif join_request.status_code == 401:
                data["reason"] = "got logged out"
            elif join_request.status_code == 400:
                data["reason"] = "invalid group id"
            else:
                data["reason"] = "unknown reason"

        webhook_payload = format_webhook_json(
            visual["fail"].copy(),
            group_id=group_id, 
            time=format_time(claim_time),
            link=f"https://www.roblox.com/groups/{group_id}/mehhovcki-group-autoclaimer",
            status=data["reason"]
        )
        await send_webhook(webhook_payload)

    return data
    
async def attempt(group_id: int, headers: dict):
    session.proxy = None
    claim_request = None
    for i in range(1250):
        try:
            claim_request = await session.post(
                f"https://groups.roblox.com/v1/groups/{group_id}/claim-ownership", 
                json={}, 
                headers=headers
                # proxies=proxies
            )
        except Exception as e:
            print(e)
            pass
        i += 1
        log_info(f"trying to claim {group_id}, attempt #{i + 1} ({claim_request.status_code})", "debug", "\r")
        if claim_request:
            if claim_request.status_code == 200:
                log_info("succesfully claimed on reattempt!", "debug")
                return claim_request
            elif claim_request.status_code == 429:
                log_info("failed to claim on reattempt.", "debug")
                return claim_request
            elif claim_request.status_code == 403:
                data = await claim_request.json()
                if data.get("errors") != None:
                    error: dict = data.get("errors")
                    if error != None:
                        message: str = error[0].get("message")

                        if message == "This group already has an owner":
                            return claim_request
                        elif "Challenge" in message:
                            return claim_request

# async def request_join(group_id, headers, proxies):
#     if proxies != {}:
#         selected = proxies["http"]
#         auth, ip = selected.split("@")
#         session = HTTPClient(proxy=Proxy(
#             f"http://{ip}",
#             auth.replace("http://", "")
#         ))
#     else:
#         session = HTTPClient()
#     try:
#         begin = time.time()
#         request = await session.post(
#             f"https://groups.roblox.com/v1/groups/{group_id}/users", 
#             json={"sessionId": "", "redemptionToken": ""}, 
#             headers=headers,
#             verify=True
#         )
#         end = time.time()
#     except:
#         return await request_join(group_id, headers, proxies)
#     return request, end - begin

# async def request_claim(group_id, headers):
#     session = HTTPClient()
#     await asyncio.sleep(0.12)
#     try:
#         begin = time.time()
#         request = await session.post(
#             f"https://groups.roblox.com/v1/groups/{group_id}/claim-ownership", 
#             headers=headers,
#             verify=True
#         )
#         end = time.time()
#     except:
#         return await request_claim(group_id, headers)
#     return request, end - begin

# async def claim_group(user_id: int, group_id: int, headers: dict, proxies: dict = {}):
#     responses = await asyncio.gather(
#         request_join(group_id, headers, proxies),
#         request_claim(group_id, headers)
#     )

#     join_request = responses[0][0]
#     claim_request = responses[1][0]
#     claim_time = responses[0][1] - responses[1][1]
#     data = await response_handler(group_id, user_id,  claim_time, join_request, claim_request, headers)
#     return data

async def claim_group(user_id: int, group_id: int, headers: dict, proxies: dict = {}):
    if proxies != {}:
        selected = proxies["http"]
        auth, ip = selected.split("@")
        session.proxy = Proxy(
            f"http://{ip}",
            auth.replace("http://", "")
        )
    
    begin = time.time()
    try:
        join_request = await session.post(
            f"https://groups.roblox.com/v1/groups/{group_id}/users", 
            json={"sessionId": "", "redemptionToken": ""}, 
            headers=headers,
            verify=True
        )
    except:
        return await claim_group(user_id, group_id, headers, proxies)
    try:
        session.proxy = None
        claim_request = await session.post(
            f"https://groups.roblox.com/v1/groups/{group_id}/claim-ownership", 
            headers=headers
        )
    except:
        return await claim_group(user_id, group_id, headers, proxies)
    end = time.time()

    claim_time = end - begin
    data = await response_handler(group_id, user_id,  claim_time, join_request, claim_request, headers)
    return data

async def mess_with_group(user_id: int, group_id: int, headers: dict, action: dict):

    session = HTTPClient()
    if action["action"] == "leave":
        response = await session.delete(f"https://groups.roblox.com/v1/groups/{group_id}/users/{user_id}", headers=headers)
    elif action["action"] == "shout":
        response = await session.patch(f"https://groups.roblox.com/v1/groups/{group_id}/status", json={"message": action["message"]}, headers=headers)
        # print(response.json())
        # print(response.status_code)
    
    return response.status_code
