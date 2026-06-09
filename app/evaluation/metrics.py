def exact_match_score(actual: str, expected: str) -> float:
    return 1.0 if actual == expected else 0.0


def contains_required_sections(markdown: str, sections: list[str]) -> float:
    if not sections:
        return 1.0
    found = sum(1 for section in sections if section.lower() in markdown.lower())
    return found / len(sections)


def non_empty_ratio(values: list[object]) -> float:
    if not values:
        return 0.0
    return sum(1 for value in values if bool(value)) / len(values)
