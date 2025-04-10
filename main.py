import asyncio
import selfcord
import os
import random
import time
import threading
import signal
from datetime import datetime, timedelta

try:
    import uvloop # type: ignore
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except:
    import winloop
    asyncio.set_event_loop_policy(winloop.EventLoopPolicy())

from src.core.account import switch
from src.core.request import leave_groups, return_token
from src.settings.settings import load_settings, load_visual_settings
from src.settings.customization import log_info, introduction
from src.settings.verifier import verify_version
from src.core.claimer import claim_group, mess_with_group, get_group_id

settings, visual = load_settings(), load_visual_settings()

autoclaim = settings["autoclaim"]
discord = settings["discord"]
client = selfcord.Client()

def update_headers():
    global headers, account_data

    while True:
        try:
            now = datetime.now()
            next_minute = now.replace(second=0, microsecond=0) + timedelta(seconds=30)
            wait_seconds = (next_minute - now).total_seconds()
            time.sleep(wait_seconds)
        except Exception as e:
            time.sleep(1)

        
        headers = asyncio.run(return_token(account_data["cookie"]))

@client.event
async def on_message(message: selfcord.Message):
    global headers, account_data
    if message.channel.id in autoclaim["channels"]:
        group_id = await get_group_id(message)
        if group_id is not None:
            data = await claim_group(account_data["id"], group_id, headers,
            settings["proxies"]["enabled"] and settings["proxies"]["proxies"] or {})

            if data["join"]["status"] != 200:
                if data["join"]["status"] == 429 or data["join"]["status"] == 401:
                    log_info("switching account", "warn")
                    headers, account_data, trash = await switch()
                    headers = await return_token(account_data["cookie"])
                    log_info("succesfully switched account", "warn")

            if data["claim"]["status"] != 200:
                if data["claim"]["status"] == 429 or data["claim"]["status"] == 401:
                    log_info("switching account", "warn")
                    headers, account_data, trash = await switch()
                    headers = await return_token(account_data["cookie"])
                    log_info("succesfully switched account", "warn")
            
            print(data["join"]["status"], data["claim"]["status"], data["join"]["json"], data["claim"]["json"], data["reason"], data["time"])
            if data["join"]["status"] == 200 and data["claim"]["status"] == 200:
                log_info(f"succesfully claimed {group_id} in {data['time']} :D", "info")
                if autoclaim["shouts"]:
                    await mess_with_group(account_data["id"], group_id, headers, {"action": "shout", "message": random.choice(autoclaim["shoutsList"])})
            else:
                log_info(f"failed to claim {group_id} in {data['time']} because {data['reason']} :(", "warn")
                await mess_with_group(account_data["id"], group_id, headers, {"action": "leave"})

@client.event
async def on_ready():
    if not os.path.exists("user_id.txt"):
        with open("user_id.txt", "a") as file:
            file.write(str(client.user.id))
        file.close()

loop = asyncio.get_event_loop()
headers, account_data, trash = loop.run_until_complete(switch())

os.system("cls" if os.name == "nt" else "clear")
introduction(visual, account_data["displayName"], account_data["id"], account_data["time"], len(discord["trust"]), len(autoclaim["channels"]))
asyncio.run(leave_groups(account_data["id"], headers.get("Cookie").split(".ROBLOSECURITY=")[1].split(";")[0]))

isUpdated = asyncio.run(verify_version())
if not isUpdated:
    log_info("[!] WARNING, PLEASE TAKE ATTENTION! your version of mehhovcki autoclaimer v6 is out-of-date.", "warn")
    log_info("[!] please, visit [https://github.com/mehhovcki-dev/group-autoclaimer] to download the latest version.", "warn")

def handle_interrupt(signum, frame):
    log_info("exiting...", "info")
    if os.path.exists("user_id.txt"):
        os.remove("user_id.txt")
    os._exit(0)

if os.name == "nt":
    os.system(f"title mehhovcki group autoclaimer v6 :3")

signal.signal(signal.SIGINT, handle_interrupt)
signal.signal(signal.SIGTERM, handle_interrupt)

threading.Thread(target=update_headers).start()
client.run(discord["token"])#, log_handler=)
