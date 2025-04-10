import json
import pyfiglet
import time

settings_file_location = "config/config.json"
visual_file_location = "config/visual.json"

def validate_settings(content: str):
    validation_begin = time.time()
    errors = []
    
    stripped = content.strip()
    if stripped.count('{') != stripped.count('}'):
        errors.append("Missing closing curly bracket")

    try:
        content = json.loads(content)
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON format: {str(e)}")
        return errors

    if 'discord' not in content:
        errors.append("Missing 'discord' section in configuration")
    else:
        discord = content['discord']
        if 'token' not in discord or not discord['token']:
            errors.append("Discord token cannot be empty")
        if 'prefix' not in discord or not discord['prefix']:
            errors.append("Discord prefix cannot be empty")
        if 'trust' in discord and not isinstance(discord['trust'], list):
            errors.append("Trust must be a list")
        if 'trustOwnerCommands' in discord and not isinstance(discord['trustOwnerCommands'], bool):
            errors.append("TrustOwnerCommands must be a boolean")

    if 'autoclaim' not in content:
        errors.append("Missing 'autoclaim' section in configuration")
    else:
        autoclaim = content['autoclaim']
        if 'channels' in autoclaim:
            if not isinstance(autoclaim['channels'], list):
                errors.append("Channels must be a list")
            elif not all(isinstance(channel, int) for channel in autoclaim['channels']):
                errors.append("All channels must be integers")
        if 'webhooks' in autoclaim:
            if not isinstance(autoclaim['webhooks'], list):
                errors.append("Webhooks must be a list")
        if 'shouts' in autoclaim and not isinstance(autoclaim['shouts'], bool):
            errors.append("Shouts must be a boolean")
        if 'shoutsList' in autoclaim:
            if not isinstance(autoclaim['shoutsList'], list):
                errors.append("ShoutsList must be a list")
            elif not all(isinstance(shout, str) for shout in autoclaim['shoutsList']):
                errors.append("All shouts must be strings")

    if 'proxies' not in content:
        errors.append("Missing 'proxies' section in configuration")
    else:
        proxies = content['proxies']
        if 'enabled' not in proxies or not isinstance(proxies['enabled'], bool):
            errors.append("Proxies enable must be a boolean")
        if 'proxies' in proxies:
            if not isinstance(proxies['proxies'], dict):
                errors.append("Proxies must be a dictionary")
            if proxies['proxies'] == True:
                if 'http' not in proxies['proxies'] or not proxies['proxies']['http']:
                    errors.append("HTTP proxy cannot be empty")
                if 'https' not in proxies['proxies'] or not proxies['proxies']['https']:
                    errors.append("HTTPS proxy cannot be empty")

    if 'detections' not in content:
        errors.append("Missing 'detections' section in configuration")
    else:        
        detections = content['detections']
        detection_fields = ['funds', 'pending', 'members', 'clothing', 'games', 'visits', 'ugc']
        
        for field in detection_fields:
            if field not in detections:
                errors.append(f"Missing {field} in detections")
            elif not isinstance(detections[field], (int, float)):
                errors.append(f"{field} must be a number")

    if 'logging' not in content:
        errors.append("Missing 'logging' section in configuration")
    else:
        logging = content['logging']
        logging_fields = ['enable', 'accountSwitch', 'claimData', 'discordHandler']
        for field in logging_fields:
            if field not in logging:    
                errors.append(f"Missing {field} in logging")
            elif not isinstance(logging[field], bool):
                errors.append(f"{field} must be a boolean")

    validation_end = time.time()
    print(f"[SETTINGS] validation took {validation_end - validation_begin:.2f} seconds")
    return errors

