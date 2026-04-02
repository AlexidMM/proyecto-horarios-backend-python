# analizar_huecos_y_sugerencias_mejorado.py
"""
Analiza los huecos y materias no asignadas del horario greedy, y sugiere posibles ubicaciones para insertar las materias faltantes sin violar restricciones:
- No más de 2 horas seguidas de la misma materia por grupo
- No repetir profesor en el mismo grupo el mismo día
- No solapamiento de profesor ni aula
- (Opcional) Restricción de inglés
"""
import json
from collections import defaultdict


import sys
# Cargar datos
with open('horario_greedy.json', encoding='utf-8') as f:
    asignaciones = json.load(f)
with open('materias_fuera.json', encoding='utf-8') as f:
    materias_fuera = json.load(f)

SLOTS_PER_DAY = 5
DAYS = ["Lun", "Mar", "Mie", "Jue", "Vie"]
SLOTS = [f"{d}{17+i}" for d in DAYS for i in range(SLOTS_PER_DAY)]

# Permitir pasar la ruta de SUBJECTS como argumento
if len(sys.argv) > 1:
    with open(sys.argv[1], encoding="utf-8") as f:
        SUBJECTS = json.load(f)
else:
    SUBJECTS = {
        "IDGS14": [
            {"id": "administracion del tiempo", "H": 3, "rooms": ["Aula 12 edificio k"], "profs": ["Maria Guadalupe"]},
            {"id": "Matematicas para ingenieria", "H": 4, "rooms": ["Aula 11 edificio k"], "profs": ["Jesus Hernan"]},
            {"id": "Arquitectura de software", "H": 5, "rooms": ["Aula 11 edificio I"], "profs": ["Manuel"]},
            {"id": "Ingles", "H": 4, "rooms": ["Aula 13 edificio k"], "profs": ["Profe Ingles3"]},
            {"id": "Metodologia de desarrollo de proyectos", "H": 3, "rooms": ["SUMPA edificio k"], "profs": ["Angelica"]},
            {"id": "Experiencia de usuario", "H": 3, "rooms": ["Aula 10 edificio j"], "profs": ["Emmanuel"]},
            {"id": "Seguridad informatica", "H": 3, "rooms": ["Aula 12 edificio j"], "profs": ["Brandon"]},
        ],
        "IDGS15": [
            {"id": "administracion del tiempo", "H": 3, "rooms": ["Aula 12 edificio k"], "profs": ["Maria Guadalupe"]},
            {"id": "Matematicas para ingenieria", "H": 4, "rooms": ["Aula 11 edificio k"], "profs": ["Jesus Hernan"]},
            {"id": "Arquitectura de software", "H": 5, "rooms": ["Aula 11 edificio I"], "profs": ["Manuel"]},
            {"id": "Ingles", "H": 4, "rooms": ["Aula 13 edificio k"], "profs": ["Profe Ingles1"]},
            {"id": "Metodologia de desarrollo de proyectos", "H": 3, "rooms": ["SUMPA edificio k"], "profs": ["Angelica"]},
            {"id": "Experiencia de usuario", "H": 3, "rooms": ["Aula 10 edificio j"], "profs": ["Emmanuel"]},
            {"id": "Seguridad informatica", "H": 3, "rooms": ["Aula 12 edificio j"], "profs": ["Brandon"]},
        ],
        "IDGS16": [
            {"id": "administracion del tiempo", "H": 3, "rooms": ["Aula 12 edificio k"], "profs": ["Maria Guadalupe"]},
            {"id": "Matematicas para ingenieria", "H": 4, "rooms": ["Aula 11 edificio k"], "profs": ["Jesus Hernan"]},
            {"id": "Arquitectura de software", "H": 5, "rooms": ["Aula 11 edificio I"], "profs": ["Manuel"]},
            {"id": "Ingles", "H": 4, "rooms": ["Aula 13 edificio k"], "profs": ["Profe Ingles2"]},
            {"id": "Metodologia de desarrollo de proyectos", "H": 3, "rooms": ["SUMPA edificio k"], "profs": ["Angelica"]},
            {"id": "Experiencia de usuario", "H": 3, "rooms": ["Aula 10 edificio j"], "profs": ["Emmanuel"]},
            {"id": "Seguridad informatica", "H": 3, "rooms": ["Aula 12 edificio j"], "profs": ["Brandon"]},
        ]
    }

