

from ortools.sat.python import cp_model
import json

# Cargar los mismos datos y parámetros que el modelo principal
from cp_sat_schedule import SUBJECTS, SLOTS, ROOMS, PROFS, SLOTS_PER_DAY, DAYS

def diagnostico():
    print("--- DIAGNÓSTICO DE FACTIBILIDAD ---")
    total_slots = len(SLOTS)
    total_rooms = len(ROOMS)
    total_profs = len(PROFS)
    print(f"Slots disponibles: {total_slots}")
    print(f"Aulas disponibles: {total_rooms}")
    print(f"Profesores disponibles: {total_profs}")
    for g, materias in SUBJECTS.items():
        print(f"\nGrupo {g}:")
        total_horas = sum(m['H'] for m in materias)
        print(f"  Total de horas a asignar: {total_horas}")
        if total_horas > total_slots:
            print("  ⚠️ Más horas que slots disponibles. Imposible.")
        for m in materias:
            if m['H'] > SLOTS_PER_DAY:
                print(f"  ⚠️ Materia '{m['id']}' requiere más horas ({m['H']}) que slots por día ({SLOTS_PER_DAY})")
            if len(m['rooms']) == 0:
                print(f"  ⚠️ Materia '{m['id']}' no tiene aulas asignadas.")
            if len(m['profs']) == 0:
                print(f"  ⚠️ Materia '{m['id']}' no tiene profesor asignado.")
    print("\nSugerencias para suavizar restricciones:")
    print("- Permitir bloques de 3 horas para algunas materias si es necesario.")
    print("- Relajar la restricción de inglés aún más (por ejemplo, solo mismo día, no mismo slot).")
    print("- Permitir que una materia se imparta en más de un aula/profesor si es posible.")
    print("- Aumentar el número de slots por día o días disponibles.")
    print("- Revisar si hay materias con muchas horas y pocos recursos.")

if __name__ == "__main__":
    diagnostico()
