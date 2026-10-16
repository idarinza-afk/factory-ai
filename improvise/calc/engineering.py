"""Common machine-design calculations used by the skills.

All formulas are standard first-order engineering estimates; results are for
sizing and proposals and must be confirmed with supplier data.
"""

from __future__ import annotations

import math

from ..tools import tool

G = 9.81
IEC_MOTORS_KW = [0.09, 0.12, 0.18, 0.25, 0.37, 0.55, 0.75, 1.1, 1.5, 2.2, 3.0, 4.0, 5.5, 7.5, 11, 15, 18.5, 22,
                 30, 37, 45, 55, 75, 90, 110, 132, 160, 200, 250, 315]


def next_motor(kw: float) -> float:
    for m in IEC_MOTORS_KW:
        if m >= kw:
            return m
    return math.ceil(kw)


# Running friction belt/chain -> bed. modular dry/wet: Rexnord TableTop/MatTop manual (acetal on UHMWPE 0.25 dry,
# 0.21 water); flat dry: ISO 5048 belt on steel 0.3-0.4. Values marked allowance are engineering allowances from
# field experience (wet PU/PVC belts suck onto flat stainless slider beds; sauce, sugar, starch, fat make it sticky):
# calibrate them on site from the measured motor current.
FRICTION = {("flat", "dry"): 0.30, ("flat", "wet"): 0.50, ("flat", "sticky"): 0.60,
            ("modular", "dry"): 0.25, ("modular", "wet"): 0.21, ("modular", "sticky"): 0.35,
            ("roller_bed", "dry"): 0.05, ("roller_bed", "wet"): 0.06, ("roller_bed", "sticky"): 0.10}
BREAKAWAY = {"dry": 1.3, "wet": 1.8, "sticky": 2.0}  # static / running friction after a standstill (allowance)
DRUM_FRICTION = {("lagged", "dry"): 0.40, ("lagged", "wet"): 0.30, ("lagged", "sticky"): 0.25,
                 ("bare", "dry"): 0.35, ("bare", "wet"): 0.15, ("bare", "sticky"): 0.10}  # belt on drive drum
TRANSMISSION_FZ = {"direct": 1.0, "chain": 1.25, "gear": 1.15, "v_belt": 1.75, "timing_belt": 2.25, "flat_belt": 2.5}


