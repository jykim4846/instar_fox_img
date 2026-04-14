from __future__ import annotations

import os
import time
from pathlib import Path

import cloudinary
import cloudinary.uploader
import requests


class InstagramPoster:
    GRAPH_URL = "https://graph.facebook.com/v19.0"

    def __init__(self, logger) -> None:
        self.logger = logger
        self.ig_user_id = os.getenv("IG_USER_ID", "").strip()
        self.access_token = os.getenv("META_ACCESS_TOKEN", "").strip()

        cloudinary.config(
            cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", "").strip(),
            api_key=os.getenv("CLOUDINARY_API_KEY", "").strip(),
            api_secret=os.getenv("CLOUDINARY_API_SECRET", "").strip(),
        )

    def post(self, image_path: Path, caption: str) -> bool:
        try:
            public_url = self._upload_to_cloudinary(image_path)
            creation_id = self._create_media_container(public_url, caption)
            self._publish(creation_id)
            self.logger.info("인스타그램 게시 성공 | %s", image_path.name)
            return True
        except Exception as e:
            self.logger.error("인스타그램 게시 실패 | %s | %s", image_path.name, e)
            return False

    def _upload_to_cloudinary(self, image_path: Path) -> str:
        result = cloudinary.uploader.upload(
            str(image_path),
            folder="instar_fox",
            public_id=image_path.stem,
            overwrite=True,
        )
        url = result["secure_url"]
        self.logger.info("Cloudinary 업로드 완료 | %s", url)
        return url

    def _create_media_container(self, image_url: str, caption: str) -> str:
        resp = requests.post(
            f"{self.GRAPH_URL}/{self.ig_user_id}/media",
            data={
                "image_url": image_url,
                "caption": caption,
                "access_token": self.access_token,
            },
            timeout=30,
        )
        if not resp.ok:
            self.logger.error("Meta API 응답 | %s | %s", resp.status_code, resp.text)
        resp.raise_for_status()
        creation_id = resp.json()["id"]
        self.logger.info("미디어 컨테이너 생성 | id=%s", creation_id)
        return creation_id

    def _publish(self, creation_id: str) -> None:
        # 컨테이너 준비 대기 (Meta 권장)
        time.sleep(5)
        resp = requests.post(
            f"{self.GRAPH_URL}/{self.ig_user_id}/media_publish",
            data={
                "creation_id": creation_id,
                "access_token": self.access_token,
            },
            timeout=30,
        )
        resp.raise_for_status()
        media_id = resp.json()["id"]
        self.logger.info("게시 완료 | media_id=%s", media_id)
