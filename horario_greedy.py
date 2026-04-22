import json
import random
import sys
from pathlib import Path
import copy
import unicodedata

# ============================================================
# CONFIGURACIÓN BASE
# ============================================================

SLOTS_PER_DAY = 6
DAYS = ["Lun", "Mar", "Mie", "Jue", "Vie"]
SLOTS = [f"{d}{(i + 1):02d}" for d in DAYS for i in range(SLOTS_PER_DAY)]

# Cargar SUBJECTS desde main.py
if len(sys.argv) > 1:
    subjects_path = Path(sys.argv[1])
else:
    subjects_path = Path("/tmp/subjects.json")

with open(subjects_path, encoding="utf-8") as f:
    SUBJECTS = json.load(f)

OUTPUT_DIR = subjects_path.parent
horario_greedy_path = OUTPUT_DIR / "horario_greedy.json"
materias_fuera_path = OUTPUT_DIR / "materias_fuera.json"


# ============================================================
# NORMALIZAR TEXTO
# ============================================================
def norm(x):
    if not isinstance(x, str):
        return x
    x = unicodedata.normalize("NFKD", x)
    x = "".join(c for c in x if not unicodedata.combining(c))
    return x.strip().lower()


# ============================================================
# EXTRAER PROF Y ROOM
# ============================================================
def get_prof_room(materia_id, grupo):
    mat_n = norm(materia_id)
    if grupo not in SUBJECTS:
        return None, None

    for m in SUBJECTS[grupo]:
        if norm(m["id"]) == mat_n:
            prof = m["profs"][0] if m["profs"] else None
            room = m["rooms"][0] if m["rooms"] else None
            return prof, room
    return None, None


def materia_en_dia(asignaciones, grupo, materia_id, dia):
    return [
        a for a in asignaciones
        if a["group"] == grupo
        and norm(a["subj"]) == norm(materia_id)
        and a["start"].startswith(dia)
    ]


def es_doble_consecutivo_valido(asignaciones, grupo, materia_id, slot, allow_double_block):
    existentes = materia_en_dia(asignaciones, grupo, materia_id, slot[:3])
    if len(existentes) == 0:
        return True

    # Si ya hay una de la misma materia en ese dia: solo permitir una segunda y consecutiva
    if not allow_double_block:
        return False

    if len(existentes) >= 2:
        return False

    hora_actual = int(slot[-2:])
    hora_existente = int(existentes[0]["start"][-2:])
    return abs(hora_actual - hora_existente) == 1


# ============================================================
# GREEDY PRINCIPAL
# ============================================================
def run_greedy():

    grupo_materia_horas = {
        (g, m["id"]): m["H"]
        for g in SUBJECTS
        for m in SUBJECTS[g]
    }

    asignaciones = []

    # --------------------------------------------------------
    # 1. Asignar inglés primero
    # --------------------------------------------------------
    horas_ingles = [1, 2, 3, 4, 5, 6]
    grupos = list(SUBJECTS.keys())
    random.shuffle(horas_ingles)

    horas_por_grupo = {g: horas_ingles[i] for i, g in enumerate(grupos)}
    slots_ingles_por_grupo = {g: set() for g in grupos}

    for g in grupos:
        materia_ingles = next(
            (m for m in SUBJECTS[g] if norm(m["id"]).startswith("ingles")),
            None
        )
        if not materia_ingles:
            continue

        prof, room = get_prof_room(materia_ingles["id"], g)
        hora = horas_por_grupo[g]

        for dia in DAYS:
            slot = f"{dia}{hora:02d}"
            if grupo_materia_horas[(g, materia_ingles["id"])] > 0:
                asignaciones.append({
                    "group": g,
                    "subj": materia_ingles["id"],
                    "start": slot,
                    "room": room,
                    "prof": prof
                })
                grupo_materia_horas[(g, materia_ingles["id"])] -= 1
                slots_ingles_por_grupo[g].add(slot)

    # --------------------------------------------------------
    # 2. Asignar el resto de materias
    # --------------------------------------------------------
    for slot in SLOTS:
        dia = slot[:3]
        hora_slot = int(slot[-2:])

        profes_slot = {a["prof"] for a in asignaciones if a["start"] == slot}
        rooms_slot = {a["room"] for a in asignaciones if a["start"] == slot}

        grupos_pend = list(SUBJECTS.keys())
        random.shuffle(grupos_pend)

        for g in grupos_pend:

            if slot in slots_ingles_por_grupo[g]:
                continue

            materias_disponibles = [
                m for m in SUBJECTS[g]
                if grupo_materia_horas[(g, m["id"])] > 0
                and not norm(m["id"]).startswith("ingles")
            ]

            opciones = []

            for m in materias_disponibles:
                materia_id = m["id"]
                prof, room = get_prof_room(materia_id, g)
                allow_double_block = bool(m.get("allow_double_block", False))

                # min_hora se interpreta como bloque de 1 a 6
                min_hora = m.get("min_hora")
                if min_hora is not None and hora_slot < min_hora:
                    continue

                # Regla por materia en el dia:
                # por defecto una sola vez; si allow_double_block=true, maximo 2 y consecutivas
                if not es_doble_consecutivo_valido(asignaciones, g, materia_id, slot, allow_double_block):
                    continue

                if prof in profes_slot:
                    continue
                if room in rooms_slot:
                    continue

                opciones.append((materia_id, prof, room))

            if not opciones:
                continue

            materia_id, prof, room = opciones[0]

            asignaciones.append({
                "group": g,
                "subj": materia_id,
                "start": slot,
                "room": room,
                "prof": prof
            })

            grupo_materia_horas[(g, materia_id)] -= 1
            profes_slot.add(prof)
            rooms_slot.add(room)

    # --------------------------------------------------------
    # 3. Métrica de huecos
    # --------------------------------------------------------
    total_slots = len(SUBJECTS) * len(SLOTS)
    usados = len(asignaciones)
    huecos = total_slots - usados

    return asignaciones, huecos