@tool
def conveyor_sizing(length_m: float, rate_per_min: float, pitch_mm: float, product_mass_kg: float,
                    belt_mass_kg_per_m: float = 3.0, friction: float = 0, incline_deg: float = 0,
                    efficiency: float = 0.8, service_factor: float = 1.5, belt_type: str = "flat",
                    condition: str = "dry", drive_pulley_mm: float = 100, pulley_surface: str = "lagged",
                    accel_time_s: float = 1.0, transmission: str = "direct", drive_element_mm: float = 0,
                    product_length_mm: float = 0, gap_mm: float = -1) -> dict:
    """Belt/chain conveyor: speed, belt pull, running AND starting torque, shaft load, motor size, wet/dry effects.

    Args:
        length_m: conveyor length between pulley centres in m
        rate_per_min: products per minute to transport
        pitch_mm: spacing between products on the belt in mm = product length + gap (e.g. 250 mm tray + 150 mm gap = 400)
        product_mass_kg: mass of one product in kg
        belt_mass_kg_per_m: belt/chain mass per metre of conveyor length, default 3.0
        friction: belt-to-bed running friction; 0 = from belt_type and condition
        incline_deg: incline angle in degrees, default 0
        efficiency: drive efficiency (gearbox etc.), default 0.8
        service_factor: gearbox/motor service factor for the duty, default 1.5
        belt_type: flat (PU/PVC belt on slider bed), modular (plastic modular / table-top chain on wear strips), roller_bed
        condition: dry, wet (water, washdown, wet product) or sticky (sauce, sugar, starch, fat residue)
        drive_pulley_mm: drive pulley / sprocket pitch diameter in mm, default 100
        pulley_surface: lagged or bare drive pulley (flat belts), default lagged
        accel_time_s: start-up time to full speed in s, default 1.0
        transmission: how the gearmotor drives the pulley shaft: direct (hollow/coupled shaft), chain, gear, v_belt, timing_belt
        drive_element_mm: pitch diameter of the sprocket/pulley ON THE GEARMOTOR shaft when transmission is not direct
        product_length_mm: optional - with gap_mm, the pitch is product_length_mm + gap_mm (overrides pitch_mm)
        gap_mm: optional gap between products in mm (use with product_length_mm)
    """
    if product_length_mm and gap_mm >= 0:
        pitch_mm = product_length_mm + gap_mm
    belt_type = belt_type.lower().replace(" ", "_").replace("-", "_")
    belt_type = {"belt": "flat", "pu": "flat", "pvc": "flat", "slider_bed": "flat", "chain": "modular",
                 "table_top": "modular", "rollers": "roller_bed", "roller": "roller_bed"}.get(belt_type, belt_type)
    condition = {"washdown": "wet", "water": "wet", "dirty": "sticky", "oily": "sticky"}.get(condition.lower(), condition.lower())
    if (belt_type, condition) not in FRICTION:
        raise ValueError("belt_type must be flat, modular or roller_bed; condition dry, wet or sticky")
    mu = friction or FRICTION[(belt_type, condition)]
    v = rate_per_min * pitch_mm / 1000 / 60  # m/s
    load = length_m / (pitch_mm / 1000) * product_mass_kg
    belt = 2 * length_m * belt_mass_kg_per_m
    th = math.radians(incline_deg)
    force = G * (mu * (load + belt) * math.cos(th) + load * math.sin(th))
    k_break = BREAKAWAY[condition] if belt_type != "roller_bed" else 1.2
    force_start = G * (mu * k_break * (load + belt) * math.cos(th) + load * math.sin(th)) + (load + belt) * v / accel_time_s
    r = drive_pulley_mm / 2000
    t_run, t_start = force * r, force_start * r
    rpm = v / (math.pi * drive_pulley_mm / 1000) * 60
    p_shaft = force * v / 1000
    p_motor = p_shaft / efficiency * service_factor
    # a standard motor gives about 1.5-2x rated torque while starting: size so the start needs <= 1.5x rated
    p_start = t_start * rpm * 2 * math.pi / 60 / 1000 / efficiency / 1.5
    selected = next_motor(max(p_motor, p_start))
    # belt tensions and the load they put on the drive shaft
    if belt_type == "flat":
        mu_d = DRUM_FRICTION[(pulley_surface.lower(), condition)]
        euler = math.exp(mu_d * math.pi)  # 180 deg wrap
        t2 = force_start / (euler - 1) * 1.2  # minimum slack-side tension + 20 %
        t1 = force_start + t2
        slip_note = (f"drive pulley ({pulley_surface}, {condition}) needs >= {t2:.0f} N slack-side tension "
                     "(take-up) not to slip at start")
    else:  # positive sprocket drive: no slip, little slack-side tension
        t1, t2, slip_note = force_start * 1.1, force_start * 0.1, "sprocket drive: no slip; keep catenary sag on the return"
    shaft_load = t1 + t2
    fz = TRANSMISSION_FZ.get(transmission.lower(), 1.0)
    gm_radial = 2000 * t_start / drive_element_mm * fz if transmission.lower() != "direct" and drive_element_mm else 0
    warnings = []
    if belt_type == "flat" and condition != "dry":
        warnings.append("Wet/sticky flat belt on a flat stainless slider bed: the belt sucks onto the bed and drag can "
                        "rise sharply. Prefer a perforated/grooved slider bed, UHMW strips or a roller bed, a belt with "
                        "a structured underside, and a lagged drive pulley.")
    if condition != "dry":
        warnings.append("Friction for wet/sticky running is an allowance: confirm on site by measuring motor current "
                        "under the real condition and record it as a verified case.")
    return {"pitch_mm_used": pitch_mm, "speed_m_per_min": round(v * 60, 2), "speed_m_per_s": round(v, 3),
            "load_on_belt_kg": round(load, 1), "belt_type": belt_type, "condition": condition, "friction_used": mu,
            "effective_pull_N": round(force, 1), "starting_pull_N": round(force_start, 1),
            "drive_pulley_rpm": round(rpm, 1), "running_torque_Nm": round(t_run, 1), "starting_torque_Nm": round(t_start, 1),
            "required_gearbox_output_torque_Nm": round(t_run * service_factor, 1),
            "belt_tension_T1_N": round(t1), "belt_tension_T2_N": round(t2),
            "drive_shaft_radial_load_N": round(shaft_load),
            **({"gearmotor_shaft_radial_load_N": round(gm_radial)} if gm_radial else {}),
            "shaft_power_kW": round(p_shaft, 3), "required_motor_kW": round(max(p_motor, p_start), 3),
            "selected_motor_kW": selected, "slip_check": slip_note, "warnings": warnings,
            "next_step": ("Choose a gearmotor from the brand's catalogue and run gearmotor_check with its datasheet values "
                          "(rated output torque, output rpm, output shaft diameter, permissible radial load): kW alone "
                          "does not prove the shaft and gearbox can take this load.")}


