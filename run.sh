#!/bin/bash
# Activa el entorno virtual
source .venv/bin/activate

# Lanza el servidor
uvicorn app.main:app --reload
