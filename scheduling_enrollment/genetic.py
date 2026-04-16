"""
Algoritmo genético para generar horarios de profesores.
Retorna top-3 cromosomas y desglose de penalizaciones.
"""

import random
from datetime import datetime, timedelta, time
from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Estructuras de datos
# ---------------------------------------------------------------------------

@dataclass
class GroupInfo:
    group_id: int
    course_code: str
    course_name: str
    credits: int
    required_classroom_type: str
    is_virtual: bool = False

    @property
    def duration_minutes(self) -> int:
        return self.credits * 45


@dataclass
class AvailabilitySlot:
    day: str
    start: time
    end: time

    def contains(self, start: time, end: time) -> bool:
        return self.start <= start and end <= self.end


@dataclass
class ClassroomInfo:
    classroom_id: int
    code: str
    capacity: int
    classroom_type: str
    is_virtual: bool = False


@dataclass
class OccupiedSlot:
    classroom_id: int
    day: str
    start: time
    end: time


@dataclass
class ActivitySlot:
    """Actividad extra del profesor (asesoría / investigación)."""
    activity_type: str
    day: str
    start: time
    end: time

    def duration_hours(self) -> float:
        s = datetime.combine(datetime.today(), self.start)
        e = datetime.combine(datetime.today(), self.end)
        return (e - s).total_seconds() / 3600


@dataclass
class Gene:
    group_id: int
    day: str
    start_time: time
    end_time: time
    classroom_id: Optional[int]

    def overlaps(self, other: "Gene") -> bool:
        if self.day != other.day:
            return False
        return self.start_time < other.end_time and other.start_time < self.end_time

    def overlaps_activity(self, act: ActivitySlot) -> bool:
        if self.day != act.day:
            return False
        return self.start_time < act.end and act.start < self.end_time

    def duration_minutes(self) -> int:
        s = datetime.combine(datetime.today(), self.start_time)
        e = datetime.combine(datetime.today(), self.end_time)
        return int((e - s).total_seconds() / 60)


# ---------------------------------------------------------------------------
# Penalizaciones
# ---------------------------------------------------------------------------

HARD_PENALTY            = 1000
SOFT_DEAD_TIME_PER_HOUR = 5
SOFT_SINGLE_CLASS_DAY   = 20
SOFT_UNDER_MIN_HOURS    = 30
SOFT_ACTIVITY_OVERLAP   = 50


@dataclass
class FitnessBreakdown:
    teacher_overlaps: int       = 0
    classroom_conflicts: int    = 0
    availability_violations: int = 0
    over_max_hours: float       = 0.0
    under_min_hours: float      = 0.0
    dead_time_hours: float      = 0.0
    single_class_days: int      = 0
    activity_overlaps: int      = 0
    total_score: float          = 0.0
    total_teaching_hours: float = 0.0

    def penalty_detail(self) -> list[dict]:
        details = []
        if self.teacher_overlaps:
            details.append({
                "tipo": "error",
                "descripcion": f"{self.teacher_overlaps} solapamiento(s) de clases del profesor",
                "impacto": -self.teacher_overlaps * HARD_PENALTY,
            })
        if self.classroom_conflicts:
            details.append({
                "tipo": "error",
                "descripcion": f"{self.classroom_conflicts} conflicto(s) de aula ocupada",
                "impacto": -self.classroom_conflicts * HARD_PENALTY,
            })
        if self.availability_violations:
            details.append({
                "tipo": "error",
                "descripcion": f"{self.availability_violations} clase(s) fuera de disponibilidad del profesor",
                "impacto": -self.availability_violations * HARD_PENALTY,
            })
        if self.over_max_hours > 0:
            details.append({
                "tipo": "error",
                "descripcion": f"Excede el máximo de horas en {self.over_max_hours:.1f}h",
                "impacto": -HARD_PENALTY * self.over_max_hours,
            })
        if self.activity_overlaps:
            details.append({
                "tipo": "advertencia",
                "descripcion": f"{self.activity_overlaps} clase(s) solapan con asesorías/investigación",
                "impacto": -self.activity_overlaps * SOFT_ACTIVITY_OVERLAP,
            })
        if self.under_min_hours > 0:
            details.append({
                "tipo": "advertencia",
                "descripcion": f"Faltan {self.under_min_hours:.1f}h para el mínimo del contrato",
                "impacto": -SOFT_UNDER_MIN_HOURS * self.under_min_hours,
            })
        if self.single_class_days:
            details.append({
                "tipo": "info",
                "descripcion": f"{self.single_class_days} día(s) con una sola clase (ineficiente)",
                "impacto": -self.single_class_days * SOFT_SINGLE_CLASS_DAY,
            })
        if self.dead_time_hours > 0:
            details.append({
                "tipo": "info",
                "descripcion": f"{self.dead_time_hours:.1f}h de ventana muerta entre clases",
                "impacto": -SOFT_DEAD_TIME_PER_HOUR * self.dead_time_hours,
            })
        if not details:
            details.append({
                "tipo": "ok",
                "descripcion": "Sin penalizaciones — horario óptimo",
                "impacto": 0,
            })
        return details


