# main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import subprocess
import os
import pathlib

# Paths base
TMP_DIR = pathlib.Path("/tmp")
TMP_DIR.mkdir(parents=True, exist_ok=True)

BASE_DIR = pathlib.Path(__file__).parent.resolve()


app = FastAPI()

# CORS: aceptar cualquier origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
def norm(x):
    if not isinstance(x, str):
        return x
    import unicodedata
    x = unicodedata.normalize("NFKD", x)
    x = "".join(c for c in x if not unicodedata.combining(c))
    return x.strip().lower()


# Datos de prueba
TEST_SUBJECTS = {
    "1A": [
        {"id": "Matematicas", "H": 5, "rooms": ["Aula 1"], "profs": ["Ana Lopez"]},
        {"id": "Espanol", "H": 5, "rooms": ["Aula 1"], "profs": ["Carlos Perez"]},
        {"id": "Ciencias", "H": 4, "rooms": ["Aula 2"], "profs": ["Mario Garcia"]},
        {"id": "Historia", "H": 3, "rooms": ["Aula 3"], "profs": ["Carlos Perez"]},
        {"id": "Ingles", "H": 3, "rooms": ["Aula 2"], "profs": ["Ana Lopez"]}
    ],
    "2A": [
        {"id": "Matematicas", "H": 5, "rooms": ["Aula 2"], "profs": ["Ana Lopez"]},
        {"id": "Espanol", "H": 5, "rooms": ["Aula 2"], "profs": ["Carlos Perez"]},
        {"id": "Ciencias", "H": 4, "rooms": ["Aula 3"], "profs": ["Mario Garcia"]},
        {"id": "Historia", "H": 3, "rooms": ["Aula 1"], "profs": ["Carlos Perez"]},
        {"id": "Ingles", "H": 3, "rooms": ["Aula 1"], "profs": ["Ana Lopez"]}
    ],
    "3A": [
        {"id": "Matematicas", "H": 5, "rooms": ["Aula 3"], "profs": ["Ana Lopez"]},
        {"id": "Espanol", "H": 5, "rooms": ["Aula 3"], "profs": ["Carlos Perez"]},
        {"id": "Ciencias", "H": 4, "rooms": ["Aula 1"], "profs": ["Mario Garcia"]},
        {"id": "Historia", "H": 3, "rooms": ["Aula 2"], "profs": ["Carlos Perez"]},
        {"id": "Ingles", "H": 3, "rooms": ["Aula 2"], "profs": ["Ana Lopez"]}
    ]
}

def get_prof_room(materia, grupo):
    materia_n = norm(materia)
    grupo_n = norm(grupo)

    if grupo not in TEST_SUBJECTS:
        return None, None

    for m in TEST_SUBJECTS[grupo]:
        if norm(m["id"]) == materia_n:
            prof = norm(m["profs"][0]) if m["profs"] else None
            room = norm(m["rooms"][0]) if m["rooms"] else None
            return prof, room

    return None, None
# Función para limpiar archivos
def limpiar_archivos():
    archivos = [
        TMP_DIR / "materias_fuera.json",
        TMP_DIR / "horario_greedy.json",
        TMP_DIR / "horario_greedy_aplicado.json",
        TMP_DIR / "sugerencias_movimientos.json",
        TMP_DIR / "sugerencias_ignoradas.json",
        TMP_DIR / "subjects.json"
    ]
    for archivo in archivos:
        if archivo.exists():
            try:
                archivo.unlink()
            except Exception:
                pass

@app.post("/generar-horario")
async def generar_horario(request: Request):
    # Limpiar archivos previos
    limpiar_archivos()

    try:
        data = await request.json()
    except Exception:
        data = None

    if not data:
        data = TEST_SUBJECTS

    # Guardar subjects en /tmp
    subjects_path = TMP_DIR / "subjects.json"
    with open(subjects_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Ejecutar scripts
    try:
        subprocess.run(["python", str(BASE_DIR / "horario_greedy.py"), str(subjects_path)], check=True)
    except subprocess.CalledProcessError as e:
        return JSONResponse({"error": "Error al ejecutar horario_greedy.py", "details": str(e)}, status_code=500)

    # Rutas absolutas para los archivos generados
    materias_fuera_path = TMP_DIR / "materias_fuera.json"
    horario_greedy_path = TMP_DIR / "horario_greedy.json"
    result_path = TMP_DIR / "horario_greedy_aplicado.json"

    # Verificar si el horario es perfecto
    perfecto = False
    if materias_fuera_path.exists():
        with open(materias_fuera_path, encoding="utf-8") as f:
            fuera = json.load(f)
        if not fuera:
            perfecto = True
    else:
        perfecto = True

    if perfecto:
        if horario_greedy_path.exists():
            with open(horario_greedy_path, encoding="utf-8") as f:
                horario = json.load(f)
            return {"horario": horario, "perfecto": True}
        else:
            return JSONResponse({"error": "No se generó el horario perfecto"}, status_code=500)

    # Si no es perfecto, pipeline de sugerencias
    try:
        subprocess.run(["python", str(BASE_DIR / "swap_sugerencias_horario.py"),str(TMP_DIR / "horario_greedy.json"),str(TMP_DIR / "materias_fuera.json"),str(TMP_DIR /"sugerencias_movimientos.json"),str(TMP_DIR / "subjects.json")  ], check=True)

        subprocess.run(["python", str(BASE_DIR / "aplicar_sugerencias_horario.py"),str(TMP_DIR / "horario_greedy.json"),str(TMP_DIR / "sugerencias_movimientos.json"),str(TMP_DIR / "horario_greedy_aplicado.json"),str(TMP_DIR / "subjects.json")], check=True)

    except subprocess.CalledProcessError as e:
        return JSONResponse({"error": "Error al ejecutar scripts de sugerencias", "details": str(e)}, status_code=500)

    # Devolver resultado final
    if not result_path.exists():
        return JSONResponse({"error": "No se generó el horario final"}, status_code=500)

    with open(result_path, encoding="utf-8") as f:
        horario = json.load(f)

    return {"horario": horario, "perfecto": False}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