def validate_visual_settings(content: str):
    validation_begin = time.time()
    errors = []

    stripped = content.strip()
    if stripped.count('{') != stripped.count('}'):
        errors.append("Missing closing curly bracket")
    try:
        content = json.loads(content)
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON format: {str(e)}")
        return errors

    if 'console' not in content:
        errors.append("Missing 'console' section in visual settings")
    else:
        console = content['console']
        
        if 'text' not in console:
            errors.append("Missing 'text' in console settings")
        else:
            text = console['text']
            text_fields = ['consoleTime', 'timeFormat', 'alignment']
            for field in text_fields:
                if field not in text:
                    errors.append(f"Missing '{field}' in text settings")
            
            if 'consoleTime' in text and not isinstance(text['consoleTime'], bool):
                errors.append("consoleTime must be a boolean")
            
            if 'timeFormat' in text and text['timeFormat'] not in ["12h", "24h"]:
                errors.append(f"Unsupported time format: {text['timeFormat']}. Must be 12h or 24h")
            
            if 'alignment' in text and text['alignment'] not in ["left", "center", "right"]:
                errors.append(f"Unsupported alignment: {text['alignment']}. Must be left, center or right")

        if 'logo' not in console:
            errors.append("Missing 'logo' in console settings")
        else:
            logo = console['logo']
            if 'ascii' not in logo or not isinstance(logo['ascii'], bool):
                errors.append("Logo 'ascii' must be a boolean")
            
            if 'font' not in logo:
                errors.append("Missing 'font' in logo settings")
            elif logo['font'] not in pyfiglet.FigletFont.getFonts():
                errors.append(f"Unsupported font: {logo['font']}")
            if 'text' not in logo or not logo['text']:
                errors.append("Logo 'text' cannot be empty")

        if 'colors' not in console:
            errors.append("Missing 'colors' in console settings")
        else:
            colors = console['colors']
            
            if 'gradient' not in colors or not isinstance(colors['gradient'], bool):
                errors.append("Colors 'gradient' must be a boolean")
            
            color_sections = ['info', 'warn', 'error', 'debug', 'critical']
            for section in color_sections:
                if section not in colors:
                    errors.append(f"Missing '{section}' in colors")
                else:
                    color = colors[section]
                    if colors['gradient']:
                        if not color.get('color2'):
                            errors.append(f"{section} color2 cannot be empty when gradient is true")
                    else:
                        if not color.get('color1'):
                            errors.append(f"{section} color1 cannot be empty when gradient is false")

    if 'webhook' not in content:
        errors.append("Missing 'webhook' section in visual settings")
    else:
        webhook = content['webhook']
        if 'account' not in webhook:
            errors.append("Missing 'account' in webhook settings")
        else:
            account = webhook['account']
            
            if 'logging' in account:
                logging = account['logging']
                if 'loaded' in logging:
                    loaded = logging['loaded']
                    if not loaded.get('content'):
                        errors.append("Logging 'loaded' content cannot be empty")
            
            if 'claim' in account:
                claim = account['claim']
                if 'success' in claim:
                    success = claim['success']
                    if not success.get('content'):
                        errors.append("Claim 'success' content cannot be empty")
                if 'fail' in claim:
                    fail = claim['fail']
                    if not fail.get('content'):
                        errors.append("Claim 'fail' content cannot be empty")

            if 'detection' in account:
                detection = account['detection']
                if 'embeds' in detection:
                    for embed in detection['embeds']:
                        required_fields = ['id', 'description', 'fields', 'title']
                        for field in required_fields:
                            if field not in embed:
                                errors.append(f"Missing '{field}' in detection embed")

    if not 'crqzy' in content:
        errors.append("Missing required section in visual settings.")

    validation_end = time.time()
    print(f"[VISUAL SETTINGS] validation took {round(validation_end - validation_begin, 2)} seconds")
    return errors

def load_settings():
    try:
        with open(settings_file_location, 'r', encoding="utf-8") as f:
            content = f.read()
        
        errors = validate_settings(content)
        
        if errors:
            logger = ["[BEGIN] please, fix the following errors in order to use mehhovcki group autoclaimer:"]
            for error in errors:
                logger.append(f"[ALERT] {error}")
            
            for log_entry in logger:
                print(f"[TROUBLESHOOT] {log_entry}")
            exit(1)
    except Exception as error:
        logger = []
        logger.append("[BEGIN] failed to load settings file. trying to figure out now.")

        if isinstance(error, FileNotFoundError):
            logger.append("[ERROR] failed to find settings file. did you remove it?")
            logger.append("[SUGGESTION] create config.json in the config directory")
        elif isinstance(error, PermissionError):
            logger.append("[ERROR] failed to read settings file. check permissions.")
            logger.append("[SUGGESTION] verify file read permissions")
        else:
            logger.append(f"[ERROR] failed because of unhandled error. report this to github. {error}")
        logger.append("[LOG] trying to validate settings file, to understand if any more issues are present.")
        errors = validate_settings(content if 'content' in locals() else '{}')

        if errors:
            logger.append("[ERROR] found errors in settings file:")
            for error in errors:
                logger.append(f"[ALERT] {error}")
        
        for log_entry in logger:
            print(f"[TROUBLESHOOT] {log_entry}")        
        exit(1)

    errors = validate_settings(content)
    
    if errors:
        logger = ["[BEGIN] found errors in settings file:"]
        for error in errors:
            logger.append(f"[ERROR] {error}")
        
        for log_entry in logger:
            print(f"[TROUBLESHOOT] {log_entry}")
        
        return None
    print("[INFO] successfully loaded settings file! trying to read visual settings.")
    return json.loads(content)

def load_visual_settings():
    try:
        with open(visual_file_location, 'r', encoding="utf-8") as f:
            content = f.read()
        errors = validate_visual_settings(content)
        
        if errors:
            logger = ["[BEGIN] please, fix the following errors in visual settings:"]
            for error in errors:
                logger.append(f"[ALERT] {error}")
            
            for log_entry in logger:
                print(f"[TROUBLESHOOT] {log_entry}")
            exit(1)
    except Exception as error:
        logger = []
        logger.append("[BEGIN] failed to load visual settings file.")

        if isinstance(error, FileNotFoundError):
            logger.append("[ERROR] failed to find visual settings file.")
            logger.append("[SUGGESTION] create visual.json in the config directory")
        elif isinstance(error, PermissionError):
            logger.append("[ERROR] failed to read visual settings file. Check permissions.")
        else:
            logger.append(f"[ERROR] failed because of unhandled error: {error}")
        
        for log_entry in logger:
            print(f"[TROUBLESHOOT] {log_entry}")        
        exit(1)
    
    print("[INFO] successfully loaded visual settings file!")
    return json.loads(content)
