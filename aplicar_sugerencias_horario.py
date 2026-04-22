# aplicar_sugerencias_horario.py
"""
Aplica automáticamente las sugerencias de movimientos y swaps al horario original,
generando un nuevo archivo de horario ajustado.
"""
import json
import copy
import sys
from pathlib import Path

# --- Configuración de paths ---
if len(sys.argv) > 3:
    horario_path = Path(sys.argv[1])
    sugerencias_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3])
    subjects_path = Path(sys.argv[4]) if len(sys.argv) > 4 else None
else:
    BASE_DIR = Path(__file__).parent.resolve()
    horario_path = BASE_DIR / "horario_greedy.json"
    sugerencias_path = BASE_DIR / "sugerencias_movimientos.json"
    output_path = BASE_DIR / "horario_greedy_aplicado.json"
    subjects_path = None

# --- Cargar archivos ---
with open(horario_path, encoding='utf-8') as f:
    horario = json.load(f)
with open(sugerencias_path, encoding='utf-8') as f:
    sugerencias = json.load(f)

# --- Cargar subjects ---
if subjects_path and subjects_path.exists():
    with open(subjects_path, encoding="utf-8") as f:
        SUBJECTS = json.load(f)
else:
    SUBJECTS = {
  "IDGS15": [
    {
      "id": "Matematicas para Ingenieria 1",
      "H": 4,
      "rooms": [
        "Salón 11 Edificio K"
      ],
      "profs": [
        "Jesus Hernan Perez Vazquez"
      ]
    },
    {
      "id": "Ingles",
      "H": 4,
      "rooms": [
        "Salón 13 Edificio K"
      ],
      "profs": [
        "Juan josé Vazquez Rodriguez"
      ]
    },
    {
      "id": "Seguridad Informatica",
      "H": 3,
      "rooms": [
        "Salón 12 Edificio J"
      ],
      "profs": [
        "Brandon Efren Venegas Olvera"
      ]
    },
    {
      "id": "Experiencia de Usuario",
      "H": 3,
      "rooms": [
        "Salon 11 Edificio I",
        "Salon 11 Edificio J"
      ],
      "profs": [
        "Emmanuel Martinez Hernándes"
      ]
    },
    {
      "id": "Arquitectura de software",
      "H": 5,
      "rooms": [
        "Salon 12 Edificio I"
      ],
      "profs": [
        "Manuel Contreras Castillo"
      ]
    },
    {
      "id": "Metodologia de desarrollo deproyectos",
      "H": 3,
      "rooms": [
        "SUMPA Edificio K"
      ],
      "profs": [
        "Angelica Garduño Bustamante"
      ],
      "min_hora": 19
    },
    {
      "id": "Administración del Tiempo",
      "H": 3,
      "rooms": [
        "Salón 12 Edificio K"
      ],
      "profs": [
        "Maria Guadalupe Callejas Ramirez"
      ]
    }
  ],
  "IDGS14": [
    {
      "id": "Matematicas para Ingenieria 1",
      "H": 4,
      "rooms": [
        "Salón 11 Edificio K"
      ],
      "profs": [
        "Jesus Hernan Perez Vazquez"
      ]
    },
    {
      "id": "Ingles",
      "H": 4,
      "rooms": [
        "Salón 13 Edificio K"
      ],
      "profs": [
        "profe ingles 2"
      ]
    },
    {
      "id": "Seguridad Informatica",
      "H": 3,
      "rooms": [
        "Salón 12 Edificio J"
      ],
      "profs": [
        "Brandon Efren Venegas Olvera"
      ]
    },
    {
      "id": "Experiencia de Usuario",
      "H": 3,
      "rooms": [
        "Salon 11 Edificio I",
        "Salon 11 Edificio J"
      ],
      "profs": [
        "Emmanuel Martinez Hernándes"
      ]
    },
    {
      "id": "Arquitectura de software",
      "H": 5,
      "rooms": [
        "Salon 12 Edificio I"
      ],
      "profs": [
        "Manuel Contreras Castillo"
      ]
    },
    {
      "id": "Metodologia de desarrollo deproyectos",
      "H": 3,
      "rooms": [
        "SUMPA Edificio K"
      ],
      "profs": [
        "Angelica Garduño Bustamante"
      ],
      "min_hora": 19
    },
    {
      "id": "Administración del Tiempo",
      "H": 3,
      "rooms": [
        "Salón 12 Edificio K"
      ],
      "profs": [
        "Maria Guadalupe Callejas Ramirez"
      ]
    }
  ],
  "IDGS16": [
    {
      "id": "Matematicas para Ingenieria 1",
      "H": 4,
      "rooms": [
        "Salón 11 Edificio K"
      ],
      "profs": [
        "Jesus Hernan Perez Vazquez"
      ]
    },
    {
      "id": "Ingles",
      "H": 4,
      "rooms": [
        "Salón 13 Edificio K"
      ],
      "profs": [
        "Profe ingles 3"
      ]
    },
    {
      "id": "Seguridad Informatica",
      "H": 3,
      "rooms": [
        "Salón 12 Edificio J"
      ],
      "profs": [
        "Brandon Efren Venegas Olvera"
      ]
    },
    {
      "id": "Experiencia de Usuario",
      "H": 3,
      "rooms": [
        "Salon 11 Edificio I",
        "Salon 11 Edificio J"
      ],
      "profs": [
        "Emmanuel Martinez Hernándes"
      ]
    },
    {
      "id": "Arquitectura de software",
      "H": 5,
      "rooms": [
        "Salon 12 Edificio I"
      ],
      "profs": [
        "Manuel Contreras Castillo"
      ]
    },
    {
      "id": "Metodologia de desarrollo deproyectos",
      "H": 3,
      "rooms": [
        "SUMPA Edificio K"
      ],
      "profs": [
        "Angelica Garduño Bustamante"
      ],
      "min_hora": 19
    },
    {
      "id": "Administración del Tiempo",
      "H": 3,
      "rooms": [
        "Salón 12 Edificio K"
      ],
      "profs": [
        "Maria Guadalupe Callejas Ramirez"
      ]
    }
  ]
}

