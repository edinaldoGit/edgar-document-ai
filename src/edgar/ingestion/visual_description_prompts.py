from edgar.domain import ComponentType

FIGURE_DESCRIPTION_PROMPT = """
Describe the educational figure shown in the image.

Focus on:
- what the figure represents;
- the main visible elements;
- labels, legends, axes, symbols, and annotations when present;
- spatial, quantitative, or conceptual relationships between elements;
- the main information a student should understand from the figure.

Preserve important names, values, units, and terminology exactly when readable.
Do not invent information that is not visible in the image.
Do not describe decorative or irrelevant visual details.
Return a concise factual description in Portuguese.
""".strip()


TABLE_DESCRIPTION_PROMPT = """
Interpret the educational table shown in the image.

Focus on:
- what the rows and columns represent;
- the relationships between headers and cell values;
- important values, units, categories, and labels;
- comparisons, trends, maxima, minima, or notable differences when present;
- the main information a student should understand from the table.

Preserve important names, values, units, and terminology exactly when readable.
Do not flatten the table into an unordered sequence of cell contents.
Do not invent information that is not visible in the image.
Return a concise factual description in Portuguese.
""".strip()


def visual_description_prompt(
    component_type: ComponentType,
) -> str:
    if component_type == ComponentType.FIGURE:
        return FIGURE_DESCRIPTION_PROMPT

    if component_type == ComponentType.TABLE:
        return TABLE_DESCRIPTION_PROMPT

    raise ValueError(f"Unsupported component type for visual description: {component_type.value}")
