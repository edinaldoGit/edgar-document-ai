from typing import Any


class ModalVisualDescriptionClient:
    def __init__(
        self,
        *,
        app_name: str = "edgar-visual-description-service",
        class_name: str = "VisualDescriptionService",
    ):
        if not app_name.strip():
            raise ValueError("Modal app name must not be blank.")

        if not class_name.strip():
            raise ValueError("Modal class name must not be blank.")

        self._app_name = app_name
        self._class_name = class_name
        self._service: Any | None = None

    def describe_image(
        self,
        image_bytes: bytes,
        *,
        prompt: str,
        context: str | None = None,
    ) -> dict[str, Any]:
        if not image_bytes:
            raise ValueError("Image bytes must not be empty.")

        if not prompt.strip():
            raise ValueError("Prompt must not be blank.")

        service = self._get_service()

        result = service.describe.remote(
            image_bytes,
            prompt=prompt,
            context=context,
        )

        if not isinstance(result, dict):
            raise RuntimeError("Modal visual description service returned an invalid response.")

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
