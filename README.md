# Script para obtener de forma sencilla las cotizaciones del día del BCP
#### El script se actualiza de forma automática cada 10 minutos
## 1. Clonar repositorio

```bash
git clone https://github.com/USUARIO/bcp-cotizaciones-api.git

cd bcp-cotizaciones-api
```

## 2. Crear entorno virtual

```bash
python3 -m venv venv

source venv/bin/activate
```

## 3. Instalar dependencias

```bash
pip install requests beautifulsoup4 fastapi uvicorn apscheduler
```

## Ejecutar

```bash
python request.py
```

## Obtener cotizaciones
```bash
http://localhost:8000/cotizaciones
```

## Forzar actualización manual
```bash
http://localhost:8000/refresh
```




