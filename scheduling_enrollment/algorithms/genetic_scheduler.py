import math
import random
from dataclasses import dataclass
from datetime import datetime, time


@dataclass(frozen=True)
class TimeSlotResource:
    index: int
    day: str
    start_time: time
    end_time: time

    @property
    def duration_hours(self) -> float:
        start = datetime.combine(datetime.today(), self.start_time)
        end = datetime.combine(datetime.today(), self.end_time)
        return (end - start).total_seconds() / 3600


@dataclass(frozen=True)
class DemandCourse:
    course_id: int
    code: str
    name: str
    demand: int
    min_sections: int
    max_sections: int


@dataclass(frozen=True)
class TeacherResource:
    teacher_id: int
    label: str
    qualified_course_ids: frozenset[int]
    availability: tuple[tuple[str, time, time], ...]
    activities: tuple[tuple[str, time, time], ...]
    max_teaching_hours: float
    min_teaching_hours: float
    campus_id: int | None = None


@dataclass(frozen=True)
class ClassroomResource:
    classroom_id: int
    label: str
    capacity: int
    classroom_type: str
    campus_id: int | None = None


@dataclass(frozen=True)
class PotentialSection:
    index: int
    course_id: int
    course_code: str
    course_name: str
    section_number: int


@dataclass
class SectionGene:
    open_section: bool
    teacher_id: int | None
    classroom_id: int | None
    timeslot_index: int | None


@dataclass
class AssignmentResult:
    course_id: int
    course_code: str
    course_name: str
    section_number: int
    teacher_id: int
    classroom_id: int
    timeslot_index: int
    students_assigned: int
    capacity: int


@dataclass
class FitnessResult:
    score: float
    summary: dict
    assignments: list[AssignmentResult]


def _overlaps(start_a, end_a, start_b, end_b) -> bool:
    return start_a < end_b and start_b < end_a


def _slot_within_availability(slot: TimeSlotResource, teacher: TeacherResource) -> bool:
    return any(
        day == slot.day and start <= slot.start_time and slot.end_time <= end
        for day, start, end in teacher.availability
    )


def _slot_overlaps_activity(slot: TimeSlotResource, teacher: TeacherResource) -> bool:
    return any(
        day == slot.day and _overlaps(slot.start_time, slot.end_time, start, end)
        for day, start, end in teacher.activities
    )


def _build_feasible_candidates(
    demand_courses: dict[int, DemandCourse],
    teachers: dict[int, TeacherResource],
    classrooms: dict[int, ClassroomResource],
    timeslots: dict[int, TimeSlotResource],
) -> dict[int, list[tuple[int, int, int]]]:
    candidates: dict[int, list[tuple[int, int, int]]] = {}
    classroom_ids = list(classrooms.keys())
    for course_id in demand_courses:
        course_candidates = []
        for teacher in teachers.values():
            if course_id not in teacher.qualified_course_ids:
                continue
            for slot in timeslots.values():
                if not _slot_within_availability(slot, teacher):
                    continue
                if _slot_overlaps_activity(slot, teacher):
                    continue
                for classroom_id in classroom_ids:
                    course_candidates.append((teacher.teacher_id, classroom_id, slot.index))
        candidates[course_id] = course_candidates
    return candidates


def _normalize_assignments(
    chromosome: list[SectionGene],
    potential_sections: list[PotentialSection],
    demand_courses: dict[int, DemandCourse],
) -> tuple[list[AssignmentResult], dict[int, list[int]]]:
    open_indexes_by_course: dict[int, list[int]] = {}
    for idx, gene in enumerate(chromosome):
        if not gene.open_section:
            continue
        section = potential_sections[idx]
        open_indexes_by_course.setdefault(section.course_id, []).append(idx)

    assignments: list[AssignmentResult] = []
    for course_id, indexes in open_indexes_by_course.items():
        demand = demand_courses[course_id].demand
        remaining = demand
        open_count = len(indexes)
        for position, idx in enumerate(indexes):
            gene = chromosome[idx]
            section = potential_sections[idx]
            sections_left = open_count - position
            students_assigned = min(20, math.ceil(remaining / sections_left)) if sections_left else 0
            remaining -= students_assigned
            assignments.append(
                AssignmentResult(
                    course_id=section.course_id,
                    course_code=section.course_code,
                    course_name=section.course_name,
                    section_number=section.section_number,
                    teacher_id=gene.teacher_id or 0,
                    classroom_id=gene.classroom_id or 0,
                    timeslot_index=gene.timeslot_index or 0,
                    students_assigned=max(students_assigned, 0),
                    capacity=20,
                )
            )
    return assignments, open_indexes_by_course


