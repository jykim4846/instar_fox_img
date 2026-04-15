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

    def post_reel(self, video_path: Path, caption: str) -> bool:
        try:
            public_url = self._upload_to_cloudinary(video_path, resource_type="video")
            creation_id = self._create_reel_container(public_url, caption)
            self._publish_reel(creation_id)
            self.logger.info("릴스 게시 성공 | %s", video_path.name)
            return True
        except Exception as e:
            self.logger.error("릴스 게시 실패 | %s | %s", video_path.name, e)
            return False

    def _upload_to_cloudinary(self, file_path: Path, resource_type: str = "image") -> str:
        result = cloudinary.uploader.upload(
            str(file_path),
            folder="instar_fox",
            public_id=file_path.stem,
            overwrite=True,
            resource_type=resource_type,
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

    def _create_reel_container(self, video_url: str, caption: str) -> str:
        resp = requests.post(
            f"{self.GRAPH_URL}/{self.ig_user_id}/media",
            data={
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption,
                "share_to_feed": "true",
                "access_token": self.access_token,
            },
            timeout=30,
        )
        if not resp.ok:
            self.logger.error("Meta Reels API 응답 | %s | %s", resp.status_code, resp.text)
        resp.raise_for_status()
        creation_id = resp.json()["id"]
        self.logger.info("릴스 컨테이너 생성 | id=%s", creation_id)
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

    def _publish_reel(self, creation_id: str, max_wait: int = 120) -> None:
        """릴스는 트랜스코딩이 필요하므로 status polling 후 게시한다."""
        for _ in range(max_wait // 5):
            time.sleep(5)
            resp = requests.get(
                f"{self.GRAPH_URL}/{creation_id}",
                params={
                    "fields": "status_code",
                    "access_token": self.access_token,
                },
                timeout=15,
            )
            resp.raise_for_status()
            status = resp.json().get("status_code")
            self.logger.info("릴스 트랜스코딩 상태 | %s", status)
            if status == "FINISHED":
                break
            if status == "ERROR":
                raise RuntimeError("릴스 트랜스코딩 실패")
        else:
            raise TimeoutError("릴스 트랜스코딩 타임아웃 (120초)")

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
        self.logger.info("릴스 게시 완료 | media_id=%s", media_id)
