# swap_sugerencias_horario.py
"""
Script para sugerir movimientos en cascada (swap/push) para acomodar materias faltantes en el horario,
intentando dejar el horario perfecto sin violar restricciones.
"""
import json
import copy
import sys
from pathlib import Path

# --- Configuración de paths ---
if len(sys.argv) > 2:
    horario_path = Path(sys.argv[1])
    materias_fuera_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3]) if len(sys.argv) > 3 else materias_fuera_path.parent / "sugerencias_movimientos.json"
else:
    BASE_DIR = Path(__file__).parent.resolve()
    horario_path = BASE_DIR / "horario_greedy.json"
    materias_fuera_path = BASE_DIR / "materias_fuera.json"
    output_path = BASE_DIR / "sugerencias_movimientos.json"

# --- Cargar datos ---
with open(horario_path, encoding='utf-8') as f:
    asignaciones = json.load(f)
with open(materias_fuera_path, encoding='utf-8') as f:
    materias_fuera = json.load(f)

    
# --- Slots ---
SLOTS_PER_DAY = 6
DAYS = ["Lun", "Mar", "Mie", "Jue", "Vie"]
SLOTS = [f"{d}{(i + 1):02d}" for d in DAYS for i in range(SLOTS_PER_DAY)]
# --- Cargar SUBJECTS pasado desde main.py ---
if len(sys.argv) > 4:
    subjects_path = Path(sys.argv[4])
    with open(subjects_path, encoding='utf-8') as f:
        SUBJECTS = json.load(f)
else:
   

    SUBJECTS = {
  "IDGS15": [
    {"id": "Administración del Tiempo","H": 3,"rooms": ["Salón 12 Edificio K"],"profs": ["Maria Guadalupe Callejas Ramirez"]},
    {"id": "Matematicas para Ingenieria 1","H": 4,"rooms": ["Salón 11 Edificio K"],"profs": ["Jesus Hernan Perez Vazquez"]},
    {"id": "Arquitectura de software","H": 5,"rooms": ["Salon 12 Edificio I"],"profs": ["Manuel Contreras Castillo"]},
    {"id": "Ingles","H": 4,"rooms": ["Salón 13 Edificio K"],"profs": ["Juan josé Vazquez Rodriguez"]},
    {"id": "Metodologia de desarrollo de proyectos","H": 3,"rooms": ["SUMPA Edificio K"],"profs": ["Angelica Garduño Bustamante"],"min_hora": 19},
    {"id": "Experiencia de Usuario","H": 3,"rooms": ["Salon 11 Edificio J"],"profs": ["Emmanuel Martinez Hernándes"]},
    {"id": "Seguridad Informatica","H": 3,"rooms": ["Salón 12 Edificio J"],"profs": ["Brandon Efren Venegas Olvera"]}
   
  ],
  "IDGS14": [
    {"id": "Administración del Tiempo","H": 3,"rooms": ["Salón 12 Edificio K"],"profs": ["Maria Guadalupe Callejas Ramirez"]},
    {"id": "Matematicas para Ingenieria 1","H": 4,"rooms": ["Salón 11 Edificio K"],"profs": ["Jesus Hernan Perez Vazquez"]},
    {"id": "Arquitectura de software","H": 5,"rooms": ["Salon 12 Edificio I"],"profs": ["Manuel Contreras Castillo"]},
    {"id": "Ingles","H": 4,"rooms": ["Salón 13 Edificio K"],"profs": ["profe ingles 2"]},
    {"id": "Metodologia de desarrollo de proyectos","H": 3,"rooms": ["SUMPA Edificio K"],"profs": ["Angelica Garduño Bustamante"],"min_hora": 19},
    {"id": "Experiencia de Usuario","H": 3,"rooms": ["Salon 11 Edificio J"],"profs": ["Emmanuel Martinez Hernándes"]},
    {"id": "Seguridad Informatica","H": 3,"rooms": ["Salón 12 Edificio J"],"profs": ["Brandon Efren Venegas Olvera"]}

  ],
  "IDGS16": [
    {"id": "Administración del Tiempo","H": 3,"rooms": ["Salón 12 Edificio K"],"profs": ["Maria Guadalupe Callejas Ramirez"]},
    {"id": "Matematicas para Ingenieria 1","H": 4,"rooms": ["Salón 11 Edificio K"],"profs": ["Jesus Hernan Perez Vazquez"]},
    {"id": "Arquitectura de software","H": 5,"rooms": ["Salon 12 Edificio I"],"profs": ["Manuel Contreras Castillo"]},
    {"id": "Ingles","H": 4,"rooms": ["Salón 13 Edificio K"],"profs": ["profe ingles 3"]},
    {"id": "Metodologia de desarrollo de proyectos","H": 3,"rooms": ["SUMPA Edificio K"],"profs": ["Angelica Garduño Bustamante"],"min_hora": 19},
    {"id": "Experiencia de Usuario","H": 3,"rooms": ["Salon 11 Edificio J"],"profs": ["Emmanuel Martinez Hernándes"]},
    {"id": "Seguridad Informatica","H": 3,"rooms": ["Salón 12 Edificio J"],"profs": ["Brandon Efren Venegas Olvera"]}
  ]
}