# ---------------------------------------------------------------------------
# Fitness con desglose
# ---------------------------------------------------------------------------

def evaluate_fitness_detailed(
    chromosome: list[Gene],
    groups: dict[int, GroupInfo],
    availability: list[AvailabilitySlot],
    occupied_slots: list[OccupiedSlot],
    activities: list[ActivitySlot],
    max_teaching_hours: int,
    min_teaching_hours: int,
) -> tuple[float, FitnessBreakdown]:

    bd    = FitnessBreakdown()
    score = 0.0

    for i in range(len(chromosome)):
        for j in range(i + 1, len(chromosome)):
            if chromosome[i].overlaps(chromosome[j]):
                bd.teacher_overlaps += 1
                score -= HARD_PENALTY

    for gene in chromosome:
        if gene.classroom_id is None:
            continue
        for occ in occupied_slots:
            if occ.classroom_id != gene.classroom_id or occ.day != gene.day:
                continue
            if gene.start_time < occ.end and occ.start < gene.end_time:
                bd.classroom_conflicts += 1
                score -= HARD_PENALTY

    for gene in chromosome:
        if not any(s.day == gene.day and s.contains(gene.start_time, gene.end_time)
                   for s in availability):
            bd.availability_violations += 1
            score -= HARD_PENALTY

    total_hours = sum(g.duration_minutes() for g in chromosome) / 60
    bd.total_teaching_hours = round(total_hours, 2)
    if total_hours > max_teaching_hours:
        excess = total_hours - max_teaching_hours
        bd.over_max_hours = round(excess, 2)
        score -= HARD_PENALTY * excess

    for gene in chromosome:
        for act in activities:
            if gene.overlaps_activity(act):
                bd.activity_overlaps += 1
                score -= SOFT_ACTIVITY_OVERLAP

    if total_hours < min_teaching_hours:
        deficit = min_teaching_hours - total_hours
        bd.under_min_hours = round(deficit, 2)
        score -= SOFT_UNDER_MIN_HOURS * deficit

    days_used: dict[str, list[Gene]] = {}
    for gene in chromosome:
        days_used.setdefault(gene.day, []).append(gene)

    for day_genes in days_used.values():
        day_genes_sorted = sorted(day_genes, key=lambda g: g.start_time)
        if len(day_genes_sorted) == 1:
            bd.single_class_days += 1
            score -= SOFT_SINGLE_CLASS_DAY
        for k in range(len(day_genes_sorted) - 1):
            end_prev   = datetime.combine(datetime.today(), day_genes_sorted[k].end_time)
            start_next = datetime.combine(datetime.today(), day_genes_sorted[k + 1].start_time)
            gap = (start_next - end_prev).total_seconds() / 3600
            if gap > 1:
                bd.dead_time_hours += gap
                score -= SOFT_DEAD_TIME_PER_HOUR * gap

    bd.dead_time_hours = round(bd.dead_time_hours, 2)
    bd.total_score     = round(score, 2)
    return score, bd


def evaluate_fitness(chromosome, groups, availability, occupied_slots,
                     activities, max_teaching_hours, min_teaching_hours):
    s, _ = evaluate_fitness_detailed(chromosome, groups, availability,
                                     occupied_slots, activities,
                                     max_teaching_hours, min_teaching_hours)
    return s


# ---------------------------------------------------------------------------
# Generación de población
# ---------------------------------------------------------------------------

VALID_START_TIMES = [
    time(6, 0),  time(6, 45),  time(7, 30),  time(8, 15),  time(9, 0),
    time(9, 45), time(10, 30), time(11, 15),
    time(18, 0), time(18, 45), time(19, 30), time(20, 15), time(21, 0),
]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


def _compute_end_time(start: time, duration_minutes: int) -> time:
    dt = datetime.combine(datetime.today(), start)
    dt += timedelta(minutes=duration_minutes)
    return dt.time()


