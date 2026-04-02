# cp_sat_full_schedule.py
"""
Modelo CP-SAT para maximizar la ocupación de slots en el horario universitario.
- Cero solapamientos (profesor, aula, grupo, inglés, etc.)
- Todos los slots deben estar ocupados
"""



from ortools.sat.python import cp_model
import json

# DATOS DE PRUEBA
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

# Definir slots: 5 días x 5 horas = 25 slots
slots = [(dia, hora) for dia in range(5) for hora in range(5)]

# Construir listas y diccionarios requeridos
grupos = list(SUBJECTS.keys())
materias = sorted({subj['id'] for group in SUBJECTS.values() for subj in group})
profesores = sorted({prof for group in SUBJECTS.values() for subj in group for prof in subj['profs']})
aulas = sorted({room for group in SUBJECTS.values() for subj in group for room in subj['rooms']})

# Horas por materia (por grupo)
horas_por_materia = {m: 0 for m in materias}
for group in SUBJECTS.values():
    for subj in group:
        horas_por_materia[subj['id']] = subj['H']

# Profesor por materia (asume 1 profe por materia por grupo)
profesor_por_materia = {}
for group in SUBJECTS.values():
    for subj in group:
        profesor_por_materia[subj['id']] = subj['profs'][0]

# Aula por materia (asume 1 aula por materia por grupo)
aula_por_materia = {}
for group in SUBJECTS.values():
    for subj in group:
        aula_por_materia[subj['id']] = subj['rooms'][0]

# Materia es inglés
materia_es_ingles = {m: ("ingles" in m.lower()) for m in materias}

model = cp_model.CpModel()

# Variables: x[g][s][m] = 1 si grupo g tiene materia m en slot s
x = {}
for g in grupos:
    for s in range(len(slots)):
        for m in materias:
            x[g, s, m] = model.NewBoolVar(f'x_{g}_{s}_{m}')

# 1. Cada slot de cada grupo debe estar ocupado por exactamente una materia
for g in grupos:
    for s in range(len(slots)):
        model.AddExactlyOne(x[g, s, m] for m in materias)

# 2. Cada materia debe asignarse el número correcto de horas por grupo
for g in grupos:
    for m in materias:
        model.Add(sum(x[g, s, m] for s in range(len(slots))) == horas_por_materia[m])

# 3. Un profesor no puede estar en dos grupos en el mismo slot
for p in profesores:
    for s in range(len(slots)):
        model.Add(sum(x[g, s, m] for g in grupos for m in materias if profesor_por_materia[m] == p) <= 1)

# 4. Un aula no puede estar en dos grupos en el mismo slot
for a in aulas:
    for s in range(len(slots)):
        model.Add(sum(x[g, s, m] for g in grupos for m in materias if aula_por_materia[m] == a) <= 1)

# 5. (Opcional) Inglés en el mismo slot para cada grupo
for g in grupos:
    ingles_slots = [s for s in range(len(slots)) for m in materias if materia_es_ingles.get(m, False)]
    if ingles_slots:
        # Fuerza que todos los slots de inglés sean el mismo para el grupo
        for s in range(len(slots)):
            for m in materias:
                if materia_es_ingles.get(m, False):
                    model.Add(x[g, s, m] == x[g, ingles_slots[0], m])

# 6. (Opcional) No más de 2 horas seguidas de la misma materia por grupo
for g in grupos:
    for m in materias:
        for s in range(len(slots) - 2):
            model.Add(sum(x[g, s + offset, m] for offset in range(3)) <= 2)

# 7. (Opcional) Maximizar slots ocupados (pero ya están todos ocupados por restricción 1)
# Si quieres permitir huecos, puedes cambiar la restricción 1 y maximizar la suma de x

# Resolver
solver = cp_model.CpSolver()
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    horario = {}
    for g in grupos:
        horario[g] = []
        for s in range(len(slots)):
            for m in materias:
                if solver.Value(x[g, s, m]):
                    horario[g].append({'slot': slots[s], 'materia': m})
    with open('horario_cp_sat.json', 'w', encoding='utf-8') as f:
        json.dump(horario, f, ensure_ascii=False, indent=2)
    print('¡Horario generado y guardado en horario_cp_sat.json!')
else:
    print('No se encontró solución factible.')
