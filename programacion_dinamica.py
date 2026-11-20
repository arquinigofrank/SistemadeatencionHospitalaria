# -*- coding: utf-8 -*-
"""
OPTIMIZACIÓN DE LA ATENCIÓN DE PACIENTES EN UN HOSPITAL
Estrategia ABC: PROGRAMACIÓN DINÁMICA (Mochila 0/1)

Idea general:
  - Cada médico es una "mochila" con capacidad de 480 minutos.
  - Cada paciente es un objeto con peso = duración y valor = puntaje de
    prioridad.
  - La tabla dp[i][t] guarda el MEJOR puntaje posible usando los primeros
    i pacientes y t minutos, sin recalcular subproblemas.

El código está dividido en 5 BLOQUES (Expositores 6 a 10, un minuto cada uno).
"""
import heapq
import random
import time

# =====================================================================
# BLOQUE 6 (Expositor 6) - MISMO ESCENARIO + COLA DE PRIORIDAD (heapq)
# Los datos son idénticos a los de divide y vencerás (misma semilla).
# =====================================================================
MEDICOS = {
    "Medicina general": ["Dr. Ramos", "Dra. Salazar"],
    "Pediatría":        ["Dra. Quispe"],
    "Traumatología":    ["Dr. Huamán"],
    "Cardiología":      ["Dra. Torres"],
}
MINUTOS_TURNO = 480
HORA_INICIO = 8 * 60
DURACIONES = [15, 20, 30, 40]
NIVELES = {1: "Emergencia", 2: "Urgente", 3: "Prioritario", 4: "Estándar"}
PUNTAJE = {1: 0, 2: 10, 3: 5, 4: 2}   # valor de cada paciente en la mochila


def generar_pacientes(cantidad, semilla=2026):
    """Mismo generador y misma semilla que la estrategia XYZ."""
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


def cola_por_especialidad(pacientes):
    """Restricción E4: cada especialidad tiene su cola de prioridad (heapq).
    Al sacar elementos, sale primero el más grave y, si empatan, el que
    llegó antes. El código del paciente evita comparar diccionarios."""
    colas = {esp: [] for esp in MEDICOS}
    for p in pacientes:
        heapq.heappush(colas[p["especialidad"]],
                       (p["prioridad"], p["llegada"], p["codigo"], p))
    # se vacía cada cola para obtener la lista ya ordenada por prioridad
    return {esp: [heapq.heappop(c)[3] for _ in range(len(c))]
            for esp, c in colas.items()}


# =====================================================================
# BLOQUE 7 (Expositor 7) - CONSTRUCCIÓN DE LA TABLA DP (Mochila 0/1)
# =====================================================================
def construir_tabla(pacientes, capacidad):
    """dp[i][t] = mejor puntaje con los primeros i pacientes y t minutos.
    Recurrencia:
        dp[i][t] = max( dp[i-1][t] ,                       -> no atenderlo
                        dp[i-1][t - d_i] + p_i )            -> atenderlo
    Complejidad: O(n x T) en tiempo y en memoria (T = minutos libres)."""
    n = len(pacientes)
    dp = [[0] * (capacidad + 1) for _ in range(n + 1)]   # fila 0 = sin pacientes
    for i in range(1, n + 1):
        d = pacientes[i - 1]["duracion"]                  # peso
        v = PUNTAJE[pacientes[i - 1]["prioridad"]]        # valor
        anterior, actual = dp[i - 1], dp[i]
        for t in range(capacidad + 1):
            actual[t] = anterior[t]                       # opción: no atenderlo
            if d <= t and anterior[t - d] + v > actual[t]:
                actual[t] = anterior[t - d] + v           # opción: atenderlo
    return dp


# =====================================================================
# BLOQUE 8 (Expositor 8) - RECONSTRUCCIÓN DE LA SOLUCIÓN ÓPTIMA
# =====================================================================
def reconstruir(dp, pacientes, capacidad):
    """Recorre la tabla desde la última celda hacia atrás: si el valor
    cambió respecto a la fila anterior, el paciente i fue elegido."""
    elegidos, t = [], capacidad
    for i in range(len(pacientes), 0, -1):
        if dp[i][t] != dp[i - 1][t]:
            elegidos.append(pacientes[i - 1])
            t -= pacientes[i - 1]["duracion"]       # se descuentan sus minutos
    elegidos.reverse()
    return elegidos


