from copy import deepcopy

TASK_ROOTS = {
    "basic_info": ("basicInfo",),
    "work_experience": ("workExperience",),
    "project_experience": ("projectExperience",),
    "education": ("education",),
    "skills_strengths": ("professionalSkills", "personalStrengths"),
    "publication": ("publicationList",),
    "competition": ("competitionList",),
    "honor": ("honorList",),
    "research_direction": ("researchDirectionList",),
    "social_profile": ("socialProfileList",),
}
EXTRACT_TYPES = tuple(TASK_ROOTS)
RECORD_ROOTS = tuple(
    root
    for roots in TASK_ROOTS.values()
    for root in roots
    if root not in ("basicInfo", "professionalSkills", "personalStrengths")
)


def complete_resume(data):

    result = deepcopy(data)
    result.setdefault("basicInfo", {})
    for key in RECORD_ROOTS:
        result.setdefault(key, [])
    for key in ("professionalSkills", "personalStrengths"):
        result.setdefault(key, "")
    return result


def validate_task_result(task, result):

    if not isinstance(result, dict):
        raise ValueError("Model result must be a JSON object")
    selected = {}
    for key in TASK_ROOTS[task]:
        if key not in result:
            raise ValueError("Missing JSON root: " + key)
        value = result[key]
        if key == "basicInfo":
            valid = isinstance(value, dict)
        elif key in RECORD_ROOTS:
            valid = isinstance(value, list) and all(
                isinstance(x, dict) for x in value
            )
        else:
            valid = isinstance(value, (list, str))
        if not valid:
            raise ValueError("Invalid JSON type for " + key)
        selected[key] = value
    return selected