def evaluate_semester_schedule(
    chromosome: list[SectionGene],
    potential_sections: list[PotentialSection],
    demand_courses: dict[int, DemandCourse],
    teachers: dict[int, TeacherResource],
    classrooms: dict[int, ClassroomResource],
    timeslots: dict[int, TimeSlotResource],
) -> FitnessResult:
    score = 100.0
    summary = {
        "hard_conflicts": 0,
        "availability_violations": 0,
        "activity_conflicts": 0,
        "qualification_violations": 0,
        "capacity_violations": 0,
        "contract_overload": 0,
        "under_min_hours_teachers": 0,
        "sections_below_minimum": 0,
        "uncovered_students": 0,
        "teachers_used": 0,
        "load_balance_penalty": 0.0,
        "penalties": {},
    }
    penalties = {
        "uncovered_demand": 0.0,
        "extra_sections": 0.0,
        "missing_resources": 0.0,
        "qualification": 0.0,
        "capacity": 0.0,
        "teacher_conflicts": 0.0,
        "classroom_conflicts": 0.0,
        "availability": 0.0,
        "activities": 0.0,
        "below_min_section_size": 0.0,
        "load_balance": 0.0,
        "contract_overload": 0.0,
        "under_min_hours": 0.0,
    }

    assignments, open_indexes_by_course = _normalize_assignments(
        chromosome, potential_sections, demand_courses
    )

    teacher_slots: dict[int, set[int]] = {}
    classroom_slots: dict[int, set[int]] = {}
    teacher_hours: dict[int, float] = {}

    for course_id, course in demand_courses.items():
        open_count = len(open_indexes_by_course.get(course_id, []))
        if course.demand >= 5 and open_count == 0:
            summary["uncovered_students"] += course.demand
            penalties["uncovered_demand"] += 25
            score -= 25
        if open_count < course.min_sections:
            uncovered_capacity = (course.min_sections - open_count) * 20
            uncovered = min(course.demand, uncovered_capacity)
            penalty = 15 + uncovered * 0.8
            summary["uncovered_students"] += uncovered
            penalties["uncovered_demand"] += penalty
            score -= penalty
        if open_count > course.max_sections:
            summary["hard_conflicts"] += open_count - course.max_sections
            penalty = 12 * (open_count - course.max_sections)
            penalties["extra_sections"] += penalty
            score -= penalty

    for assignment in assignments:
        teacher = teachers.get(assignment.teacher_id)
        classroom = classrooms.get(assignment.classroom_id)
        slot = timeslots.get(assignment.timeslot_index)

        if not teacher or not classroom or not slot:
            summary["hard_conflicts"] += 1
            penalties["missing_resources"] += 20
            score -= 20
            continue

        if assignment.course_id not in teacher.qualified_course_ids:
            summary["qualification_violations"] += 1
            penalties["qualification"] += 12
            score -= 12

        if classroom.capacity < assignment.students_assigned:
            summary["capacity_violations"] += 1
            penalties["capacity"] += 10
            score -= 10

        teacher_slots.setdefault(teacher.teacher_id, set())
        classroom_slots.setdefault(classroom.classroom_id, set())
        if assignment.timeslot_index in teacher_slots[teacher.teacher_id]:
            summary["hard_conflicts"] += 1
            penalties["teacher_conflicts"] += 18
            score -= 18
        else:
            teacher_slots[teacher.teacher_id].add(assignment.timeslot_index)

        if assignment.timeslot_index in classroom_slots[classroom.classroom_id]:
            summary["hard_conflicts"] += 1
            penalties["classroom_conflicts"] += 18
            score -= 18
        else:
            classroom_slots[classroom.classroom_id].add(assignment.timeslot_index)

        if not _slot_within_availability(slot, teacher):
            summary["availability_violations"] += 1
            penalties["availability"] += 12
            score -= 12

        if _slot_overlaps_activity(slot, teacher):
            summary["activity_conflicts"] += 1
            penalties["activities"] += 8
            score -= 8

        if assignment.students_assigned < 5:
            summary["sections_below_minimum"] += 1
            penalties["below_min_section_size"] += 4
            score -= 4

        teacher_hours[teacher.teacher_id] = teacher_hours.get(teacher.teacher_id, 0.0) + slot.duration_hours

    loads = list(teacher_hours.values())
    summary["teachers_used"] = len(loads)
    if loads:
        avg_load = sum(loads) / len(loads)
        load_balance_penalty = sum(abs(load - avg_load) for load in loads) / max(len(loads), 1)
        summary["load_balance_penalty"] = round(load_balance_penalty, 2)
        penalty = min(15, load_balance_penalty * 3)
        penalties["load_balance"] += penalty
        score -= penalty

    for teacher_id, hours in teacher_hours.items():
        teacher = teachers[teacher_id]
        if hours > teacher.max_teaching_hours:
            summary["contract_overload"] += 1
            penalty = 12 + (hours - teacher.max_teaching_hours) * 2
            penalties["contract_overload"] += penalty
            score -= penalty
        elif teacher.min_teaching_hours and hours < teacher.min_teaching_hours:
            summary["under_min_hours_teachers"] += 1
            penalty = min(4, (teacher.min_teaching_hours - hours))
            penalties["under_min_hours"] += penalty
            score -= penalty

    covered = sum(a.students_assigned for a in assignments)
    total_demand = sum(course.demand for course in demand_courses.values())
    summary["demand_covered"] = covered
    summary["demand_total"] = total_demand
    summary["sections_opened"] = len(assignments)
    summary["penalties"] = {key: round(value, 2) for key, value in penalties.items()}
    summary["total_penalty"] = round(sum(penalties.values()), 2)
    score = max(0.0, min(100.0, round(score, 2)))
    return FitnessResult(score=score, summary=summary, assignments=assignments)


