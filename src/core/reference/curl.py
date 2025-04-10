import asyncio
import time
import json
from curl_cffi import requests

session = requests.Session(impersonate="chrome")
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

async def response_handler(group_id: int, user_id: int, time: float, join: requests.Response, claim: requests.Response, headers: dict, retry: bool = False):
    data = {
        "group_id": group_id,
        "time": format_time(time),
        "join": {
            "status": join.status_code,
            "json": join.json()
        },
        "claim": {
            "status": claim.status_code,
            "json": claim.json()
        },
        "reason": ""
    }
    with open("config/visual.json", "r", encoding="utf-8") as f:
        content = json.load(f)
    
    visual = content["webhook"]["account"]["claim"]

    if claim.status_code == 200:
        data["reason"] = "success"
        webhook_payload = format_webhook_json(
            visual["success"].copy(),
            group_id=group_id,
            time=format_time(time),
            link=f"https://www.roblox.com/groups/{group_id}/mehhovcki-group-autoclaimer"
        )
        await send_webhook(webhook_payload)
        await detect(
            group_id,
            user_id,
            format_time(time),
            headers
        )
    else:
        if claim.status_code in [400, 403, 500]:
            if claim.status_code == 403:
                reason = claim.json()
                if reason["errors"][0]["code"] == 18:
                    new_claim = await attempt(group_id, headers)
                    if new_claim and not retry:
                        return await response_handler(group_id, user_id, time, join, new_claim, headers, True)
                    data["reason"] = "roblox didn't like you"
                else:
                    data["reason"] = "got claimed already"
            else:
                data["reason"] = "got claimed already"
        elif claim.status_code == 429:
            data["reason"] = "account is ratelimited"
        elif claim.status_code == 401:
            data["reason"] = "got logged out"
        elif claim.status_code == 400:
            data["reason"] = "invalid group id"
        else:
            if join.status_code in [400, 403, 500]:
                data["reason"] = "got joined already"
            elif join.status_code == 429:
                data["reason"] = "account is ratelimited"
            elif join.status_code == 401:
                data["reason"] = "got logged out"
            elif join.status_code == 400:
                data["reason"] = "invalid group id"
            else:
                data["reason"] = "unknown reason"

        webhook_payload = format_webhook_json(
            visual["fail"].copy(),
            group_id=group_id, 
            time=format_time(time),
            link=f"https://www.roblox.com/groups/{group_id}/mehhovcki-group-autoclaimer",
            status=data["reason"]
        )
        await send_webhook(webhook_payload)

    # if join.status_code == 200:
    #     if claim.status_code == 200:
    #         data["reason"] = "success"
    #         webhook_payload = visual["success"].copy()
    #         webhook_payload["content"] = webhook_payload["content"].format(
    #             time=format_time(time), 
    #             group_id=group_id
    #         )
    #         await send_webhook(webhook_payload)
    #         await detect(
    #             group_id,
    #             user_id,
    #             format_time(time),
    #             headers 
    #         )
    #     else:
    #         if claim.status_code in [400, 403, 500]:
    #             data["reason"] = "got claimed already"
    #         elif claim.status_code == 429:
    #             data["reason"] = "account is ratelimited"
    #         elif claim.status_code == 401:
    #             data["reason"] = "got logged out"
    #         elif claim.status_code == 400:
    #             data["reason"] = "invalid group id"
    #         elif claim.status_code == 404:
    #             data["reason"] = "group not found? weird"
    #         else:
    #             data["reason"] = f"got unknown response code from roblox on claim. status code: {claim.status_code}"
            
    #         webhook_payload = visual["fail"].copy()
    #         webhook_payload["content"] = webhook_payload["content"].format(
    #             group_id=group_id, 
    #             time=format_time(time), 
    #             status=data["reason"]
    #         )
    #         await send_webhook(webhook_payload)
    # else:
    #     if join.status_code == 403:
    #         error: dict = join.json().get("errors")
    #         if error != None:
    #             message: str = error[0].get("message")

    #             if message == "You cannot join a closed group.":
    #                 data["reason"] = "group is closed"
    #             elif message == "You are already in the maximum number of groups.":
    #                 data["reason"] = "account is full"
    #             elif "Challenge" in message:
    #                 data["reason"] = "account is flagged"
    #         else:
    #             data["reason"] = "couldn't get reason. didn't got an error message. weird?"
    #     elif join.status_code == 409:
    #         pass
    #     elif join.status_code == 429:
    #         data["reason"] = "account is ratelimited"
    #     elif join.status_code == 401:
    #         data["reason"] = "got logged out"
    #     elif join.status_code == 400:
    #         data["reason"] = "invalid group id"
    #     elif join.status_code == 404:
    #         data["reason"] = "group not found? weird"
    #     else:
    #         data["reason"] = f"got unknown response code from roblox on join. {join.status_code}"
        
    #     webhook_payload = visual["fail"].copy()
    #     webhook_payload["content"] = webhook_payload["content"].format(
    #         group_id=group_id, 
    #         time=format_time(time), 
    #         status=data["reason"]
    #     )
    #     await send_webhook(webhook_payload)

    return data