# --- Funciones de validación ---
def get_prof_room(materia, grupo):
    for subj in SUBJECTS[grupo]:
        if subj["id"] == materia:
            return subj["profs"][0], subj["rooms"][0]
    return None, None

def profe_ya_dio_en_dia(asignaciones, grupo, prof, slot):
    dia = slot[:3]
    return any(a["prof"] == prof and a["group"] == grupo and a["start"].startswith(dia) for a in asignaciones)

def max_2_seguidas(asignaciones, grupo, materia, slot):
    slots_materia = [a["start"] for a in asignaciones if a["group"] == grupo and a["subj"] == materia]
    slots_materia.append(slot)
    idxs = sorted(SLOTS.index(s) for s in slots_materia)
    for i in range(len(idxs)-2):
        if idxs[i+2] - idxs[i] == 2:
            return False
    return True

def slot_libre(asignaciones, grupo, slot):
    return not any(a["group"] == grupo and a["start"] == slot for a in asignaciones)

def prof_room_libres(asignaciones, prof, room, slot):
    return not any((a["prof"] == prof or a["room"] == room) and a["start"] == slot for a in asignaciones)

def get_constraints(materia, grupo):
    for subj in SUBJECTS.get(grupo, []):
        if subj["id"] == materia:
            return {
                "prof": subj["profs"][0],
                "room": subj["rooms"][0],
                "allow_double_block": subj.get("allow_double_block", False),
                "min_hora": subj.get("min_hora", 1),
                "max_hora": subj.get("max_hora", 6)
            }
    return None

def hora_valida(slot, min_hora, max_hora):
    hora = int(slot[3:])
    return min_hora <= hora <= max_hora

def materia_repetida_en_dia(asignaciones, grupo, materia, slot):
    dia = slot[:3]
    return any(a["group"] == grupo and a["subj"] == materia and a["start"].startswith(dia) for a in asignaciones)


def puede_repetir_materia_en_dia(asignaciones, grupo, materia, slot):
    cons = get_constraints(materia, grupo)
    if not cons:
        return False

    allow_double = bool(cons.get("allow_double_block", False))
    dia = slot[:3]
    hora = int(slot[3:])
    existentes = [a for a in asignaciones if a["group"] == grupo and a["subj"] == materia and a["start"].startswith(dia)]

    if len(existentes) == 0:
        return True
    if not allow_double:
        return False
    if len(existentes) >= 2:
        return False

    hora_existente = int(existentes[0]["start"][3:])
    return abs(hora - hora_existente) == 1

def puede_asignar(asignaciones, grupo, materia, prof, room, slot):
    cons = get_constraints(materia, grupo)
    if not cons or not prof or not room:
        return False

    # 1) hora válida
    if not hora_valida(slot, cons["min_hora"], cons["max_hora"]):
        return False

    # 2) slot libre para ese grupo
    if not slot_libre(asignaciones, grupo, slot):
        return False

    # 3) no repetir materia en el mismo dia (excepto cuando se permita doble bloque consecutivo)
    if not puede_repetir_materia_en_dia(asignaciones, grupo, materia, slot):
        return False

    # 4) prof + room disponibles
    if not prof_room_libres(asignaciones, prof, room, slot):
        return False

    # 5) prof no repite ese día
    if profe_ya_dio_en_dia(asignaciones, grupo, prof, slot):
        return False

    # 6) máximo 2 seguidas
    if not max_2_seguidas(asignaciones, grupo, materia, slot):
        return False

    return True


