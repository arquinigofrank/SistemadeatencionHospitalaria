# -*- coding: utf-8 -*-
"""
OPTIMIZACIÓN DE LA ATENCIÓN DE PACIENTES EN UN HOSPITAL
Estrategia XYZ: DIVIDE Y VENCERÁS

Idea general:
  1) DIVIDIR  : separar recursivamente a los pacientes por especialidad.
  2) VENCER   : ordenar cada grupo por prioridad con Merge Sort (otro
                algoritmo divide y vencerás) y asignarlo a sus médicos.
  3) COMBINAR : unir las agendas de todas las especialidades en un
                solo resultado del hospital.

El código está dividido en 5 BLOQUES (Expositores 1 a 5, un minuto cada uno).
"""
import random
import time

# =====================================================================
# BLOQUE 1 (Expositor 1) - DATOS DEL ESCENARIO Y PACIENTES SIMULADOS
# Representa las restricciones A, B, C y D del informe (sección 1.2.3).
# =====================================================================

# Restricción A: médicos disponibles por especialidad (5 médicos en total)
MEDICOS = {
    "Medicina general": ["Dr. Ramos", "Dra. Salazar"],
    "Pediatría":        ["Dra. Quispe"],
    "Traumatología":    ["Dr. Huamán"],
    "Cardiología":      ["Dra. Torres"],
}
MINUTOS_TURNO = 480          # Restricción B: turno mañana 08:00-16:00
HORA_INICIO = 8 * 60         # 08:00 expresado en minutos
DURACIONES = [15, 20, 30, 40]  # Restricción C: tiempos de atención posibles

# Restricción D: nivel de prioridad registrado previamente (1 = más grave)
NIVELES = {1: "Emergencia", 2: "Urgente", 3: "Prioritario", 4: "Estándar"}
# Puntaje usado para medir la calidad de la asignación (las emergencias
# no compiten: siempre se programan primero)
PUNTAJE = {1: 0, 2: 10, 3: 5, 4: 2}


def generar_pacientes(cantidad, semilla=2026):
    """Crea pacientes simulados. La misma semilla genera SIEMPRE el mismo
    caso, por eso ambas estrategias se prueban con los mismos datos."""
    rnd = random.Random(semilla)
    especialidades = list(MEDICOS)
    pacientes = []
    for i in range(1, cantidad + 1):
        esp = rnd.choices(especialidades, weights=[40, 20, 20, 20])[0]
        prioridad = rnd.choices([1, 2, 3, 4], weights=[5, 20, 35, 40])[0]
        edad = rnd.randint(0, 17) if esp == "Pediatría" else rnd.randint(18, 90)
        pacientes.append({
            "codigo": f"P{i:04d}", "llegada": i, "edad": edad,
            "especialidad": esp, "prioridad": prioridad,
            "duracion": rnd.choice(DURACIONES), "estado": "Pendiente",
        })
    return pacientes


# =====================================================================
# BLOQUE 2 (Expositor 2) - DIVIDIR: separación recursiva por especialidad
# =====================================================================
def dividir_por_especialidad(pacientes, especialidades):
    """Parte la lista de especialidades por la mitad y reparte a los
    pacientes en cada mitad, hasta llegar a UNA sola especialidad."""
    # Caso base 1: no hay pacientes que repartir
    if not pacientes:
        return {}
    # Caso base 2: queda una sola especialidad -> ese es el grupo final
    if len(especialidades) == 1:
        return {especialidades[0]: pacientes}

    # Dividir: la lista de especialidades se parte en dos mitades
    mitad = len(especialidades) // 2
    izquierda, derecha = especialidades[:mitad], especialidades[mitad:]
    grupo_izq = [p for p in pacientes if p["especialidad"] in izquierda]
    grupo_der = [p for p in pacientes if p["especialidad"] in derecha]

    # Llamadas recursivas sobre cada mitad y combinación de los resultados
    resultado = dividir_por_especialidad(grupo_izq, izquierda)
    resultado.update(dividir_por_especialidad(grupo_der, derecha))
    return resultado


# =====================================================================
# BLOQUE 3 (Expositor 3) - VENCER: Merge Sort por prioridad
# =====================================================================
def clave_orden(p):
    """Primero la prioridad (1 = emergencia), luego la atención más corta
    y, si empatan, el que llegó antes."""
    return (p["prioridad"], p["duracion"], p["llegada"])


def merge_sort(lista):
    """Ordena dividiendo la lista en dos mitades, ordenando cada mitad
    recursivamente y mezclándolas. Complejidad O(n log n)."""
    if len(lista) <= 1:                 # caso base: ya está ordenada
        return lista
    mitad = len(lista) // 2
    izquierda = merge_sort(lista[:mitad])   # dividir y resolver izquierda
    derecha = merge_sort(lista[mitad:])     # dividir y resolver derecha
    return mezclar(izquierda, derecha)      # combinar


