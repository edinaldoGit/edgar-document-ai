def build_grounded_answer_prompt(
    *,
    question: str,
    evidence_context: str,
) -> str:
    question = question.strip()
    evidence_context = evidence_context.strip()

    if not question:
        raise ValueError("Question must not be blank.")

    if not evidence_context:
        raise ValueError("Evidence context must not be blank.")

    return (
        "Responda à pergunta usando exclusivamente as evidências fornecidas.\n"
        "Não use conhecimento externo e não invente informações.\n"
        "Se as evidências forem insuficientes para responder, diga isso claramente.\n"
        "Ao sustentar uma afirmação, indique a evidência correspondente "
        "usando o formato [Evidence N].\n"
        "Seja objetivo e preserve números, termos técnicos e relações "
        "presentes nas evidências.\n\n"
        f"Pergunta:\n{question}\n\n"
        f"Evidências:\n{evidence_context}\n\n"
        "Resposta:"
    )
