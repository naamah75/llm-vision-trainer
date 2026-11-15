DOMAIN = "llm_vision_trainer"
STORE_VERSION = 2
STORE_KEY = f"{DOMAIN}.registry"
MEMORY_BACKUP_DIR = f"{DOMAIN}/memory_backups"
MEMORY_QUARANTINE_DIR = f"{DOMAIN}/memory_quarantine"
IMAGE_DIR = f"{DOMAIN}/images"
DEFAULT_MAX_EXAMPLES = 2
DEFAULT_LABELS = {
    "amazon": "Amazon", "gls": "GLS", "brt": "BRT",
    "poste": "Poste Italiane", "altro": "Altro corriere",
    "non_corriere": "Non corriere",
}
ALLOWED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
CARD_URL = "/llm-vision-trainer/llm-vision-trainer-card.js"
