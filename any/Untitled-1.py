
# cp_sat_schedule_sequential.py
# Modelo CP-SAT secuencial por grado/instancia (OR-Tools)
# Requisitos: pip install ortools
from ortools.sat.python import cp_model
import json

# --- Configuración básica ---
SLOTS_PER_DAY = 5  # 17,18,19,20,21
DAYS = ["Lun", "Mar", "Mie", "Jue", "Vie"]
SLOTS = [f"{d}{17+i}" for d in DAYS for i in range(SLOTS_PER_DAY)]
slot2day = {s: (s[:3], int(s[3:]) - 17) for s in SLOTS}

ROOMS = ["12k", "13k", "12j", "13j", "10j", "11j"]
PROFS = ["juan martin", "Lucas", "Gabriel", "P3", "P4", "P2"]
# Plantillas por grado (subjects por grado)
SUBJECTS = {
    "1ro": [ 
        {"id": "fisica 1", "H": 3, "rooms": ["12k", "13k"], "profs": ["juan martin"]}, 
        {"id": "Algebra", "H": 2, "rooms": ["12k"], "profs": ["Lucas"]}, 
        {"id": "introduccion a la programacion", "H": 5, "rooms": ["12j","13j"], "profs": ["Gabriel"]}, 
    ],
    "2do": [ 
        {"id": "fisica 2", "H": 2, "rooms": ["12k","13k"], "profs": ["P3"]}, 
        {"id": "calculo diferencial", "H": 3, "rooms": ["13k"], "profs": ["P4"]}, 
        {"id": "programacion web", "H": 3, "rooms": ["10j","11j"], "profs": ["P2","P4"]}, 
    ]
}

# Instances of groups to schedule sequentially: list of (grade, instance_id)
GROUP_INSTANCES = [
    ("1ro", "A"),
    ("1ro", "B"),
    ("2do", "A"),
]

# Helper: generate patterns (greedy + spread if H<=5)
def generate_patterns(H, allow_spread=True):
    patterns = []
    rem = H
    pat = []
    while rem >= 2:
        pat.append(2)
        rem -= 2
    if rem == 1:
        pat.append(1)
    patterns.append(("greedy", pat))
    if allow_spread and H <= 5:
        patterns.append(("spread", [1]*H))
    return patterns

def build_units_for_grade(grade):
    units = []
    patterns_by_subj = {}
    unit_counter = 0
    for subj in SUBJECTS[grade]:
        key = (grade, subj["id"])
        pats = generate_patterns(subj["H"], allow_spread=True)
        patterns_by_subj[key] = []
        for pidx, (pname, pat) in enumerate(pats):
            u_indices = []
            for u_local_idx, ulen in enumerate(pat):
                uid = f"u_{grade}_{subj['id']}_pat{pidx}_#{u_local_idx}"
                units.append({
                    "uid": uid,
                    "grade": grade,
                    "subj": subj["id"],
                    "pat_key": f"pat{pidx}",
                    "pat_idx": pidx,
                    "len": ulen,
                    "allowed_rooms": subj["rooms"],
                    "allowed_profs": subj["profs"]
                })
                u_indices.append(unit_counter)
                unit_counter += 1
            patterns_by_subj[key].append({
                "pat_key": f"pat{pidx}",
                "pat_type": pname,
                "units": u_indices
            })
    return units, patterns_by_subj

