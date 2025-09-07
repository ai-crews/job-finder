# config/email_config.py
import os


class EmailConfig:
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    TEMPLATE_PATH = os.getenv("TEMPLATE_PATH", "templates/email_template.html")
    MAX_RECOMMENDED_JOBS = 10
