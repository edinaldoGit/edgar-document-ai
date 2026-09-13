class ModalAnswerGenerationClient:
    def __init__(
        self,
        *,
        app_name: str = "edgar-answer-generation-service",
        class_name: str = "AnswerGenerationService",
    ):
        self._app_name = app_name
        self._class_name = class_name

    def generate(
        self,
        prompt: str,
        *,
        max_new_tokens: int = 256,
    ) -> dict:
        import modal

        service_class = modal.Cls.from_name(
            self._app_name,
            self._class_name,
        )

        service = service_class()

        return service.generate.remote(
            prompt,
            max_new_tokens=max_new_tokens,
        )