# Función para obtener profe y aula
def get_prof_room(materia, grupo):
  for subj in SUBJECTS.get(grupo, []):
    if subj["id"] == materia:
      return subj["profs"][0], subj["rooms"][0]
  return None, None


def get_constraints(materia, grupo):
    for subj in SUBJECTS.get(grupo, []):
        if subj["id"] == materia:
            return {
                "min_hora": subj.get("min_hora", 1),
                "max_hora": subj.get("max_hora", 6),
        "allow_double_block": subj.get("allow_double_block", False),
            }
    return None


def hora_valida(slot, min_hora, max_hora):
    hora = int(slot[3:])
    return min_hora <= hora <= max_hora


def slot_libre(asignaciones, grupo, slot):
    return not any(a["group"] == grupo and a["start"] == slot for a in asignaciones)


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


def prof_room_libres(asignaciones, prof, room, slot):
    return not any((a["prof"] == prof or a["room"] == room) and a["start"] == slot for a in asignaciones)


def puede_asignar(asignaciones, grupo, materia, prof, room, slot):
    cons = get_constraints(materia, grupo)
    if not cons or not prof or not room:
        return False
    if not hora_valida(slot, cons["min_hora"], cons["max_hora"]):
        return False
    if not slot_libre(asignaciones, grupo, slot):
        return False
    if not puede_repetir_materia_en_dia(asignaciones, grupo, materia, slot):
        return False
    if not prof_room_libres(asignaciones, prof, room, slot):
        return False
    return True


def find_assignment_index(asignaciones, group, materia, start):
    for idx, item in enumerate(asignaciones):
        if item.get("group") == group and item.get("subj") == materia and item.get("start") == start:
            return idx
    return None

nuevo_horario = copy.deepcopy(horario)
# Función para aplicar swaps en cascada
def aplicar_swap_cascada(asignaciones, swap):
    mover = swap["mover"]
    for a in asignaciones:
        if a["group"] == mover["group"] and a["subj"] == mover["materia"] and a["start"] == mover["from"]:
            a["start"] = mover["to"]
            break
    # Aplicar recursivamente cualquier cascada
    if "cascada" in swap:
        aplicar_swap_cascada(asignaciones, swap["cascada"])

# --- Loop principal sobre sugerencias ---
aplicadas = 0
omitidas = 0

for sug in sugerencias:
  if sug["accion"] == "asignar_directo":
    grupo = sug["group"]
    materia = sug["materia"]
    slot = sug["slot"]
    prof, room = get_prof_room(materia, grupo)

    if not puede_asignar(nuevo_horario, grupo, materia, prof, room, slot):
      omitidas += 1
      print(f"[OMITIDA] asignar_directo invalida para {grupo} - {materia} en {slot}")
      continue

    nuevo_horario.append(
      {
        "group": grupo,
        "subj": materia,
        "start": slot,
        "room": room,
        "prof": prof,
      }
    )
    aplicadas += 1
    continue

  if sug["accion"] == "swap":
    grupo = sug["group"]
    materia = sug["materia"]
    slot = sug["slot"]
    prof, room = get_prof_room(materia, grupo)

    mover = sug.get("swap", {}).get("mover", {})
    mover_group = mover.get("group")
    mover_materia = mover.get("materia")
    mover_from = mover.get("from")
    mover_to = mover.get("to")

    idx = find_assignment_index(nuevo_horario, mover_group, mover_materia, mover_from)
    if idx is None:
      omitidas += 1
      print(f"[OMITIDA] swap sin materia origen: {mover_group} - {mover_materia} {mover_from}")
      continue

    entrada_mover = copy.deepcopy(nuevo_horario[idx])
    temp = copy.deepcopy(nuevo_horario)
    temp.pop(idx)

    if not puede_asignar(
      temp,
      entrada_mover["group"],
      entrada_mover["subj"],
      entrada_mover["prof"],
      entrada_mover["room"],
      mover_to,
    ):
      omitidas += 1
      print(f"[OMITIDA] swap invalido al mover {entrada_mover['subj']} de {mover_from} a {mover_to}")
      continue

    entrada_mover["start"] = mover_to
    temp.append(entrada_mover)

    if not puede_asignar(temp, grupo, materia, prof, room, slot):
      omitidas += 1
      print(f"[OMITIDA] swap invalido al insertar {materia} en {slot} para {grupo}")
      continue

    temp.append(
      {
        "group": grupo,
        "subj": materia,
        "start": slot,
        "room": room,
        "prof": prof,
      }
    )
    nuevo_horario = temp
    aplicadas += 1

# Guardar el resultado final en la ruta que quieras
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(nuevo_horario, f, ensure_ascii=False, indent=4)





print(f"¡Horario ajustado guardado en {output_path}!")
print(f"Sugerencias aplicadas: {aplicadas}")
print(f"Sugerencias omitidas por conflicto: {omitidas}")
