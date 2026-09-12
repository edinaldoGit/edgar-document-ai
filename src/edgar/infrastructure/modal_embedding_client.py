from typing import Any


class ModalEmbeddingClient:
    def __init__(
        self,
        *,
        app_name: str = "edgar-embedding-service",
        class_name: str = "EmbeddingService",
    ):
        if not app_name.strip():
            raise ValueError("Modal app name must not be blank.")

        if not class_name.strip():
            raise ValueError("Modal class name must not be blank.")

        self._app_name = app_name
        self._class_name = class_name
        self._service: Any | None = None

    def embed_texts(
        self,
        texts: list[str],
    ) -> dict[str, Any]:
        if not texts:
            raise ValueError("Texts must not be empty.")

        if any(not text.strip() for text in texts):
            raise ValueError("Texts must not contain blank values.")

        service = self._get_service()

        result = service.embed.remote(texts)

        if not isinstance(result, dict):
            raise RuntimeError("Modal embedding service returned an invalid response.")

        return result

    def _get_service(self) -> Any:
        if self._service is not None:
            return self._service

        try:
            import modal
        except ModuleNotFoundError as error:
            raise RuntimeError(
                "Modal support is not installed. "
                "Install the EDGAR cloud extra with: uv sync --extra cloud"
            ) from error

        remote_class = modal.Cls.from_name(
            self._app_name,
            self._class_name,
        )

        self._service = remote_class()

        return self._service