@tool
def gearmotor_check(running_torque_Nm: float, starting_torque_Nm: float, required_rpm: float, radial_load_N: float,
                    rated_output_torque_Nm: float = 0, output_rpm: float = 0, motor_kW: float = 0,
                    output_shaft_mm: float = 0, permissible_radial_load_N: float = 0, catalogue_service_factor: float = 0,
                    required_service_factor: float = 1.5, starting_torque_ratio: float = 0, load_offset_mm: float = 0,
                    brand_model: str = "") -> dict:
    """Check ONE gearmotor from a brand's datasheet against the conveyor load: output torque, starting torque, speed,
    permissible radial (overhung) load on the output shaft and shaft stress. Every brand differs - use its datasheet.

    Args:
        running_torque_Nm: load torque at the output shaft while running (conveyor_sizing running_torque_Nm)
        starting_torque_Nm: load torque at start / breakaway (conveyor_sizing starting_torque_Nm)
        required_rpm: output speed needed (conveyor_sizing drive_pulley_rpm)
        radial_load_N: radial load on the gearmotor output shaft (drive_shaft_radial_load_N if the pulley is on it,
            gearmotor_shaft_radial_load_N for a chain/belt drive, 0 for a hollow shaft with its own bearings)
        rated_output_torque_Nm: datasheet output torque Ma (or Mn) of this gearmotor
        output_rpm: datasheet output speed
        motor_kW: datasheet motor power
        output_shaft_mm: datasheet output shaft diameter
        permissible_radial_load_N: datasheet permissible radial/overhung load FRa at the shaft middle
        catalogue_service_factor: datasheet service factor fB (= gearbox rating / motor torque); 0 if not given
        required_service_factor: duty service factor needed (starts/h, shocks, hours/day), default 1.5
        starting_torque_ratio: motor starting torque / rated torque from the datasheet (MA/MN); 0 = assume 1.6 (DOL IE3)
        load_offset_mm: distance from the shaft shoulder to the load centre (pulley/sprocket); 0 = shaft middle
        brand_model: brand and type, for the report
    """
    missing = [n for n, v in (("rated_output_torque_Nm", rated_output_torque_Nm), ("output_rpm", output_rpm),
                              ("output_shaft_mm", output_shaft_mm),
                              ("permissible_radial_load_N", permissible_radial_load_N if radial_load_N else 1)) if not v]
    checks, ok_all = [], True

    def add(name, ok, text):
        nonlocal ok_all
        ok_all = ok_all and ok
        checks.append({"check": name, "ok": ok, "detail": text})

    if rated_output_torque_Nm:
        need = running_torque_Nm * required_service_factor
        add("output torque", rated_output_torque_Nm >= need,
            f"rated {rated_output_torque_Nm:g} Nm vs running {running_torque_Nm:g} x SF {required_service_factor:g} = {need:.1f} Nm")
        ratio = starting_torque_ratio or 1.6
        avail = rated_output_torque_Nm * ratio
        add("starting torque", avail >= starting_torque_Nm,
            f"about {avail:.1f} Nm available at start ({ratio:g} x rated{'' if starting_torque_ratio else ', assumed'}) "
            f"vs {starting_torque_Nm:g} Nm breakaway")
        if catalogue_service_factor:
            add("catalogue service factor fB", catalogue_service_factor >= required_service_factor,
                f"fB {catalogue_service_factor:g} vs required {required_service_factor:g}")
    if output_rpm:
        dev = (output_rpm - required_rpm) / required_rpm
        add("speed", abs(dev) <= 0.15 or (dev > 0),
            f"{output_rpm:g} rpm vs {required_rpm:g} rpm needed ({dev:+.0%}; a VFD can trim, but torque falls above "
            "base speed and cooling falls at low speed)")
    if permissible_radial_load_N and radial_load_N:
        add("radial (overhung) load", permissible_radial_load_N >= radial_load_N,
            f"permissible {permissible_radial_load_N:g} N vs {radial_load_N:g} N"
            + (" - load not at the shaft middle: apply the brand's position correction" if load_offset_mm else ""))
    if output_shaft_mm:
        bend = radial_load_N * (load_offset_mm or output_shaft_mm) / 1000  # Nm, lever from the bearing
        teq = math.sqrt(starting_torque_Nm ** 2 + bend ** 2)
        d_min = (16 * teq / (math.pi * 40e6)) ** (1 / 3) * 1000
        add("shaft stress", output_shaft_mm >= d_min,
            f"shaft {output_shaft_mm:g} mm vs about {d_min:.1f} mm minimum (torsion at start + bending from the radial "
            "load, 40 MPa allowable incl. keyway/fatigue)")
    verdict = ("NEEDS DATASHEET VALUES: " + ", ".join(missing)) if missing and not checks else \
        ("OK" if ok_all else "NOT OK - " + "; ".join(c["check"] for c in checks if not c["ok"]))
    if missing and checks:
        verdict += " (not checked: " + ", ".join(missing) + ")"
    advice = []
    if not ok_all:
        advice += ["bigger gear unit (higher rated torque / fB), not only a bigger motor",
                   "move the radial load off the gearmotor: hollow-shaft mounting on the pulley shaft with a torque arm, "
                   "or pulley shaft in its own pillow-block bearings with a flexible coupling",
                   "for wet lines: reduce bed friction (perforated/grooved slider, UHMW strips, roller bed) instead of "
                   "only adding power"]
    name = brand_model or "gearmotor"
    return {"brand_model": brand_model, "checks": checks, "verdict": verdict, "advice": advice,
            "report_to_user": f"{name} check: {verdict}"}