def mezclar(izq, der):
    """Une dos listas ya ordenadas en una sola lista ordenada."""
    resultado, i, j = [], 0, 0
    while i < len(izq) and j < len(der):
        if clave_orden(izq[i]) <= clave_orden(der[j]):
            resultado.append(izq[i]); i += 1
        else:
            resultado.append(der[j]); j += 1
    resultado.extend(izq[i:])           # lo que sobra ya está ordenado
    resultado.extend(der[j:])
    return resultado


# =====================================================================
# BLOQUE 4 (Expositor 4) - ASIGNACIÓN A MÉDICOS Y COMBINACIÓN
# Restricciones E1, E2, E3, E5 y E6.
# =====================================================================
def asignar_grupo(ordenados, medicos):
    """Recorre los pacientes ya ordenados y los programa uno detrás de otro
    (nunca dos a la vez) mientras quepan en los 480 minutos del médico."""
    libres = {m: MINUTOS_TURNO for m in medicos}
    agenda = {m: [] for m in medicos}
    pendientes = []
    for p in ordenados:
        medico = max(libres, key=libres.get)   # médico con más tiempo libre
        if p["duracion"] <= libres[medico]:
            inicio = HORA_INICIO + MINUTOS_TURNO - libres[medico]
            agenda[medico].append(dict(p, estado="Programado", medico=medico,
                                       inicio=inicio, fin=inicio + p["duracion"]))
            libres[medico] -= p["duracion"]
        else:
            # No cabe en el turno: queda pendiente (E5). Si es emergencia
            # se marca para derivarla de inmediato al siguiente turno (E6).
            estado = "Derivar (emergencia)" if p["prioridad"] == 1 else "Pendiente"
            pendientes.append(dict(p, estado=estado))
    return agenda, pendientes


def resolver_divide_y_venceras(pacientes):
    """Algoritmo completo: DIVIDIR -> VENCER -> COMBINAR."""
    grupos = dividir_por_especialidad(pacientes, list(MEDICOS))     # dividir
    agenda_total, pendientes_total = {}, []
    for especialidad, medicos in MEDICOS.items():
        ordenados = merge_sort(grupos.get(especialidad, []))        # vencer
        agenda, pendientes = asignar_grupo(ordenados, medicos)
        agenda_total.update(agenda)                                 # combinar
        pendientes_total.extend(pendientes)
    return {"agenda": agenda_total, "pendientes": pendientes_total}


# =====================================================================
# BLOQUE 5 (Expositor 5) - REPORTE Y MEDICIÓN DEL TIEMPO
# =====================================================================
def hora(minutos):
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def resumen(resultado):
    """Calcula los indicadores que se comparan en el análisis empírico."""
    atendidos = [p for lista in resultado["agenda"].values() for p in lista]
    return {
        "atendidos": len(atendidos),
        "pendientes": len(resultado["pendientes"]),
        "emergencias": sum(p["prioridad"] == 1 for p in atendidos),
        "urgentes": sum(p["prioridad"] == 2 for p in atendidos),
        "minutos": sum(p["duracion"] for p in atendidos),
        "puntaje": sum(PUNTAJE[p["prioridad"]] for p in atendidos),
    }


def imprimir_reporte(resultado, ms):
    print("=" * 66)
    print(" ESTRATEGIA XYZ - DIVIDE Y VENCERÁS")
    print("=" * 66)
    for medico, lista in resultado["agenda"].items():
        usados = sum(p["duracion"] for p in lista)
        print(f"{medico:<13} pacientes: {len(lista):>3} | usados: {usados:>3} min"
              f" | libres: {MINUTOS_TURNO - usados:>3} min")
        for p in lista[:3]:   # primeras citas de la agenda
            print(f"   {hora(p['inicio'])}-{hora(p['fin'])}  {p['codigo']}"
                  f"  {NIVELES[p['prioridad']]:<11} {p['duracion']} min")
    r = resumen(resultado)
    print("-" * 66)
    print(f"Atendidos: {r['atendidos']} | Pendientes: {r['pendientes']}"
          f" | Emergencias atendidas: {r['emergencias']}")
    print(f"Minutos usados: {r['minutos']}/{MINUTOS_TURNO * 5}"
          f" | Puntaje de prioridad: {r['puntaje']}")
    print(f"Tiempo de ejecución: {ms:.3f} ms")


if __name__ == "__main__":
    pacientes = generar_pacientes(200)            # mismo caso para ambas estrategias
    inicio = time.perf_counter()
    resultado = resolver_divide_y_venceras(pacientes)
    ms = (time.perf_counter() - inicio) * 1000
    imprimir_reporte(resultado, ms)