### THIS IS REALLY BAD; unreliable, shitcoded and just stinks. i need to find better way to do this ###
async def attempt(group_id: int, headers: dict):
    claim_request: requests.Response = None
    for i in range(1250):
        try:
            claim_request = session.post(
                f"https://groups.roblox.com/v1/groups/{group_id}/claim-ownership", 
                json={}, 
                headers=headers,
                # proxies=proxies
            )
        except:
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
                if claim_request.json().get("errors") != None:
                    error: dict = claim_request.json().get("errors")
                    if error != None:
                        message: str = error[0].get("message")

                        if message == "This group already has an owner":
                            return claim_request
                        elif "Challenge" in message:
                            return claim_request

async def request_claim(group_id, headers):
    await asyncio.sleep(0.07)
    try:
        begin = time.time()
        request = session.post(
            f"https://groups.roblox.com/v1/groups/{group_id}/claim-ownership", 
            headers=headers
        )
        end = time.time()
    except:
        return await request_claim(group_id, headers)
    return request, end - begin

async def request_join(group_id, headers, proxies):
    try:
        begin = time.time()
        request = session.post(
            f"https://groups.roblox.com/v1/groups/{group_id}/users", 
            json={"sessionId": "", "redemptionToken": ""}, 
            headers=headers,
            proxies=proxies
        )
        end = time.time()
    except:
        return await request_join(group_id, headers, proxies)
    return request, end - begin

async def claim_group(user_id: int, group_id: int, headers: dict, proxies: dict = {}):
    responses = await asyncio.gather(
        request_join(group_id, headers, proxies),
        request_claim(group_id, headers)
    )
    join_request: requests.Response = responses[0][0]
    claim_request: requests.Response = responses[1][0]
    claim_time = join_request[1] - claim_request[1]

    data = await response_handler(group_id,
                                user_id, 
                                claim_time,
                                join_request,
                                claim_request,
                                headers)
    return data


# async def claim_group(user_id: int, group_id: int, headers: dict, proxies: dict = {}):
#     begin_time: float = time.time()
#     try:
#         join_request: requests.Response = session.post(
#             f"https://groups.roblox.com/v1/groups/{group_id}/users", 
#             json={"sessionId": "", "redemptionToken": ""}, 
#             headers=headers,
#             proxies=proxies
#         )
#     except:
#         return await claim_group(user_id, group_id, headers, proxies)
#     try:
#         claim_request: requests.Response = session.post(
#             f"https://groups.roblox.com/v1/groups/{group_id}/claim-ownership", 
#             headers=headers,
#             # proxies=proxies
#         )
#     except:
#         return await claim_group(user_id, group_id, headers, proxies)
#     end_time: float = time.time()

#     data = await response_handler(group_id, user_id, end_time - begin_time, join_request, claim_request, headers)
#     return data

async def mess_with_group(user_id: int, group_id: int, headers: dict, action: dict):
    if action["action"] == "leave":
        response = session.delete(f"https://groups.roblox.com/v1/groups/{group_id}/users/{user_id}", headers=headers)
    elif action["action"] == "shout":
        response = session.patch(f"https://groups.roblox.com/v1/groups/{group_id}/status", json={"message": action["message"]}, headers=headers)
        # print(response.json())
        # print(response.status_code)
    
    return response.status_code