@tool
def pneumatic_cylinder(bore_mm: float, stroke_mm: float, pressure_bar: float = 6, rod_mm: float = 0,
                       cycles_per_min: float = 0, required_force_N: float = 0, load_factor: float = 0.7,
                       quantity: int = 1, other_air_NL_min: float = 0) -> dict:
    """Double-acting cylinder: theoretical/usable force and free-air consumption; checks a required force.

    Args:
        bore_mm: piston diameter in mm
        stroke_mm: stroke in mm
        pressure_bar: working gauge pressure in bar, default 6
        rod_mm: rod diameter in mm (0 = use 0.3 x bore)
        cycles_per_min: double strokes per minute for air consumption
        required_force_N: force the application needs (0 = no check)
        load_factor: usable share of theoretical force (dynamic ~0.5-0.7, static ~0.8), default 0.7
        quantity: number of identical cylinders (air total is for all of them), default 1
        other_air_NL_min: other air users on the same machine (blow-offs, vacuum generators, air knives) in NL/min;
            they are added into machine_total_air_NL_min
    """
    rod = rod_mm or 0.3 * bore_mm
    a_ext = math.pi * (bore_mm / 1000) ** 2 / 4
    a_ret = a_ext - math.pi * (rod / 1000) ** 2 / 4
    p = pressure_bar * 1e5
    f_ext, f_ret = p * a_ext, p * a_ret
    ratio = (pressure_bar + 1.013) / 1.013
    nl_per_cycle = (a_ext + a_ret) * stroke_mm / 1000 * ratio * 1000
    res = {"force_extend_N": round(f_ext, 1), "force_retract_N": round(f_ret, 1),
           "usable_extend_N": round(f_ext * load_factor, 1), "air_NL_per_cycle": round(nl_per_cycle, 3),
           "air_NL_per_min": round(nl_per_cycle * cycles_per_min, 2),
           "quantity": quantity, "air_NL_per_min_all_cylinders": round(nl_per_cycle * cycles_per_min * quantity, 2),
           "other_air_NL_min": other_air_NL_min,
           "machine_total_air_NL_min": round(nl_per_cycle * cycles_per_min * quantity + other_air_NL_min, 2),
           "next_step": ("machine_total_air_NL_min is the TOTAL air demand (cylinders + other users) - report it as the "
                         "total. Size a receiver for demand peaks with air_receiver; size compressors with "
                         "utilities_summary or total x (1 + margin)." if other_air_NL_min else
                         "If the machine also has blow-offs, vacuum generators or air knives, call again with "
                         "other_air_NL_min so the total includes them.")}
    if required_force_N:
        min_bore = math.sqrt(4 * required_force_N / (load_factor * p * math.pi)) * 1000
        std = [8, 10, 12, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 320]
        res.update({"ok": f_ext * load_factor >= required_force_N, "minimum_bore_mm": round(min_bore, 1),
                    "suggested_standard_bore_mm": next((b for b in std if b >= min_bore), None)})
    return res