# ============================================================
# BÚSQUEDA DE MEJOR SOLUCIÓN
# ============================================================
best_asignaciones = None
min_huecos = float('inf')

for intento in range(1000):
    asignaciones, huecos = run_greedy()
    if huecos < min_huecos:
        min_huecos = huecos
        best_asignaciones = copy.deepcopy(asignaciones)
    if min_huecos == 0:
        print(f"Solución perfecta encontrada en el intento {intento+1}!")
        break
else:
    print(f"Mejor solución tiene {min_huecos} huecos tras 1000 intentos.")


# ============================================================
# GUARDAR HORARIO
# ============================================================
with open(horario_greedy_path, "w", encoding="utf-8") as f:
    json.dump(best_asignaciones, f, ensure_ascii=False, indent=4)

with open("horario_greedy.json", "w", encoding="utf-8") as f:
    json.dump(best_asignaciones, f, ensure_ascii=False, indent=4)


# ============================================================
# DETECTAR MATERIAS NO ASIGNADAS
# ============================================================
def materias_fuera(asignaciones):
    horas_restantes = {
        (g, m["id"]): m["H"]
        for g in SUBJECTS
        for m in SUBJECTS[g]
    }

    for a in asignaciones:
        horas_restantes[(a["group"], a["subj"])] -= 1

    return [
        {"group": g, "materia": m, "horas_faltantes": h}
        for (g, m), h in horas_restantes.items()
        if h > 0
    ]


fuera = materias_fuera(best_asignaciones)

if fuera:
    print("Materias que quedaron fuera:")
    for f in fuera:
        print(f)

    with open(materias_fuera_path, "w", encoding="utf-8") as f_json:
        json.dump(fuera, f_json, ensure_ascii=False, indent=4)

   
else:
    print("¡Todas las materias fueron asignadas completamente!")


# ============================================================
# REPORTE RESUMEN
# ============================================================
print("\nResumen de horas asignadas por grupo y materia:")
asignadas_por_materia = {
    (g, m["id"]): 0
    for g in SUBJECTS
    for m in SUBJECTS[g]
}

for a in best_asignaciones:
    asignadas_por_materia[(a["group"], a["subj"])] += 1

for g in SUBJECTS:
    print(f"\nGrupo {g}:")
    for subj in SUBJECTS[g]:
        h_asig = asignadas_por_materia[(g, subj["id"])]
        h_req = subj["H"]
        status = (
            "OK"
            if h_asig == h_req
            else f"FALTAN {h_req - h_asig}"
            if h_asig < h_req
            else f"SOBRAN {h_asig - h_req}"
        )
        print(f"  {subj['id']}: {h_asig}/{h_req}  [{status}]")