# =====================================================================
# BLOQUE 9 (Expositor 9) - ASIGNACIÓN POR MÉDICO
# E6: emergencias primero (no entran a la mochila); luego la DP usa el
# tiempo restante. Medicina general repite la DP para su segundo médico.
# =====================================================================
def programar(medico, lista, libres):
    """Coloca a los pacientes uno tras otro (E2: nunca dos a la vez)."""
    agenda, reloj = [], HORA_INICIO + MINUTOS_TURNO - libres
    for p in lista:
        agenda.append(dict(p, estado="Programado", medico=medico,
                           inicio=reloj, fin=reloj + p["duracion"]))
        reloj += p["duracion"]
    return agenda


def asignar_especialidad(ordenados, medicos):
    libres = {m: MINUTOS_TURNO for m in medicos}
    agenda = {m: [] for m in medicos}
    pendientes = []
    # 1) Reserva de emergencias: se programan antes de optimizar
    for p in [p for p in ordenados if p["prioridad"] == 1]:
        medico = max(libres, key=libres.get)
        if p["duracion"] <= libres[medico]:
            agenda[medico] += programar(medico, [p], libres[medico])
            libres[medico] -= p["duracion"]
        else:
            pendientes.append(dict(p, estado="Derivar (emergencia)"))
    # 2) Mochila 0/1 por cada médico con sus minutos restantes (E3)
    restantes = [p for p in ordenados if p["prioridad"] != 1]
    for medico in medicos:
        dp = construir_tabla(restantes, libres[medico])
        elegidos = reconstruir(dp, restantes, libres[medico])
        agenda[medico] += programar(medico, elegidos, libres[medico])
        libres[medico] -= sum(p["duracion"] for p in elegidos)
        codigos = {p["codigo"] for p in elegidos}
        restantes = [p for p in restantes if p["codigo"] not in codigos]
    # 3) Los que no entraron quedan pendientes (E5)
    pendientes += [dict(p, estado="Pendiente") for p in restantes]
    return agenda, pendientes


def resolver_programacion_dinamica(pacientes):
    colas = cola_por_especialidad(pacientes)
    agenda_total, pendientes_total = {}, []
    for especialidad, medicos in MEDICOS.items():
        agenda, pendientes = asignar_especialidad(colas[especialidad], medicos)
        agenda_total.update(agenda)
        pendientes_total.extend(pendientes)
    return {"agenda": agenda_total, "pendientes": pendientes_total}


# =====================================================================
# BLOQUE 10 (Expositor 10) - VALIDACIÓN DE RESTRICCIONES Y REPORTE
# =====================================================================
def hora(minutos):
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def validar(resultado):
    """Comprueba que la agenda respete E1, E2 y E3."""
    for especialidad, medicos in MEDICOS.items():
        for m in medicos:
            citas = sorted(resultado["agenda"][m], key=lambda p: p["inicio"])
            assert all(p["especialidad"] == especialidad for p in citas)      # E1
            assert all(a["fin"] <= b["inicio"] for a, b in zip(citas, citas[1:]))  # E2
            assert sum(p["duracion"] for p in citas) <= MINUTOS_TURNO          # E3
    return True


def resumen(resultado):
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
    print(" ESTRATEGIA ABC - PROGRAMACIÓN DINÁMICA")
    print("=" * 66)
    for medico, lista in resultado["agenda"].items():
        usados = sum(p["duracion"] for p in lista)
        print(f"{medico:<13} pacientes: {len(lista):>3} | usados: {usados:>3} min"
              f" | libres: {MINUTOS_TURNO - usados:>3} min")
        for p in lista[:3]:
            print(f"   {hora(p['inicio'])}-{hora(p['fin'])}  {p['codigo']}"
                  f"  {NIVELES[p['prioridad']]:<11} {p['duracion']} min")
    r = resumen(resultado)
    print("-" * 66)
    print(f"Atendidos: {r['atendidos']} | Pendientes: {r['pendientes']}"
          f" | Emergencias atendidas: {r['emergencias']}")
    print(f"Minutos usados: {r['minutos']}/{MINUTOS_TURNO * 5}"
          f" | Puntaje de prioridad: {r['puntaje']}")
    print(f"Restricciones E1, E2 y E3 cumplidas: {validar(resultado)}")
    print(f"Tiempo de ejecución: {ms:.3f} ms")


if __name__ == "__main__":
    pacientes = generar_pacientes(200)            # mismo caso que la estrategia XYZ
    inicio = time.perf_counter()
    resultado = resolver_programacion_dinamica(pacientes)
    ms = (time.perf_counter() - inicio) * 1000
    imprimir_reporte(resultado, ms)