@tool
def heat_load(mass_flow_kg_per_h: float, cp_kJ_per_kgK: float, delta_T_K: float, loss_factor: float = 1.15,
              latent_heat_kJ_per_kg: float = 2100) -> dict:
    """Heating duty Q = m x cp x dT (with losses) and the saturated steam needed to supply it.

    Args:
        mass_flow_kg_per_h: product or water flow in kg/h
        cp_kJ_per_kgK: specific heat (water ~4.19, most foods 3.0-3.9)
        delta_T_K: temperature rise in K
        loss_factor: allowance for losses, default 1.15
        latent_heat_kJ_per_kg: steam latent heat at supply pressure (~2100 at 4-6 barg), default 2100
    """
    q_kw = mass_flow_kg_per_h * cp_kJ_per_kgK * delta_T_K / 3600 * loss_factor
    return {"heat_load_kW": round(q_kw, 2), "steam_kg_per_h": round(q_kw * 3600 / latent_heat_kJ_per_kg, 1)}


@tool
def pump_power(flow_m3_per_h: float, head_m: float, density_kg_m3: float = 1000, efficiency: float = 0.6,
               service_factor: float = 1.15) -> dict:
    """Hydraulic and motor power of a pump (next IEC motor size).

    Args:
        flow_m3_per_h: flow in m3/h
        head_m: total dynamic head in m
        density_kg_m3: fluid density, default 1000
        efficiency: pump efficiency, default 0.6
        service_factor: motor margin, default 1.15
    """
    p_h = density_kg_m3 * G * flow_m3_per_h / 3600 * head_m / 1000
    p_m = p_h / efficiency * service_factor
    return {"hydraulic_kW": round(p_h, 3), "required_motor_kW": round(p_m, 3), "selected_motor_kW": next_motor(p_m)}


@tool
def utilities_summary(machines: list[dict], diversity_factor: float = 0.8, power_factor: float = 0.85,
                      air_margin: float = 1.3) -> dict:
    """Total utilities of a line: power (kW and transformer kVA), compressed air, water, steam.

    Args:
        machines: list of {"name", "qty" (opt), "power_kw", "air_NL_min" (opt), "water_L_h" (opt), "steam_kg_h" (opt)}
        diversity_factor: share of connected load running at the same time, default 0.8
        power_factor: for kVA, default 0.85
        air_margin: margin on compressed air for leaks and growth, default 1.3
    """
    tot = {"power_kw": 0.0, "air_NL_min": 0.0, "water_L_h": 0.0, "steam_kg_h": 0.0}
    for m in machines:
        q = m.get("qty", 1)
        for k in tot:
            tot[k] += float(m.get(k, 0) or 0) * q
    demand_kw = tot["power_kw"] * diversity_factor
    return {"connected_load_kW": round(tot["power_kw"], 2), "demand_load_kW": round(demand_kw, 2),
            "transformer_kVA_min": round(demand_kw / power_factor, 1),
            "compressed_air_NL_min": round(tot["air_NL_min"] * air_margin, 1),
            "compressor_m3_min": round(tot["air_NL_min"] * air_margin / 1000, 2),
            "water_m3_h": round(tot["water_L_h"] / 1000, 2), "steam_kg_h": round(tot["steam_kg_h"], 1)}


