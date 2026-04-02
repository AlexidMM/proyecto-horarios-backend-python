# analizar_huecos_y_sugerencias.py
"""
Analiza los huecos y materias no asignadas del horario greedy, y sugiere posibles ubicaciones para insertar las materias faltantes sin violar restricciones.
"""
import json
from collections import defaultdict

# Cargar datos
with open('horario_greedy.json', encoding='utf-8') as f:
    asignaciones = json.load(f)
with open('materias_fuera.json', encoding='utf-8') as f:
    materias_fuera = json.load(f)

# Definir slots y subjects igual que en el greedy
SLOTS_PER_DAY = 5
DAYS = ["Lun", "Mar", "Mie", "Jue", "Vie"]
SLOTS = [f"{d}{17+i}" for d in DAYS for i in range(SLOTS_PER_DAY)]

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
    # group -> set(slots)
    ocupados = defaultdict(set)
    for a in asignaciones:
        ocupados[a["group"]].add(a["start"])
    return ocupados

def profs_rooms_en_slot(asignaciones):
    # slot -> (profs, rooms) ocupados
    profs_slot = defaultdict(set)
    rooms_slot = defaultdict(set)
    for a in asignaciones:
        profs_slot[a["start"]].add(a["prof"])
        rooms_slot[a["start"]].add(a["room"])
    return profs_slot, rooms_slot

ocupados = slots_ocupados(asignaciones)
profs_slot, rooms_slot = profs_rooms_en_slot(asignaciones)

sugerencias = []
for falta in materias_fuera:
    grupo = falta["group"]
    materia = falta["materia"]
    horas = falta["horas_faltantes"]
    prof, room = get_prof_room(materia, grupo)
    posibles = []
    for slot in SLOTS:
        if slot in ocupados[grupo]:
            continue
        if prof in profs_slot[slot]:
            continue
        if room in rooms_slot[slot]:
            continue
        posibles.append(slot)
    sugerencias.append({
        "group": grupo,
        "materia": materia,
        "horas_faltantes": horas,
        "prof": prof,
        "room": room,
        "slots_sugeridos": posibles
    })

with open('sugerencias_huecos.json', 'w', encoding='utf-8') as f:
    json.dump(sugerencias, f, ensure_ascii=False, indent=4)

print("Sugerencias generadas en sugerencias_huecos.json")
for s in sugerencias:
    print(f"Grupo: {s['group']}, Materia: {s['materia']}, Horas faltantes: {s['horas_faltantes']}")
    print(f"  Slots sugeridos: {s['slots_sugeridos']}")