def _random_gene(group: GroupInfo, availability: list[AvailabilitySlot],
                 classrooms: list[ClassroomInfo]) -> Gene:
    compatible = ([None] if group.is_virtual else
                  [c for c in classrooms if c.classroom_type == group.required_classroom_type]
                  or classrooms)

    for _ in range(100):
        if not availability:
            day, start = random.choice(DAYS), random.choice(VALID_START_TIMES)
        else:
            slot  = random.choice(availability)
            day   = slot.day
            valid = [t for t in VALID_START_TIMES if slot.start <= t]
            if not valid:
                continue
            start = random.choice(valid)

        end = _compute_end_time(start, group.duration_minutes)
        if end > time(22, 45):
            continue

        classroom    = random.choice(compatible)
        classroom_id = classroom.classroom_id if classroom else None
        return Gene(group_id=group.group_id, day=day, start_time=start,
                    end_time=end, classroom_id=classroom_id)

    end = _compute_end_time(time(8, 0), group.duration_minutes)
    return Gene(group_id=group.group_id, day="Monday", start_time=time(8, 0),
                end_time=end, classroom_id=None)


def generate_population(groups, availability, classrooms, population_size=50):
    return [[_random_gene(g, availability, classrooms) for g in groups]
            for _ in range(population_size)]


# ---------------------------------------------------------------------------
# Operadores genéticos
# ---------------------------------------------------------------------------

def tournament_selection(population, fitness_scores, k=3):
    candidates = random.sample(range(len(population)), min(k, len(population)))
    best = max(candidates, key=lambda i: fitness_scores[i])
    return [Gene(**vars(g)) for g in population[best]]


def crossover(p1, p2):
    if len(p1) <= 1:
        return p1[:], p2[:]
    pt = random.randint(1, len(p1) - 1)
    return p1[:pt] + p2[pt:], p2[:pt] + p1[pt:]


def mutate(chromosome, groups, availability, classrooms, rate=0.1):
    gmap = {g.group_id: g for g in groups}
    return [
        _random_gene(gmap[gene.group_id], availability, classrooms)
        if random.random() < rate and gene.group_id in gmap else gene
        for gene in chromosome
    ]


# ---------------------------------------------------------------------------
# Algoritmo principal — retorna top 3
# ---------------------------------------------------------------------------

def run_genetic_algorithm(
    groups: list[GroupInfo],
    availability: list[AvailabilitySlot],
    classrooms: list[ClassroomInfo],
    occupied_slots: list[OccupiedSlot],
    activities: list[ActivitySlot],
    max_teaching_hours: int,
    min_teaching_hours: int,
    population_size: int = 60,
    generations: int = 120,
    mutation_rate: float = 0.12,
    crossover_rate: float = 0.8,
    elitism: int = 3,
) -> list[tuple[list[Gene], float, FitnessBreakdown]]:
    """Retorna lista de hasta 3 tuplas (cromosoma, fitness, breakdown)."""
    if not groups:
        return []

    gmap       = {g.group_id: g for g in groups}
    population = generate_population(groups, availability, classrooms, population_size)
    archive: dict[str, tuple] = {}

    def _key(ch):
        return str([(g.group_id, g.day, str(g.start_time)) for g in ch])

    for _ in range(generations):
        scores = [
            evaluate_fitness(c, gmap, availability, occupied_slots,
                             activities, max_teaching_hours, min_teaching_hours)
            for c in population
        ]

        sorted_idx = sorted(range(len(population)), key=lambda i: scores[i], reverse=True)

        for idx in sorted_idx[:10]:
            k = _key(population[idx])
            if k not in archive:
                _, bd = evaluate_fitness_detailed(
                    population[idx], gmap, availability, occupied_slots,
                    activities, max_teaching_hours, min_teaching_hours
                )
                archive[k] = ([Gene(**vars(g)) for g in population[idx]], scores[idx], bd)

        # Podar archivo a los 20 mejores
        if len(archive) > 20:
            archive = dict(
                sorted(archive.items(), key=lambda x: x[1][1], reverse=True)[:20]
            )

        new_pop = [[Gene(**vars(g)) for g in population[i]] for i in sorted_idx[:elitism]]
        while len(new_pop) < population_size:
            p1 = tournament_selection(population, scores)
            p2 = tournament_selection(population, scores)
            c1, c2 = crossover(p1, p2) if random.random() < crossover_rate else (p1[:], p2[:])
            new_pop.append(mutate(c1, groups, availability, classrooms, mutation_rate))
            if len(new_pop) < population_size:
                new_pop.append(mutate(c2, groups, availability, classrooms, mutation_rate))
        population = new_pop

    return sorted(archive.values(), key=lambda x: x[1], reverse=True)[:3]