@tool
def drive_torque(power_kw: float, output_rpm: float, input_rpm: float = 1450, service_factor: float = 1.5) -> dict:
    """Output torque of a motor/gearbox drive, design torque with service factor, and gear ratio.

    Args:
        power_kw: motor power in kW
        output_rpm: required output speed in rpm
        input_rpm: motor speed in rpm (4-pole 50 Hz ~1450), default 1450
        service_factor: gearbox service factor for the duty, default 1.5
    """
    t = 9550 * power_kw / output_rpm
    return {"output_torque_Nm": round(t, 1), "design_torque_Nm": round(t * service_factor, 1),
            "gear_ratio": round(input_rpm / output_rpm, 2)}


@tool
def shaft_diameter(torque_Nm: float, bending_moment_Nm: float = 0, allowable_shear_MPa: float = 40) -> dict:
    """First estimate of a solid steel shaft diameter for combined torsion and bending (equivalent torque).

    Args:
        torque_Nm: transmitted torque in Nm
        bending_moment_Nm: maximum bending moment in Nm, default 0
        allowable_shear_MPa: allowable shear stress incl. keyway and fatigue allowance (mild steel ~40), default 40
    """
    te = math.sqrt(bending_moment_Nm ** 2 + torque_Nm ** 2)
    d = (16 * te / (math.pi * allowable_shear_MPa * 1e6)) ** (1 / 3) * 1000
    std = [10, 12, 15, 17, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 90, 100, 110, 120]
    return {"equivalent_torque_Nm": round(te, 1), "min_diameter_mm": round(d, 1),
            "suggested_diameter_mm": next((x for x in std if x >= d), math.ceil(d))}


@tool
def pipe_size(flow_m3_per_h: float, velocity_m_s: float = 1.5) -> dict:
    """Pipe inside diameter from flow and target velocity (water ~1-2 m/s, CIP supply >=1.5 m/s, suction <1 m/s).

    Args:
        flow_m3_per_h: volume flow in m3/h
        velocity_m_s: target velocity in m/s, default 1.5
    """
    d = math.sqrt(4 * flow_m3_per_h / 3600 / (math.pi * velocity_m_s)) * 1000
    dn = [15, 20, 25, 32, 40, 50, 65, 80, 100, 125, 150, 200, 250, 300, 350, 400]
    sel = next((x for x in dn if x >= d), None)
    v_sel = flow_m3_per_h / 3600 / (math.pi * (sel / 1000) ** 2 / 4) if sel else None
    return {"required_inside_diameter_mm": round(d, 1), "nominal_size_DN": sel,
            "velocity_at_DN_m_s": round(v_sel, 2) if v_sel else None,
            "note": "DN is nominal; check the real inside diameter of the pipe standard/schedule used"}


@tool
def air_receiver(deficit_NL_min: float, duration_min: float, p_start_bar: float = 7, p_min_bar: float = 6) -> dict:
    """Compressed-air receiver volume to cover a demand peak above compressor output for a time.

    Args:
        deficit_NL_min: demand above compressor capacity in normal litres per minute
        duration_min: how long the peak lasts in minutes
        p_start_bar: receiver gauge pressure at the start of the peak, default 7
        p_min_bar: lowest acceptable gauge pressure, default 6
    """
    if p_start_bar <= p_min_bar:
        raise ValueError("p_start_bar must be above p_min_bar")
    v = deficit_NL_min * duration_min * 1.013 / (p_start_bar - p_min_bar)
    std = [50, 100, 150, 200, 270, 300, 500, 750, 1000, 1500, 2000, 3000, 5000]
    return {"receiver_volume_L": round(v), "suggested_size_L": next((x for x in std if x >= v), math.ceil(v))}