def get_prof_room(materia, grupo):
    for subj in SUBJECTS[grupo]:
        if subj["id"] == materia:
            return subj["profs"][0], subj["rooms"][0]
    return None, None

def slots_ocupados(asignaciones):
    ocupados = defaultdict(set)
    for a in asignaciones:
        ocupados[a["group"]].add(a["start"])
    return ocupados

def profs_rooms_en_slot(asignaciones):
    profs_slot = defaultdict(set)
    rooms_slot = defaultdict(set)
    for a in asignaciones:
        profs_slot[a["start"]].add(a["prof"])
        rooms_slot[a["start"]].add(a["room"])
    return profs_slot, rooms_slot

def profe_ya_dio_en_dia(asignaciones, grupo, prof, slot):
    dia = slot[:3]
    return any(a["prof"] == prof and a["group"] == grupo and a["start"].startswith(dia) for a in asignaciones)

def max_2_seguidas(asignaciones, grupo, materia, slot):
    # Simula la inserción y revisa si quedarían más de 2 seguidas
    # Obtener slots de ese grupo para esa materia (incluyendo el slot propuesto)
    slots_materia = [a["start"] for a in asignaciones if a["group"] == grupo and a["subj"] == materia]
    slots_materia.append(slot)
    # Convertir a índices
    idxs = sorted(SLOTS.index(s) for s in slots_materia)
    for i in range(len(idxs)-2):
        if idxs[i+2] - idxs[i] == 2:
            return False  # Hay 3 seguidas
    return True

def sugerir_slots_validos(falta, asignaciones, ocupados, profs_slot, rooms_slot):
    grupo = falta["group"]
    materia = falta["materia"]
    prof, room = get_prof_room(materia, grupo)
    posibles = []
    for slot in SLOTS:
        if slot in ocupados[grupo]:
            continue
        if prof in profs_slot[slot]:
            continue
        if room in rooms_slot[slot]:
            continue
        if profe_ya_dio_en_dia(asignaciones, grupo, prof, slot):
            continue
        if not max_2_seguidas(asignaciones, grupo, materia, slot):
            continue
        posibles.append(slot)
    return posibles

ocupados = slots_ocupados(asignaciones)
profs_slot, rooms_slot = profs_rooms_en_slot(asignaciones)


sugerencias = []
acciones = []
for falta in materias_fuera:
    slots_validos = sugerir_slots_validos(falta, asignaciones, ocupados, profs_slot, rooms_slot)
    sugerencias.append({
        **falta,
        "slots_sugeridos": slots_validos
    })
    if slots_validos:
        acciones.append({
            "accion": "asignar",
            "group": falta["group"],
            "materia": falta["materia"],
            "slot": slots_validos[0],
            "detalle": f"Asignar '{falta['materia']}' al grupo {falta['group']} en el slot {slots_validos[0]}"
        })
    else:
        acciones.append({
            "accion": "sin_slot",
            "group": falta["group"],
            "materia": falta["materia"],
            "detalle": f"No hay slot válido para '{falta['materia']}' del grupo {falta['group']}"
        })

with open('sugerencias_huecos_mejorado.json', 'w', encoding='utf-8') as f:
    json.dump(sugerencias, f, ensure_ascii=False, indent=4)
with open('acciones_sugeridas.json', 'w', encoding='utf-8') as f:
    json.dump(acciones, f, ensure_ascii=False, indent=4)

print("Sugerencias mejoradas generadas en sugerencias_huecos_mejorado.json")
print("Acciones sugeridas generadas en acciones_sugeridas.json")
for a in acciones:
    print(a["detalle"])
