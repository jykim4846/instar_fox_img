from __future__ import annotations

import json
import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime

import requests

from config import Settings


@dataclass(frozen=True)
class TrendCandidate:
    keyword: str
    source: str


class TrendCollector:
    def __init__(self, settings: Settings, logger: logging.Logger) -> None:
        self.settings = settings
        self.logger = logger
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            }
        )

    def collect(self) -> list[TrendCandidate]:
        self.logger.info("트렌드 수집 시작")
        collected: list[TrendCandidate] = []

        for strategy in (
            self._collect_with_pytrends,
            self._collect_with_google_trends_rss,
            self._collect_with_google_suggestions,
        ):
            if len(collected) >= self.settings.min_trend_candidates:
                break

            try:
                result = strategy()
                collected = self._merge_unique(collected, result)
                self.logger.info(
                    "트렌드 수집 소스 완료: %s | 누적 %s개",
                    strategy.__name__,
                    len(collected),
                )
            except Exception as error:  # noqa: BLE001
                self.logger.error("트렌드 수집 실패: %s | %s", strategy.__name__, error)

        self.logger.info("트렌드 수집 종료 | 총 %s개", len(collected))
        return collected

    def _collect_with_pytrends(self) -> list[TrendCandidate]:
        try:
            from pytrends.request import TrendReq
        except ImportError as error:
            raise RuntimeError("pytrends 가 설치되지 않았습니다.") from error

        tz_minutes = int(
            datetime.now(self.settings.zoneinfo).utcoffset().total_seconds() // 60
        )
        client = TrendReq(hl=self.settings.locale, tz=tz_minutes)
        frame = client.trending_searches(pn="south_korea")
        keywords = frame.iloc[:, 0].dropna().astype(str).tolist()

        if not keywords:
            raise RuntimeError("pytrends 결과가 비어 있습니다.")

        return [
            TrendCandidate(keyword=keyword.strip(), source="Google Trends / pytrends")
            for keyword in keywords
            if keyword.strip()
        ]

    def _collect_with_google_trends_rss(self) -> list[TrendCandidate]:
        endpoints = (
            "https://trends.google.com/trends/trendingsearches/daily/rss?geo=KR",
            "https://trends.google.com/trending/rss?geo=KR",
        )
        errors: list[str] = []

        for endpoint in endpoints:
            try:
                response = self.session.get(
                    endpoint,
                    timeout=self.settings.request_timeout_seconds,
                )
                response.raise_for_status()
                root = ET.fromstring(response.text)
                items = [
                    item.text.strip()
                    for item in root.findall(".//item/title")
                    if item.text and item.text.strip()
                ]
                if items:
                    return [
                        TrendCandidate(keyword=item, source="Google Trends RSS")
                        for item in items
                    ]
            except Exception as error:  # noqa: BLE001
                errors.append(f"{endpoint}: {error}")

        raise RuntimeError("; ".join(errors) or "RSS 결과가 없습니다.")

    def _collect_with_google_suggestions(self) -> list[TrendCandidate]:
        seeds = [
            "요즘",
            "직장인",
            "소비",
            "연애",
            "습관",
            "챌린지",
            "앱",
            "유행",
            "밈",
            "자기관리",
        ]
        collected: list[TrendCandidate] = []

        for seed in seeds:
            response = self.session.get(
                "https://suggestqueries.google.com/complete/search",
                params={"client": "firefox", "hl": "ko", "gl": "kr", "q": seed},
                timeout=self.settings.request_timeout_seconds,
            )
            response.raise_for_status()
            payload = json.loads(response.text)
            suggestions = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
            for suggestion in suggestions:
                suggestion_text = str(suggestion).strip()
                if suggestion_text:
                    collected.append(
                        TrendCandidate(
                            keyword=suggestion_text,
                            source="Google Suggest Fallback",
                        )
                    )

        if not collected:
            raise RuntimeError("Google Suggest 결과가 없습니다.")

        return collected

    def _merge_unique(
        self,
        base: list[TrendCandidate],
        incoming: list[TrendCandidate],
    ) -> list[TrendCandidate]:
        seen = {self._normalize(item.keyword) for item in base}
        merged = list(base)

        for item in incoming:
            normalized = self._normalize(item.keyword)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            merged.append(item)
        return merged

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"[^0-9a-z가-힣]+", "", value.lower())
