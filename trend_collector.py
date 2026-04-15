from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import requests

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

GOOGLE_NEWS_RSS_URLS = [
    "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko",           # 주요 뉴스
    "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtdHZHZ0pMVWlnQVAB?hl=ko&gl=KR&ceid=KR:ko",  # 엔터/문화
]

_UNSPLASH_QUERY_MAP = [
    (("경제", "금융", "주식", "부동산", "취업", "기업", "투자", "물가"), "business economy office"),
    (("연예", "영화", "드라마", "음악", "K팝", "아이돌", "배우", "방송"), "entertainment performance stage"),
    (("스포츠", "축구", "야구", "농구", "운동", "올림픽"), "sports stadium athlete"),
    (("건강", "의료", "병원", "식품", "다이어트", "운동"), "health wellness nature"),
    (("IT", "기술", "AI", "반도체", "스마트폰", "앱", "인공지능"), "technology digital abstract"),
    (("날씨", "환경", "자연", "계절", "봄", "여름", "가을", "겨울"), "nature landscape sky"),
    (("여행", "관광", "해외"), "travel city architecture"),
    (("교육", "학교", "시험", "입시"), "study library books"),
    (("패션", "뷰티", "쇼핑", "뷰티"), "fashion lifestyle aesthetic"),
    (("음식", "맛집", "카페", "요리"), "food cafe restaurant"),
]
_DEFAULT_UNSPLASH_QUERY = "korea city people street"


@dataclass(frozen=True)
class TrendItem:
    keyword: str
    description: str


@dataclass(frozen=True)
class TrendKeyword:
    keyword: str
    traffic: str       # e.g. "200,000+"
    traffic_num: int   # e.g. 200000 (정렬용)
    description: str


@dataclass
class TrendCollection:
    items: list[TrendItem]
    image_path: Path | None
    image_credit: str


class TrendCollector:
    def __init__(self, unsplash_key: str, logger, output_dir: Path) -> None:
        self.unsplash_key = unsplash_key
        self.logger = logger
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def collect(self, limit: int = 7) -> TrendCollection:
        items = self._fetch_google_news(limit)
        if not items:
            self.logger.warning("뉴스 수집 실패 - 빈 결과")
            return TrendCollection(items=[], image_path=None, image_credit="")
        image_path, credit = self._fetch_unsplash_image(items)
        return TrendCollection(items=items, image_path=image_path, image_credit=credit)

    def _fetch_google_news(self, limit: int) -> list[TrendItem]:
        seen: set[str] = set()
        items: list[TrendItem] = []

        for url in GOOGLE_NEWS_RSS_URLS:
            if len(items) >= limit:
                break
            try:
                resp = self.session.get(url, timeout=15)
                resp.raise_for_status()
                root = ET.fromstring(resp.content)
                for elem in root.findall(".//item"):
                    if len(items) >= limit:
                        break
                    raw_title = _clean_html(elem.findtext("title", "")).strip()
                    if not raw_title:
                        continue
                    # "뉴스제목 - 출처명" 형식 파싱
                    if " - " in raw_title:
                        keyword, source = raw_title.rsplit(" - ", 1)
                    else:
                        keyword, source = raw_title, ""
                    keyword = keyword.strip()
                    if not keyword or keyword in seen:
                        continue
                    seen.add(keyword)
                    items.append(TrendItem(keyword=keyword, description=source.strip() or "오늘의 뉴스"))
            except Exception as e:
                self.logger.warning("Google News RSS 수집 실패 | %s | %s", url, e)

        return items

    def _fetch_unsplash_image(self, items: list[TrendItem]) -> tuple[Path | None, str]:
        query = _infer_unsplash_query(items)
        try:
            resp = self.session.get(
                "https://api.unsplash.com/search/photos",
                params={
                    "query": query,
                    "client_id": self.unsplash_key,
                    "per_page": 3,
                    "orientation": "squarish",
                },
                timeout=15,
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
            if not results:
                self.logger.warning("Unsplash 결과 없음 | query=%s", query)
                return None, ""

            photo = results[0]
            img_url = photo["urls"]["regular"]
            credit = photo.get("user", {}).get("name", "Unsplash")

            self.output_dir.mkdir(parents=True, exist_ok=True)
            img_path = self.output_dir / "trend_bg.jpg"
            img_resp = self.session.get(img_url, timeout=30)
            img_resp.raise_for_status()
            img_path.write_bytes(img_resp.content)

            self.logger.info("Unsplash 이미지 다운로드 완료 | %s | %s", query, credit)
            return img_path, credit
        except Exception as e:
            self.logger.warning("Unsplash 이미지 수집 실패 | %s", e)
            return None, ""


def _infer_unsplash_query(items: list[TrendItem]) -> str:
    combined = " ".join(item.keyword for item in items)
    for keywords, query in _UNSPLASH_QUERY_MAP:
        if any(kw in combined for kw in keywords):
            return query
    return _DEFAULT_UNSPLASH_QUERY


GOOGLE_TRENDS_RSS = "https://trends.google.com/trending/rss?geo=KR"


def fetch_trending_keywords(limit: int = 3, logger=None) -> list[TrendKeyword]:
    """Google Trends daily trending RSS에서 검색수 포함 키워드를 가져온다."""
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    try:
        resp = session.get(GOOGLE_TRENDS_RSS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        if logger:
            logger.warning("Google Trends RSS 수집 실패 | %s", e)
        return []

    root = ET.fromstring(resp.content)
    ns = {"ht": "https://trends.google.com/trending/rss"}
    items: list[TrendKeyword] = []
    seen: set[str] = set()

    for elem in root.findall(".//item"):
        title = _clean_html(elem.findtext("title", "")).strip()
        if not title or title in seen:
            continue
        seen.add(title)

        traffic_raw = elem.findtext("ht:approx_traffic", "", ns).strip()
        traffic_num = _parse_traffic(traffic_raw)

        desc_elem = elem.find("ht:news_item", ns)
        desc = ""
        if desc_elem is not None:
            desc = _clean_html(desc_elem.findtext("ht:news_item_title", "", ns)).strip()

        items.append(TrendKeyword(
            keyword=title,
            traffic=traffic_raw or "10,000+",
            traffic_num=traffic_num,
            description=desc or "오늘의 트렌드",
        ))

    items.sort(key=lambda x: x.traffic_num, reverse=True)
    return items[:limit]


def _parse_traffic(raw: str) -> int:
    """'200,000+' 같은 문자열을 정수로 변환한다."""
    cleaned = raw.replace(",", "").replace("+", "").strip()
    try:
        return int(cleaned)
    except ValueError:
        return 0


def _clean_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()
