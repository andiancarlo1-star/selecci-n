import os
from dotenv import load_dotenv

load_dotenv()  # carga el .env al entorno

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "qwen/qwen3.5-397b-a17b")