def _random_gene(
    section: PotentialSection,
    demand_courses: dict[int, DemandCourse],
    feasible_candidates: dict[int, list[tuple[int, int, int]]],
    force_open: bool = False,
) -> SectionGene:
    course = demand_courses[section.course_id]
    if force_open or section.section_number <= course.min_sections:
        open_probability = 0.9
    else:
        open_probability = 0.18

    should_open = random.random() < open_probability
    if not should_open:
        return SectionGene(open_section=False, teacher_id=None, classroom_id=None, timeslot_index=None)

    candidates = feasible_candidates.get(section.course_id, [])
    if not candidates:
        return SectionGene(open_section=False, teacher_id=None, classroom_id=None, timeslot_index=None)
    teacher_id, classroom_id, timeslot_index = random.choice(candidates)
    return SectionGene(
        open_section=True,
        teacher_id=teacher_id,
        classroom_id=classroom_id,
        timeslot_index=timeslot_index,
    )


def _clone_gene(gene: SectionGene) -> SectionGene:
    return SectionGene(
        open_section=gene.open_section,
        teacher_id=gene.teacher_id,
        classroom_id=gene.classroom_id,
        timeslot_index=gene.timeslot_index,
    )


def _result_signature(result: FitnessResult) -> tuple:
    return tuple(
        sorted(
            (
                assignment.course_id,
                assignment.section_number,
                assignment.teacher_id,
                assignment.classroom_id,
                assignment.timeslot_index,
                assignment.students_assigned,
            )
            for assignment in result.assignments
        )
    )


