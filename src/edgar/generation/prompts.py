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
        "Não expanda siglas, não defina termos e não acrescente explicações "
        "que não estejam explicitamente presentes nas evidências.\n"
        "Se as evidências forem insuficientes para responder, diga isso claramente.\n"
        "Cada frase que contenha uma afirmação factual deve terminar com "
        "a citação da evidência que sustenta diretamente essa frase.\n"
        "Não cite uma evidência apenas porque ela trata do mesmo assunto.\n"
        "Use citações individuais no formato [Evidence N]. "
        "Quando mais de uma evidência sustentar a mesma frase, escreva "
        "[Evidence 1] [Evidence 2], nunca combine números dentro dos mesmos colchetes.\n"
        "Seja objetivo e preserve números, siglas, termos técnicos e relações "
        "exatamente como aparecem nas evidências.\n\n"
        f"Pergunta:\n{question}\n\n"
        f"Evidências:\n{evidence_context}\n\n"
        "Resposta:"
    )
