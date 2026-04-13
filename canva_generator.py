from __future__ import annotations

import base64
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from config import Settings
from scorer import RankedCandidate


CANVA_API_BASE = "https://api.canva.com/rest/v1"


@dataclass(frozen=True)
class CanvaTemplateConfig:
    name: str
    brand_template_id: str
    field_mapping: dict[str, str]


@dataclass(frozen=True)
class CanvaDesign:
    template_name: str
    design_id: str
    design_title: str
    edit_url: str
    view_url: str
    thumbnail_url: str | None = None


class CanvaGenerator:
    def __init__(self, settings: Settings, logger: logging.Logger) -> None:
        self.settings = settings
        self.logger = logger
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "estj-fox-pipeline/1.0"})
        self._access_token: str | None = None
        self._rotated_refresh_token: str | None = None
        self._template_configs: list[CanvaTemplateConfig] | None = None
        self._dataset_cache: dict[str, dict[str, Any]] = {}

    def is_enabled(self) -> bool:
        if not self.settings.canva_enabled:
            return False
        if self.settings.canva_configured:
            return True
        self.logger.warning(
            "Canva 연동이 활성화됐지만 설정이 부족합니다. secrets 와 템플릿 설정 파일을 확인하세요."
        )
        return False

    def generate_designs(self, candidate: RankedCandidate) -> list[CanvaDesign]:
        if not self.is_enabled():
            return []

        access_token = self._get_access_token()
        designs: list[CanvaDesign] = []

        for template in self._load_template_configs():
            try:
                dataset = self._get_dataset(template.brand_template_id, access_token)
                data = self._build_autofill_data(candidate, dataset, template.field_mapping)
                if not data:
                    self.logger.warning(
                        "Canva 템플릿 데이터 매핑 결과가 비어 있어 건너뜁니다 | template=%s",
                        template.name,
                    )
                    continue

                job_id = self._create_autofill_job(
                    brand_template_id=template.brand_template_id,
                    data=data,
                    access_token=access_token,
                )
                design = self._poll_autofill_job(
                    job_id=job_id,
                    access_token=access_token,
                    template_name=template.name,
                )
                if design is not None:
                    designs.append(design)
                    self.logger.info(
                        "Canva 디자인 생성 성공 | template=%s | design_id=%s",
                        template.name,
                        design.design_id,
                    )
            except Exception as error:  # noqa: BLE001
                self.logger.error(
                    "Canva 디자인 생성 실패 | template=%s | title=%s | %s",
                    template.name,
                    candidate.title,
                    error,
                )

        self._persist_rotated_refresh_token()
        return designs

    def _get_access_token(self) -> str:
        if self._access_token is not None:
            return self._access_token

        if not self.settings.canva_client_id or not self.settings.canva_client_secret:
            raise ValueError("Canva client credentials 가 비어 있습니다.")
        if not self.settings.canva_refresh_token:
            raise ValueError("Canva refresh token 이 비어 있습니다.")

        credentials = (
            f"{self.settings.canva_client_id}:{self.settings.canva_client_secret}".encode("utf-8")
        )
        authorization = base64.b64encode(credentials).decode("utf-8")

        response = self.session.post(
            f"{CANVA_API_BASE}/oauth/token",
            headers={
                "Authorization": f"Basic {authorization}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.settings.canva_refresh_token,
            },
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()

        access_token = payload.get("access_token")
        refresh_token = payload.get("refresh_token")
        if not access_token or not refresh_token:
            raise ValueError("Canva 토큰 응답에 access_token 또는 refresh_token 이 없습니다.")

        self._access_token = access_token
        self._rotated_refresh_token = refresh_token
        return access_token

    def _load_template_configs(self) -> list[CanvaTemplateConfig]:
        if self._template_configs is not None:
            return self._template_configs

        config_path = self.settings.canva_template_config_path
        if not config_path.exists():
            raise FileNotFoundError(f"Canva 템플릿 설정 파일이 없습니다: {config_path}")

        raw = json.loads(config_path.read_text(encoding="utf-8"))
        templates = raw.get("templates", [])
        if not templates:
            raise ValueError("Canva 템플릿 설정이 비어 있습니다.")

        parsed: list[CanvaTemplateConfig] = []
        for item in templates:
            parsed.append(
                CanvaTemplateConfig(
                    name=str(item["name"]).strip(),
                    brand_template_id=str(item["brand_template_id"]).strip(),
                    field_mapping=dict(item["field_mapping"]),
                )
            )

        self._template_configs = parsed
        return parsed

    def _get_dataset(self, brand_template_id: str, access_token: str) -> dict[str, Any]:
        if brand_template_id in self._dataset_cache:
            return self._dataset_cache[brand_template_id]

        response = self.session.get(
            f"{CANVA_API_BASE}/brand-templates/{brand_template_id}/dataset",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        dataset = payload.get("dataset", {})
        self._dataset_cache[brand_template_id] = dataset
        return dataset

    def _build_autofill_data(
        self,
        candidate: RankedCandidate,
        dataset: dict[str, Any],
        field_mapping: dict[str, str],
    ) -> dict[str, dict[str, str]]:
        candidate_values = {
            "title": candidate.title,
            "topic": candidate.topic,
            "category": candidate.category,
            "cut1": candidate.cut1,
            "cut2": candidate.cut2,
            "cut3": candidate.cut3,
            "caption": candidate.caption,
            "hashtags": " ".join(candidate.hashtags),
            "hashtags_text": " ".join(candidate.hashtags),
            "ai_score": str(candidate.ai_score),
            "recommended": "추천" if candidate.recommended else "",
            "preview_text": candidate.preview_text,
            "post_date": candidate.post_date,
        }

        data: dict[str, dict[str, str]] = {}
        for canva_field, source_key in field_mapping.items():
            field_definition = dataset.get(canva_field)
            if not field_definition:
                self.logger.warning("Canva 필드가 dataset 에 없습니다 | field=%s", canva_field)
                continue
            if field_definition.get("type") != "text":
                self.logger.warning(
                    "현재는 Canva text 필드만 자동 채움 지원 | field=%s | type=%s",
                    canva_field,
                    field_definition.get("type"),
                )
                continue

            if source_key.startswith("literal:"):
                value = source_key.removeprefix("literal:")
            else:
                value = candidate_values.get(source_key, "")

            if not value:
                continue

            data[canva_field] = {"type": "text", "text": str(value)}

        return data

    def _create_autofill_job(
        self,
        brand_template_id: str,
        data: dict[str, dict[str, str]],
        access_token: str,
    ) -> str:
        response = self.session.post(
            f"{CANVA_API_BASE}/autofills",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={
                "brand_template_id": brand_template_id,
                "data": data,
            },
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        job = payload.get("job", {})
        job_id = job.get("id")
        if not job_id:
            raise ValueError("Canva autofill job id 가 없습니다.")
        return str(job_id)

    def _poll_autofill_job(
        self,
        job_id: str,
        access_token: str,
        template_name: str,
    ) -> CanvaDesign | None:
        deadline = time.time() + self.settings.canva_poll_timeout_seconds

        while time.time() < deadline:
            response = self.session.get(
                f"{CANVA_API_BASE}/autofills/{job_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=self.settings.request_timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
            job = payload.get("job", {})
            status = job.get("status")

            if status == "success":
                result = job.get("result", {})
                design = result.get("design", {})
                urls = design.get("urls", {})
                return CanvaDesign(
                    template_name=template_name,
                    design_id=str(design.get("id", "")),
                    design_title=str(design.get("title", "")),
                    edit_url=str(urls.get("edit_url") or design.get("url") or ""),
                    view_url=str(urls.get("view_url") or design.get("url") or ""),
                    thumbnail_url=(
                        str(design.get("thumbnail", {}).get("url"))
                        if design.get("thumbnail", {}).get("url")
                        else None
                    ),
                )

            if status == "failed":
                error = job.get("error", {})
                raise RuntimeError(
                    f"Canva autofill job failed: {error.get('code')} | {error.get('message')}"
                )

            time.sleep(self.settings.canva_poll_interval_seconds)

        raise TimeoutError(f"Canva autofill job timeout | job_id={job_id}")

    def _persist_rotated_refresh_token(self) -> None:
        if not self._rotated_refresh_token:
            return

        output_path = self.settings.canva_refresh_token_output_path
        output_path.write_text(self._rotated_refresh_token, encoding="utf-8")


def load_canva_templates(path: Path) -> list[CanvaTemplateConfig]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        CanvaTemplateConfig(
            name=str(item["name"]).strip(),
            brand_template_id=str(item["brand_template_id"]).strip(),
            field_mapping=dict(item["field_mapping"]),
        )
        for item in raw.get("templates", [])
    ]