def _result_distance(result_a: FitnessResult, result_b: FitnessResult) -> float:
    signature_a = set(_result_signature(result_a))
    signature_b = set(_result_signature(result_b))
    if not signature_a and not signature_b:
        return 0.0
    intersection = len(signature_a & signature_b)
    union = len(signature_a | signature_b)
    return 1 - (intersection / union if union else 1.0)


def _select_diverse_results(
    ordered_results: list[FitnessResult],
    options_limit: int,
    min_distance: float = 0.15,
) -> list[FitnessResult]:
    selected: list[FitnessResult] = []
    seen_signatures: set[tuple] = set()

    for result in ordered_results:
        signature = _result_signature(result)
        if signature in seen_signatures:
            continue
        if all(_result_distance(result, chosen) >= min_distance for chosen in selected):
            selected.append(result)
            seen_signatures.add(signature)
        if len(selected) == options_limit:
            return selected

    for result in ordered_results:
        signature = _result_signature(result)
        if signature in seen_signatures:
            continue
        selected.append(result)
        seen_signatures.add(signature)
        if len(selected) == options_limit:
            break

    return selected


def _generate_population(
    potential_sections: list[PotentialSection],
    demand_courses: dict[int, DemandCourse],
    feasible_candidates: dict[int, list[tuple[int, int, int]]],
    population_size: int,
) -> list[list[SectionGene]]:
    sections_by_course: dict[int, list[PotentialSection]] = {}
    for section in potential_sections:
        sections_by_course.setdefault(section.course_id, []).append(section)

    population = []
    for _ in range(population_size):
        used_teacher_slots: set[tuple[int, int]] = set()
        used_classroom_slots: set[tuple[int, int]] = set()
        chromosome: list[SectionGene] = []
        section_lookup: dict[int, SectionGene] = {}

        for course_id, sections in sections_by_course.items():
            course = demand_courses[course_id]
            preferred_sections = course.min_sections
            if course.max_sections > course.min_sections and course.demand % 20 >= 10 and random.random() < 0.35:
                preferred_sections += 1
            preferred_sections = min(preferred_sections, course.max_sections)

            for order, section in enumerate(sections, start=1):
                if order > preferred_sections:
                    gene = SectionGene(False, None, None, None)
                else:
                    gene = _random_gene(
                        section,
                        demand_courses,
                        feasible_candidates,
                        force_open=True,
                    )
                    candidates = feasible_candidates.get(course_id, [])
                    random.shuffle(candidates)
                    for teacher_id, classroom_id, timeslot_index in candidates:
                        if (teacher_id, timeslot_index) in used_teacher_slots:
                            continue
                        if (classroom_id, timeslot_index) in used_classroom_slots:
                            continue
                        gene = SectionGene(True, teacher_id, classroom_id, timeslot_index)
                        break
                    if gene.open_section:
                        used_teacher_slots.add((gene.teacher_id, gene.timeslot_index))
                        used_classroom_slots.add((gene.classroom_id, gene.timeslot_index))
                section_lookup[section.index] = gene

        for section in potential_sections:
            chromosome.append(section_lookup[section.index])
        population.append(chromosome)
    return population


def _tournament_selection(population, fitness_results, size=4):
    candidates = random.sample(range(len(population)), min(size, len(population)))
    best_index = max(candidates, key=lambda idx: fitness_results[idx].score)
    return [_clone_gene(gene) for gene in population[best_index]]


def _crossover(parent_a: list[SectionGene], parent_b: list[SectionGene]):
    if len(parent_a) <= 1:
        return parent_a[:], parent_b[:]
    point = random.randint(1, len(parent_a) - 1)
    return (
        parent_a[:point] + parent_b[point:],
        parent_b[:point] + parent_a[point:],
    )


