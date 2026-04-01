ENTITY_LABELS = [
    "NAME",
    "PHONE",
    "EMAIL",
    "DEGREE",
    "MAJOR",
    "SCHOOL",
    "COMPANY",
    "TITLE",
    "SKILL",
    "PROJECT",
    "EXPERIENCE_YEARS",
    "GENDER",
    "AGE",
    "HOMETOWN",
]


def build_bio_labels():
    labels = ["O"]
    for entity in ENTITY_LABELS:
        labels.append(f"B-{entity}")
        labels.append(f"I-{entity}")
    return labels
