import sys
from types import SimpleNamespace

from edgar.infrastructure.modal_answer_generation_client import (
    ModalAnswerGenerationClient,
)


class FakeRemoteMethod:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def remote(self, *args, **kwargs):
        self.calls.append(
            (
                args,
                kwargs,
            )
        )
        return self.result


class FakeService:
    def __init__(self, remote_method):
        self.generate = remote_method


class FakeServiceClass:
    def __init__(self, service):
        self.service = service
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return self.service


class FakeCls:
    def __init__(self, service_class):
        self.service_class = service_class
        self.calls = []

    def from_name(
        self,
        app_name,
        class_name,
    ):
        self.calls.append(
            (
                app_name,
                class_name,
            )
        )
        return self.service_class


def install_fake_modal(
    monkeypatch,
    *,
    result,
):
    remote_method = FakeRemoteMethod(result)

    service = FakeService(remote_method)

    service_class = FakeServiceClass(service)

    fake_cls = FakeCls(service_class)

    fake_modal = SimpleNamespace(Cls=fake_cls)

    monkeypatch.setitem(
        sys.modules,
        "modal",
        fake_modal,
    )

    return (
        fake_cls,
        service_class,
        remote_method,
    )


def test_calls_modal_answer_generation_service(
    monkeypatch,
):
    result = {
        "answer": "Resposta fundamentada.",
        "model": "Qwen/Qwen2.5-7B-Instruct",
    }

    (
        fake_cls,
        service_class,
        remote_method,
    ) = install_fake_modal(
        monkeypatch,
        result=result,
    )

    client = ModalAnswerGenerationClient()

    returned = client.generate(
        "Prompt de teste",
        max_new_tokens=128,
    )

    assert returned == result

    assert fake_cls.calls == [
        (
            "edgar-answer-generation-service",
            "AnswerGenerationService",
        )
    ]

    assert service_class.calls == 1

    assert remote_method.calls == [
        (
            ("Prompt de teste",),
            {
                "max_new_tokens": 128,
            },
        )
    ]


def test_uses_default_token_limit(
    monkeypatch,
):
    (
        _,
        _,
        remote_method,
    ) = install_fake_modal(
        monkeypatch,
        result={"answer": "Resposta"},
    )

    client = ModalAnswerGenerationClient()

    client.generate(
        "Prompt",
    )

    assert remote_method.calls == [
        (
            ("Prompt",),
            {
                "max_new_tokens": 256,
            },
        )
    ]


def test_supports_custom_modal_names(
    monkeypatch,
):
    (
        fake_cls,
        _,
        _,
    ) = install_fake_modal(
        monkeypatch,
        result={"answer": "Resposta"},
    )

    client = ModalAnswerGenerationClient(
        app_name="custom-app",
        class_name="CustomService",
    )

    client.generate(
        "Prompt",
    )

    assert fake_cls.calls == [
        (
            "custom-app",
            "CustomService",
        )
    ]
