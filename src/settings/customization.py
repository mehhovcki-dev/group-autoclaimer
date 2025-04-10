import pyfiglet
import os
from datetime import datetime
from rgbprint import gradient_print

visual_settings = {}

def print_alignment(lines, alignment='center', start_color=None, end_color=None, end="\n"):
    try:
        width = os.get_terminal_size().columns
    except Exception:
        width = 80

    if isinstance(lines, str):
        lines = [lines]

    for line in lines:
        if alignment == 'left':
            padding = 0
        elif alignment == 'center':
            padding = (width - len(line)) // 2
        elif alignment == 'right':
            padding = width - len(line)
        else:
            raise ValueError(f"Invalid alignment: {alignment}")

        full_line = " " * padding + line
        gradient_print(full_line, start_color=start_color, end_color=end_color, end=end)

def introduction(visual: dict, username, id, time, users, channels):
    global visual_settings
    logo = visual["console"]["logo"]
    enable_ascii = logo["ascii"]
    logo_font = logo["font"]
    logo_text = logo["text"]

    visual_settings = visual
    colors = visual["console"]["colors"]
    start = colors["info"]["color1"]
    end = colors["info"]["color2"]
    should_gradient = colors["gradient"]

    text = visual["console"]["text"]
    show_console_time = text["consoleTime"]
    console_time_format = text["timeFormat"]
    console_allignment = text["alignment"]

    if enable_ascii:
        ascii_art = pyfiglet.figlet_format(logo_text, font=logo_font, width=os.get_terminal_size().columns)
    else:
        ascii_art = logo_text
    
    texts = [
        f"succesfully loaded in as {username} *({id})*",
        f"took {time} seconds to load in account",
        f"trusting {users} and claiming from {channels} channel(s)!",
        f"thank you for using mehhovcki group autoclaimer! <3"
    ]

    if show_console_time:
        now = datetime.now()
        if console_time_format == "12h":
            time = now.strftime("%I:%M:%S %p")
        else:
            time = now.strftime("%H:%M:%S")
            
        for count, item in enumerate(texts):
            if console_allignment != "right":
                texts[count] = f"[{time}] {item}"
            else:
                texts[count] = f"{item} [{time}]"

    lines = ascii_art.splitlines() + texts
    print_alignment(lines,
                    console_allignment,
                    start_color=start,
                    end_color=end if should_gradient else start)

def log_info(text, level, end="\n"):
    settings = visual_settings["console"]
    level_config = settings["colors"][level]
    text_settings = settings["text"]
    
    if text_settings["consoleTime"]:
        now = datetime.now()
        time_format = "%I:%M:%S %p" if text_settings["timeFormat"] == "12h" else "%H:%M:%S"
        time_str = now.strftime(time_format)
        
        text = (f"{text} [{time_str}]" if text_settings["alignment"] == "right" 
                else f"[{time_str}] {text}")
    print_alignment(
        text, 
        text_settings["alignment"], 
        start_color=level_config["color1"], 
        end_color=level_config["color2"] if settings["colors"]["gradient"] else level_config["color1"],
        end=end
    )
