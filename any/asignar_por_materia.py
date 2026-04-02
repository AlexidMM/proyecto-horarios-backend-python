from ortools.sat.python import cp_model
import json

# Importar datos y parámetros del modelo original
from cp_sat_schedule import SUBJECTS, SLOTS, ROOMS, PROFS, SLOTS_PER_DAY, DAYS

def asignar_materia_por_materia():
    # Orden de materias a asignar (puedes personalizar el orden)
    materias_orden = ["administracion del tiempo", "Matematicas para ingenieria", "Arquitectura de software", "Ingles", "Metodologia de desarrollo de proyectos", "Experiencia de usuario", "Seguridad informatica"]
    asignaciones = []
    ocupados = set()  # (slot, room, prof, group)
    for materia in materias_orden:
        print(f"\nAsignando materia: {materia}")
        model = cp_model.CpModel()
        x_vars = {}
        for g in SUBJECTS:
            subj = next((s for s in SUBJECTS[g] if s["id"].lower() == materia.lower()), None)
            if not subj:
                continue
            for h in range(subj["H"]):
                for s_idx, s in enumerate(SLOTS):
                    for r in subj["rooms"]:
                        for p in subj["profs"]:
                            key = (g, h, s_idx, r, p)
                            if (s_idx, r, p, g) in ocupados:
                                continue
                            var = model.NewBoolVar(f"x_{g}_{materia}_{h}_{s}_{r}_{p}")
                            x_vars[key] = var
        # Restricción: cada hora de la materia debe ser asignada exactamente una vez por grupo
        for g in SUBJECTS:
            subj = next((s for s in SUBJECTS[g] if s["id"].lower() == materia.lower()), None)
            if not subj:
                continue
            for h in range(subj["H"]):
                model.AddExactlyOne(
                    x_vars[key] for key in x_vars if key[0] == g and key[1] == h
                )
        # Restricción: no solapar en slot, room, prof, group
        for s_idx, s in enumerate(SLOTS):
            for r in ROOMS:
                for p in PROFS:
                    for g in SUBJECTS:
                        keys = [key for key in x_vars if key[2] == s_idx and key[3] == r and key[4] == p and key[0] == g]
                        if len(keys) > 1:
                            model.Add(sum(x_vars[k] for k in keys) <= 1)

        # OBJETIVO: minimizar la dispersión de los slots para cada materia y grupo
        # Para cada grupo, penalizar la suma de las diferencias absolutas entre slots asignados
        dispersion_terms = []
        for g in SUBJECTS:
            subj = next((s for s in SUBJECTS[g] if s["id"].lower() == materia.lower()), None)
            if not subj:
                continue
            # Obtener las variables de slots asignados
            slot_vars = []
            for h in range(subj["H"]):
                for key in x_vars:
                    if key[0] == g and key[1] == h:
                        slot_vars.append((key, x_vars[key]))
            # Penalizar la diferencia entre slots asignados
            for i in range(len(slot_vars)):
                for j in range(i+1, len(slot_vars)):
                    s_idx_i = slot_vars[i][0][2]
                    s_idx_j = slot_vars[j][0][2]
                    diff = abs(s_idx_i - s_idx_j)
                    # Solo penalizar si ambos están asignados
                    b = model.NewBoolVar(f"disp_{g}_{materia}_{i}_{j}")
                    model.Add(x_vars[slot_vars[i][0]] + x_vars[slot_vars[j][0]] == 2).OnlyEnforceIf(b)
                    model.Add(x_vars[slot_vars[i][0]] + x_vars[slot_vars[j][0]] < 2).OnlyEnforceIf(b.Not())
                    dispersion_terms.append(b * diff)

        if dispersion_terms:
            model.Minimize(sum(dispersion_terms))

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10.0
        result = solver.Solve(model)
        if result not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            print(f"No se pudo asignar la materia {materia} en todos los grupos.")
            continue
        for key, var in x_vars.items():
            if solver.Value(var) == 1:
                g, h, s_idx, r, p = key
                asignaciones.append({
                    "group": g,
                    "materia": materia,
                    "hora": h,
                    "slot": SLOTS[s_idx],
                    "room": r,
                    "prof": p
                })
                ocupados.add((s_idx, r, p, g))
    # Guardar resultado
    with open("asignaciones_por_materia.json", "w", encoding="utf-8") as f:
        json.dump(asignaciones, f, ensure_ascii=False, indent=4)
    print("\nAsignaciones guardadas en asignaciones_por_materia.json")

if __name__ == "__main__":
    asignar_materia_por_materia()