@tool
def cooling_load(mass_kg_per_h: float, t_in_C: float, t_out_C: float, cp_above_kJ_kgK: float = 3.6,
                 freeze_point_C: float = -1.0, latent_kJ_kg: float = 0, cp_below_kJ_kgK: float = 1.8,
                 margin: float = 1.2) -> dict:
    """Product cooling or freezing load: sensible above freezing + latent + sensible below freezing.

    Args:
        mass_kg_per_h: product throughput in kg/h
        t_in_C: product temperature in
        t_out_C: product temperature out
        cp_above_kJ_kgK: specific heat above freezing (most foods 3.2-3.9), default 3.6
        freeze_point_C: initial freezing point, default -1
        latent_kJ_kg: latent heat of freezing (water content x 334); 0 when not freezing
        cp_below_kJ_kgK: specific heat when frozen, default 1.8
        margin: allowance for losses, door openings, fans, default 1.2
    """
    m = mass_kg_per_h / 3600
    if t_out_C >= freeze_point_C or not latent_kJ_kg:
        q = m * cp_above_kJ_kgK * (t_in_C - t_out_C)
        parts = {"sensible_kW": round(q, 2)}
    else:
        q1 = m * cp_above_kJ_kgK * (t_in_C - freeze_point_C)
        q2 = m * latent_kJ_kg
        q3 = m * cp_below_kJ_kgK * (freeze_point_C - t_out_C)
        q = q1 + q2 + q3
        parts = {"sensible_above_kW": round(q1, 2), "latent_kW": round(q2, 2), "sensible_below_kW": round(q3, 2)}
    return {**parts, "product_load_kW": round(q, 2), "design_load_kW": round(q * margin, 2),
            "design_load_TR": round(q * margin / 3.517, 2)}


@tool
def process_capability(values: list[float], lsl: float, usl: float) -> dict:
    """Cp and Cpk of a process from measurements (e.g. fill weights) and specification limits.

    Args:
        values: measured values (at least 20 recommended)
        lsl: lower specification limit
        usl: upper specification limit
    """
    import statistics
    if len(values) < 2:
        raise ValueError("need at least 2 values")
    mu, sd = statistics.mean(values), statistics.stdev(values)
    if sd == 0:
        raise ValueError("no variation in the data")
    cp = (usl - lsl) / (6 * sd)
    cpk = min(usl - mu, mu - lsl) / (3 * sd)
    return {"n": len(values), "mean": round(mu, 4), "std_dev": round(sd, 4), "Cp": round(cp, 2), "Cpk": round(cpk, 2),
            "verdict": "capable (Cpk >= 1.33)" if cpk >= 1.33 else "marginal (1.0-1.33)" if cpk >= 1 else "not capable (Cpk < 1)"}


@tool
def staffing(operators_per_shift: float, shifts: int, relief_factor: float = 0.1, absence_factor: float = 0.08) -> dict:
    """Headcount needed to run a line: operators per shift, relief for breaks, absence and holidays.

    Args:
        operators_per_shift: people needed on the line at the same time
        shifts: shifts per day
        relief_factor: extra people for breaks/relief, default 0.1
        absence_factor: allowance for leave and absence, default 0.08
    """
    per_shift = math.ceil(operators_per_shift * (1 + relief_factor))
    total = math.ceil(per_shift * shifts * (1 + absence_factor))
    return {"people_per_shift": per_shift, "total_headcount": total}


@tool
def batch_heat_up(mass_kg: float, cp_kJ_per_kgK: float, t_start_C: float, t_end_C: float, time_min: float,
                  loss_factor: float = 1.15, latent_heat_kJ_per_kg: float = 2100) -> dict:
    """Heating power and steam rate to heat a batch (retort, kettle, tank, CIP tank) within a given time.

    Args:
        mass_kg: mass heated (product + water + carriers; add the steel of the vessel for accuracy)
        cp_kJ_per_kgK: specific heat (water 4.19, foods 3.0-3.9, steel 0.5)
        t_start_C: start temperature
        t_end_C: end temperature
        time_min: heat-up time in minutes
        loss_factor: allowance for losses, default 1.15
        latent_heat_kJ_per_kg: steam latent heat at supply pressure, default 2100
    """
    energy_kj = mass_kg * cp_kJ_per_kgK * (t_end_C - t_start_C) * loss_factor
    kw = energy_kj / (time_min * 60)
    return {"energy_kWh": round(energy_kj / 3600, 2), "heating_power_kW": round(kw, 1),
            "steam_kg_per_h_during_heat_up": round(kw * 3600 / latent_heat_kJ_per_kg, 1),
            "steam_kg_per_batch": round(energy_kj / latent_heat_kJ_per_kg, 1)}
