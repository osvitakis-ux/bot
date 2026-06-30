import os
BOT_TOKEN      = os.environ.get("BOT_TOKEN", "")
ADMIN_CHAT_ID  = int(os.environ.get("ADMIN_CHAT_ID", 0))
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "konstanta2024")
CRM_WEBHOOK_URL = os.environ.get("CRM_WEBHOOK_URL", "")  # URL вашої CRM для прийому лідів
CRM_WEBHOOK_SECRET = os.environ.get("CRM_WEBHOOK_SECRET", "")  # опційний токен для перевірки запиту