def _mutate(
    chromosome: list[SectionGene],
    potential_sections: list[PotentialSection],
    demand_courses: dict[int, DemandCourse],
    feasible_candidates: dict[int, list[tuple[int, int, int]]],
    mutation_rate: float,
):
    for idx, gene in enumerate(chromosome):
        if random.random() >= mutation_rate:
            continue
        section = potential_sections[idx]
        if random.random() < 0.25:
            chromosome[idx] = _random_gene(
                section,
                demand_courses,
                feasible_candidates,
            )
            continue
        if not gene.open_section:
            chromosome[idx] = _random_gene(
                section,
                demand_courses,
                feasible_candidates,
            )
            continue
        candidates = feasible_candidates.get(section.course_id, [])
        if not candidates:
            chromosome[idx] = SectionGene(False, None, None, None)
            continue
        teacher_id, classroom_id, timeslot_index = random.choice(candidates)
        chromosome[idx].teacher_id = teacher_id
        chromosome[idx].classroom_id = classroom_id
        chromosome[idx].timeslot_index = timeslot_index
    return chromosome


def run_semester_planner(
    demand_courses: list[DemandCourse],
    teachers: list[TeacherResource],
    classrooms: list[ClassroomResource],
    timeslots: list[TimeSlotResource],
    population_size: int = 80,
    generations: int = 140,
    mutation_rate: float = 0.12,
    crossover_rate: float = 0.85,
    elitism: int = 4,
    options_limit: int = 3,
) -> list[FitnessResult]:
    if not demand_courses or not teachers or not classrooms or not timeslots:
        return []

    demand_map = {course.course_id: course for course in demand_courses}
    teacher_map = {teacher.teacher_id: teacher for teacher in teachers}
    classroom_map = {classroom.classroom_id: classroom for classroom in classrooms}
    timeslot_map = {slot.index: slot for slot in timeslots}
    feasible_candidates = _build_feasible_candidates(
        demand_map,
        teacher_map,
        classroom_map,
        timeslot_map,
    )
    if any(not candidates for candidates in feasible_candidates.values()):
        return []

    potential_sections: list[PotentialSection] = []
    for course in demand_courses:
        for section_number in range(1, course.max_sections + 1):
            potential_sections.append(
                PotentialSection(
                    index=len(potential_sections),
                    course_id=course.course_id,
                    course_code=course.code,
                    course_name=course.name,
                    section_number=section_number,
                )
            )

    population = _generate_population(
        potential_sections,
        demand_map,
        feasible_candidates,
        population_size,
    )
    archive: dict[str, FitnessResult] = {}

    def _signature(chromosome: list[SectionGene]) -> str:
        return "|".join(
            f"{int(gene.open_section)}:{gene.teacher_id}:{gene.classroom_id}:{gene.timeslot_index}"
            for gene in chromosome
        )

    for _ in range(generations):
        fitness_results = [
            evaluate_semester_schedule(
                chromosome,
                potential_sections,
                demand_map,
                teacher_map,
                classroom_map,
                timeslot_map,
            )
            for chromosome in population
        ]
        sorted_indexes = sorted(
            range(len(population)),
            key=lambda idx: fitness_results[idx].score,
            reverse=True,
        )

        for idx in sorted_indexes[:10]:
            signature = _signature(population[idx])
            archive.setdefault(signature, fitness_results[idx])

        if len(archive) > 250:
            trimmed_items = sorted(
                archive.items(),
                key=lambda item: item[1].score,
                reverse=True,
            )[:250]
            archive = dict(trimmed_items)

        new_population = [
            [_clone_gene(gene) for gene in population[idx]]
            for idx in sorted_indexes[:elitism]
        ]

        while len(new_population) < population_size:
            parent_a = _tournament_selection(population, fitness_results)
            parent_b = _tournament_selection(population, fitness_results)
            if random.random() < crossover_rate:
                child_a, child_b = _crossover(parent_a, parent_b)
            else:
                child_a, child_b = parent_a, parent_b
            new_population.append(
                _mutate(
                    child_a,
                    potential_sections,
                    demand_map,
                    feasible_candidates,
                    mutation_rate,
                )
            )
            if len(new_population) < population_size:
                new_population.append(
                    _mutate(
                        child_b,
                        potential_sections,
                        demand_map,
                        feasible_candidates,
                        mutation_rate,
                    )
                )
        population = new_population

    ordered = sorted(archive.values(), key=lambda result: result.score, reverse=True)
    return _select_diverse_results(ordered, options_limit=options_limit)
