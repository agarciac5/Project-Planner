import random
from collections import defaultdict


# -------------------------
# 🧬 INDIVIDUO
# -------------------------
class Individual:
    def __init__(self, genes):
        self.genes = genes
        self.fitness = 0


# -------------------------
# 🎲 CREACIÓN INICIAL
# -------------------------
def create_individual(groups, classrooms, timeslots):
    genes = []

    for group in groups:
        ts = random.choice(timeslots)

        classroom = None
        if not getattr(group, "is_virtual", False) and classrooms:
            classroom = random.choice(classrooms)

        genes.append({
            "group": group,
            "teacher": group.teacher,
            "classroom": classroom,
            "timeslot": ts,
        })

    return Individual(genes)


# -------------------------
# 🔍 VALIDACIÓN DISPONIBILIDAD
# -------------------------
def violates_availability(gene, availability_list):
    ts = gene["timeslot"]

    for av in availability_list:
        if ts.day != av.day:
            continue

        if ts.start_time >= av.start_time and ts.end_time <= av.end_time:
            return False  # válido

    return True  # ❌ fuera de disponibilidad


# -------------------------
# 🎯 FITNESS
# -------------------------
def calculate_fitness(
    individual,
    teacher_activities,
    teacher_availability,
):
    penalty = 0
    genes = individual.genes

    # -------------------------
    # choques básicos
    # -------------------------
    for i in range(len(genes)):
        for j in range(i + 1, len(genes)):
            g1 = genes[i]
            g2 = genes[j]

            if g1["timeslot"] != g2["timeslot"]:
                continue

            # aula duplicada
            if g1["classroom"] and g1["classroom"] == g2["classroom"]:
                penalty += 10

            # profesor ocupado
            if g1["teacher"] and g1["teacher"] == g2["teacher"]:
                penalty += 10

            # mismo grupo
            if g1["group"] == g2["group"]:
                penalty += 50

    # -------------------------
    # restricciones por gen
    # -------------------------
    teacher_hours = defaultdict(int)

    for gene in genes:
        teacher = gene["teacher"]
        ts = gene["timeslot"]
        group = gene["group"]

        # contar horas
        if teacher:
            teacher_hours[teacher.id] += 1

        # -------------------------
        # disponibilidad
        # -------------------------
        if teacher:
            avail = teacher_availability.get(teacher.id, [])
            if violates_availability(gene, avail):
                penalty += 50

        # -------------------------
        # actividades del profesor
        # -------------------------
        if teacher:
            activities = teacher_activities.get(teacher.id, [])

            for act in activities:
                if ts.day != act.day:
                    continue

                overlap = not (
                    ts.end_time <= act.start_time or
                    ts.start_time >= act.end_time
                )

                if overlap:
                    penalty += 30

        # -------------------------
        # profesor calificado
        # -------------------------
        if teacher:
            if group.course not in teacher.qualified_courses.all():
                penalty += 50

        # -------------------------
        # capacidad aula
        # -------------------------
        if gene["classroom"]:
            if gene["classroom"].capacity < group.capacity:
                penalty += 20

    # -------------------------
    # contrato (horas)
    # -------------------------
    for gene in genes:
        teacher = gene["teacher"]

        if not teacher or not teacher.contract:
            continue

        hours = teacher_hours[teacher.id]
        contract = teacher.contract

        if hours > contract.max_teaching_hours:
            penalty += 30

    individual.fitness = 1 / (1 + penalty + random.random() * 0.01)
    return individual.fitness


# -------------------------
# 🧬 SELECCIÓN
# -------------------------
def selection(population):
    return sorted(population, key=lambda x: x.fitness, reverse=True)[:10]


# -------------------------
# 🔀 CRUCE
# -------------------------
def crossover(p1, p2):
    point = random.randint(0, len(p1.genes) - 1)
    child_genes = p1.genes[:point] + p2.genes[point:]
    return Individual(child_genes)


# -------------------------
# 🔄 MUTACIÓN
# -------------------------
def mutate(individual, classrooms, timeslots):
    gene = random.choice(individual.genes)

    gene["timeslot"] = random.choice(timeslots)

    if gene["classroom"]:
        gene["classroom"] = random.choice(classrooms)


# -------------------------
# 🚀 ALGORITMO PRINCIPAL
# -------------------------
def run_genetic_algorithm(
    groups,
    classrooms,
    timeslots,
    teacher_activities,
    teacher_availability,
    population_size=50,
    generations=80
):
    population = [
        create_individual(groups, classrooms, timeslots)
        for _ in range(population_size)
    ]

    for _ in range(generations):

        # evaluar fitness
        for ind in population:
            calculate_fitness(ind, teacher_activities, teacher_availability)

        # ordenar
        population.sort(key=lambda x: x.fitness, reverse=True)

        # elitismo
        new_population = population[:10]

        # reproducción
        while len(new_population) < population_size:
            p1, p2 = random.sample(population[:20], 2)
            child = crossover(p1, p2)
            mutate(child, classrooms, timeslots)
            new_population.append(child)

        population = new_population

    return population[:5]  # top 5 horarios