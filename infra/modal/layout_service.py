import tempfile
from time import perf_counter

import modal

APP_NAME = "edgar-layout-service"
MODEL_REPO = "juliozhao/DocLayout-YOLO-DocStructBench"
MODEL_FILENAME = "doclayout_yolo_docstructbench_imgsz1024.pt"

app = modal.App(APP_NAME)

image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install(
        "libgl1",
        "libglib2.0-0",
    )
    .uv_pip_install(
        "doclayout-yolo==0.0.4",
        "huggingface-hub==1.31.0",
    )
)

model_cache = modal.Volume.from_name("edgar-model-cache")


@app.cls(
    image=image,
    gpu="T4",
    volumes={"/root/.cache/huggingface": model_cache},
    max_containers=1,
    scaledown_window=300,
)
class LayoutService:
    @modal.enter()
    def load_model(self):
        from doclayout_yolo import YOLOv10
        from huggingface_hub import hf_hub_download

        model_path = hf_hub_download(
            repo_id=MODEL_REPO,
            filename=MODEL_FILENAME,
            local_files_only=True,
        )

        self.model = YOLOv10(model_path)

    @modal.method()
    def analyze(self, image_bytes: bytes):
        with tempfile.NamedTemporaryFile(suffix=".jpg") as temporary_image:
            temporary_image.write(image_bytes)
            temporary_image.flush()

            start = perf_counter()

            results = self.model.predict(
                temporary_image.name,
                imgsz=1024,
                conf=0.2,
                device="cuda:0",
                verbose=False,
            )

            elapsed = perf_counter() - start

        result = results[0]

        detections = []

        for detection in result.boxes:
            class_id = int(detection.cls.item())

            detections.append(
                {
                    "class_name": result.names[class_id],
                    "confidence": float(detection.conf.item()),
                    "xyxy": detection.xyxy[0].tolist(),
                }
            )

        return {
            "predict_seconds": round(elapsed, 4),
            "original_shape": result.orig_shape,
            "detections": detections,
        }