def buscar_swap(asignaciones, grupo, materia, prof, room, slot):
    cons = get_constraints(materia, grupo)
    if not cons:
        return None

    # No swap si este slot no cumple la hora
    if not hora_valida(slot, cons["min_hora"], cons["max_hora"]):
        return None

    # Slot ocupado -> intentar mover la materia que esta ahi
    for idx, a in enumerate(asignaciones):
        if a["group"] == grupo and a["start"] == slot:

            materia_actual = a["subj"]
            if materia_actual.lower().startswith("ingles"):
                return None  # ingles no se mueve

            cons2 = get_constraints(materia_actual, grupo)
            if not cons2:
                return None
            prof_actual = cons2["prof"]
            room_actual = cons2["room"]

            # buscar un slot válido para mover la materia actual
            for slot2 in SLOTS:
                if slot2 == slot:
                    continue

                # Simular el swap en un estado temporal para validar colisiones reales
                temp = copy.deepcopy(asignaciones)
                temp.pop(idx)

                if not puede_asignar(temp, grupo, materia_actual, prof_actual, room_actual, slot2):
                    continue

                temp.append({
                    "group": grupo,
                    "subj": materia_actual,
                    "start": slot2,
                    "room": room_actual,
                    "prof": prof_actual,
                })

                if not puede_asignar(temp, grupo, materia, prof, room, slot):
                    continue

                return {
                    "swap": True,
                    "mover": {
                        "group": grupo,
                        "materia": materia_actual,
                        "from": slot,
                        "to": slot2
                    }
                }

    return None

# --- Generar sugerencias ---
def sugerir_movimientos(asignaciones, materias_fuera):
    sugerencias = []
    sugeridas = set()
    swaps_usados = set()
    estado_actual = copy.deepcopy(asignaciones)

    def aplicar_directo_local(grupo, materia, prof, room, slot):
        estado_actual.append({
            "group": grupo,
            "subj": materia,
            "start": slot,
            "room": room,
            "prof": prof,
        })

    def aplicar_swap_local(grupo, materia, prof, room, slot, swap):
        mover = swap["mover"]
        for item in estado_actual:
            if (
                item.get("group") == mover["group"]
                and item.get("subj") == mover["materia"]
                and item.get("start") == mover["from"]
            ):
                item["start"] = mover["to"]
                break
        estado_actual.append({
            "group": grupo,
            "subj": materia,
            "start": slot,
            "room": room,
            "prof": prof,
        })

    for falta in materias_fuera:
        grupo = falta["group"]
        materia = falta["materia"]
        prof, room = get_prof_room(materia, grupo)
        if not prof or not room:
            clave = ("sin_solucion", grupo, materia, "sin_prof_room")
            if clave not in sugeridas:
                sugerencias.append({
                    "accion": "sin_solucion",
                    "group": grupo,
                    "materia": materia,
                    "detalle": f"No se encontro profesor/salon configurado para '{materia}' del grupo {grupo}"
                })
                sugeridas.add(clave)
            continue

        # Intentar asignar directo
        for slot in SLOTS:
            clave = ("asignar_directo", grupo, materia, slot)
            if clave in sugeridas:
                continue
            if puede_asignar(estado_actual, grupo, materia, prof, room, slot):
                sugerencias.append({
                    "accion": "asignar_directo",
                    "group": grupo,
                    "materia": materia,
                    "slot": slot,
                    "detalle": f"Asignar '{materia}' al grupo {grupo} en {slot} (directo)"
                })
                sugeridas.add(clave)
                aplicar_directo_local(grupo, materia, prof, room, slot)
                break
        else:
            # Intentar swap
            for slot in SLOTS:
                clave = ("swap", grupo, materia, slot)
                if clave in sugeridas or slot_libre(estado_actual, grupo, slot):
                    continue
                swap = buscar_swap(estado_actual, grupo, materia, prof, room, slot)
                if swap:
                    mover_materia = swap["mover"]["materia"]
                    if (grupo, slot, mover_materia) in swaps_usados:
                        continue
                    sugerencias.append({
                        "accion": "swap",
                        "group": grupo,
                        "materia": materia,
                        "slot": slot,
                        "detalle": f"Mover '{mover_materia}' de {slot} a {swap['mover']['to']} y asignar '{materia}' en {slot} para el grupo {grupo}",
                        "swap": swap
                    })
                    sugeridas.add(clave)
                    swaps_usados.add((grupo, slot, mover_materia))
                    aplicar_swap_local(grupo, materia, prof, room, slot, swap)
                    break
            else:
                clave = ("sin_solucion", grupo, materia, None)
                if clave not in sugeridas:
                    sugerencias.append({
                        "accion": "sin_solucion",
                        "group": grupo,
                        "materia": materia,
                        "detalle": f"No se encontró slot ni swap válido para '{materia}' del grupo {grupo}"
                    })
                    sugeridas.add(clave)
    return sugerencias

# --- Ejecutar ---
sugerencias = sugerir_movimientos(asignaciones, materias_fuera)

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(sugerencias, f, ensure_ascii=False, indent=4)

print(f"Sugerencias generadas y guardadas en {output_path}")
print(f"Total sugerencias: {len(sugerencias)}")
for s in sugerencias:
    print(s["detalle"])
    if s["accion"] == "swap":
        print(f"  Swap: mover '{s['swap']['mover']['materia']}' de {s['swap']['mover']['from']} a {s['swap']['mover']['to']}")