# Function to schedule one group instance given reserved resources
def schedule_instance(grade, inst_id, reserved_room_slot=set(), reserved_prof_slot=set(), time_limit=20):
    print(f"Scheduling instance: {grade}-{inst_id} (reserved slots: rooms={len(reserved_room_slot)}, profs={len(reserved_prof_slot)})")
    units, patterns_by_subj = build_units_for_grade(grade)
    model = cp_model.CpModel()

    ROOM_INDEX = {r: i for i, r in enumerate(ROOMS)}
    PROF_INDEX = {p: i for i, p in enumerate(PROFS)}
    SLOT_INDEX = {s: i for i, s in enumerate(SLOTS)}

    # z variables
    z_vars = {}
    for key, pat_list in patterns_by_subj.items():
        g, subj = key
        for pat in pat_list:
            var = model.NewBoolVar(f"z_{g}_{subj}_{pat['pat_key']}")
            z_vars[(g, subj, pat['pat_key'])] = var
        model.Add(sum(z_vars[(g, subj, pat['pat_key'])] for pat in pat_list) == 1)

    # x variables, but skip starts that would conflict with reserved sets
    x_vars = {}
    for ui, u in enumerate(units):
        ulen = u["len"]
        allowed_rooms = u["allowed_rooms"]
        allowed_profs = u["allowed_profs"]
        for s_idx, s in enumerate(SLOTS):
            day = s[:3]; idx_in_day = int(s[3:]) - 17
            if ulen == 2 and idx_in_day >= SLOTS_PER_DAY - 1:
                continue
            # compute occupied slots indices for this start
            occ_slot_indices = [s_idx + off for off in range(ulen)]
            # check reserved conflicts for any (slot,room) or (slot,prof)
            for r in allowed_rooms:
                room_conflict = False
                for t in occ_slot_indices:
                    if (t, r) in reserved_room_slot:
                        room_conflict = True
                        break
                if room_conflict:
                    continue
                for p in allowed_profs:
                    prof_conflict = False
                    for t in occ_slot_indices:
                        if (t, p) in reserved_prof_slot:
                            prof_conflict = True
                            break
                    if prof_conflict:
                        continue
                    var = model.NewBoolVar(f"x_u{ui}_s{s}_r{r}_p{p}")
                    x_vars[(ui, s_idx, ROOM_INDEX[r], PROF_INDEX[p])] = var
                    zvar = z_vars[(u["grade"], u["subj"], f"pat{u['pat_idx']}")]
                    model.Add(var <= zvar)

    # Each unit assigned once if pattern chosen
    for (g, subj), pat_list in patterns_by_subj.items():
        for pat in pat_list:
            zvar = z_vars[(g, subj, pat["pat_key"])]
            for ui in pat["units"]:
                sum_terms = []
                for (u_idx, s_idx, r_idx, p_idx), var in x_vars.items():
                    if u_idx == ui:
                        sum_terms.append(var)
                if not sum_terms:
                    model.Add(zvar == 0)
                else:
                    model.Add(sum(sum_terms) == zvar)

    # Room occupancy
    for r_idx, r in enumerate(ROOMS):
        for t_idx, t in enumerate(SLOTS):
            occ_terms = []
            for (u_idx, s_idx, rr_idx, p_idx), var in x_vars.items():
                if rr_idx != r_idx: continue
                ulen = units[u_idx]["len"]
                if s_idx <= t_idx <= s_idx + ulen - 1:
                    occ_terms.append(var)
            if occ_terms:
                model.Add(sum(occ_terms) <= 1)

    # Professor occupancy
    for p_idx, p in enumerate(PROFS):
        for t_idx, t in enumerate(SLOTS):
            occ_terms = []
            for (u_idx, s_idx, rr_idx, pp_idx), var in x_vars.items():
                if pp_idx != p_idx: continue
                ulen = units[u_idx]["len"]
                if s_idx <= t_idx <= s_idx + ulen - 1:
                    occ_terms.append(var)
            if occ_terms:
                model.Add(sum(occ_terms) <= 1)

    # Grade (group instance) occupancy
    for t_idx, t in enumerate(SLOTS):
        occ_terms = []
        for (u_idx, s_idx, rr_idx, pp_idx), var in x_vars.items():
            ugrade = units[u_idx]["grade"]
            if ugrade != grade: continue
            ulen = units[u_idx]["len"]
            if s_idx <= t_idx <= s_idx + ulen - 1:
                occ_terms.append(var)
        if occ_terms:
            model.Add(sum(occ_terms) <= 1)

    # y variables for contiguity (per grade/day)
    y_vars = {}
    for d_idx, d in enumerate(DAYS):
        for idx_in_day in range(SLOTS_PER_DAY):
            y = model.NewBoolVar(f"y_{grade}_{d}_{idx_in_day}")
            y_vars[(d_idx, idx_in_day)] = y
            occ_terms = []
            t_idx = d_idx * SLOTS_PER_DAY + idx_in_day
            for (u_idx, s_idx, rr_idx, pp_idx), var in x_vars.items():
                if units[u_idx]["grade"] != grade: continue
                ulen = units[u_idx]["len"]
                if s_idx <= t_idx <= s_idx + ulen - 1:
                    occ_terms.append(var)
            if occ_terms:
                model.AddMaxEquality(y, occ_terms)
            else:
                model.Add(y == 0)

    # Contiguity triples
    for a in range(SLOTS_PER_DAY):
        for b in range(a+1, SLOTS_PER_DAY):
            for c in range(b+1, SLOTS_PER_DAY):
                ya = y_vars[(a)]
                yb = y_vars[(b)]
                yc = y_vars[(c)]
                model.Add(ya + yc - 1 <= yb)

    # gap indicators
    gap_terms = []
    for a in range(SLOTS_PER_DAY):
        for b in range(a+1, SLOTS_PER_DAY):
            for c in range(b+1, SLOTS_PER_DAY):
                ya = y_vars[(a)]
                yb = y_vars[(b)]
                yc = y_vars[(c)]
                g_abc = model.NewBoolVar(f"gap_{grade}_{a}_{b}_{c}")
                model.Add(g_abc <= ya)
                model.Add(g_abc <= yc)
                model.Add(g_abc + yb <= 1)
                model.Add(g_abc >= ya + yc - 1 - yb)
                gap_terms.append(g_abc)

    # Prefer spread patterns slightly
    spread_penalties = []
    for (g, subj), pat_list in patterns_by_subj.items():
        for pat in pat_list:
            if pat["pat_type"] == "spread":
                zvar = z_vars[(g, subj, pat["pat_key"])]
                s_var = model.NewIntVar(0, 1, f"spread_pen_{g}_{subj}_{pat['pat_key']}")
                model.Add(s_var == 1 - zvar)
                spread_penalties.append(s_var)

    W_GAP = 10
    W_SPREAD = 1
    model.Minimize(W_GAP * sum(gap_terms) + W_SPREAD * sum(spread_penalties))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = 8
    result = solver.Solve(model)

    if result in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        assignments = []
        for (u_idx, s_idx, r_idx, p_idx), var in x_vars.items():
            if solver.Value(var) == 1:
                u = units[u_idx]
                s_name = SLOTS[s_idx]
                r_name = ROOMS[r_idx]
                p_name = PROFS[p_idx]
                assignments.append({
                    "unit": u["uid"],
                    "grade": u["grade"],
                    "subj": u["subj"],
                    "len": u["len"],
                    "start": s_name,
                    "room": r_name,
                    "prof": p_name
                })
        chosen_patterns = []
        for (g, subj), pat_list in patterns_by_subj.items():
            for pat in pat_list:
                zvar = z_vars[(g, subj, pat["pat_key"])]
                if solver.Value(zvar) == 1:
                    chosen_patterns.append({"grade": g, "subj": subj, "chosen": pat["pat_key"], "type": pat["pat_type"]})
        return True, assignments, chosen_patterns
    else:
        return False, None, None

# Sequential loop: schedule instances and reserve resources
def run_sequential():
    reserved_room_slot = set()   # (slot_idx, room)
    reserved_prof_slot = set()   # (slot_idx, prof_name)
    all_results = {}
    for grade, inst in GROUP_INSTANCES:
        ok, assignments, patterns = schedule_instance(grade, inst, reserved_room_slot, reserved_prof_slot, time_limit=20)
        key = f"{grade}-{inst}"
        if not ok:
            print(f"FAILED to schedule {key}")
            all_results[key] = {"status": "failed"}
            continue
        print(f"Scheduled {key}: {len(assignments)} units")
        all_results[key] = {"status": "ok", "assignments": assignments, "patterns": patterns}
        # reserve the occupied (slot,room) and (slot,prof)
        for a in assignments:
            s_idx = SLOTS.index(a["start"])
            for off in range(a["len"]):
                t = s_idx + off
                reserved_room_slot.add((t, a["room"]))
                reserved_prof_slot.add((t, a["prof"]))
    # save results json
    with open("scheduling_results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print("Finished sequential scheduling. Results saved to scheduling_results.json")

if __name__ == '__main__':
    run_sequential()
