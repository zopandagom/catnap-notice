#!/usr/bin/env python3
"""notices.json 형식 검사. 표준 라이브러리만 쓴다.

앱(냥자리 NoticeFeed)은 잘못된 공지를 조용히 빼고 넘어가므로, 여기서는 앱보다 엄격하게
모르는 키(오타)까지 오류로 잡는다. 사용법: python3 scripts/validate.py [notices.json]
"""

import json
import re
import struct
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
# 이 레포가 GitHub Pages 로 나가는 주소. 그림 주소가 이 아래면 레포 안 파일을 찾아 크기를 본다.
SITE = "https://zopandagom.github.io/catnap-notice/"

FEED_BYTE_LIMIT = 64 * 1024  # 앱 NoticeClientImpl.feedByteLimit
IMAGE_BYTE_LIMIT = 2 * 1024 * 1024  # 앱 NoticeClientImpl.imageByteLimit
IMAGE_MAX_PIXELS = 2048  # 앱 NoticeImage.maxPixelLength (긴 변)

LANGUAGES = ["ko", "en", "ja", "zh-Hans", "zh-Hant", "fr", "es", "de", "pt-BR", "it"]  # 앱 AppLanguage
NOTICE_KEYS = {"id", "startsAt", "endsAt", "minAppVersion", "maxAppVersion", "actionLink", "localizations"}
BLOCK_KEYS = {"text", "image", "imageDescription", "confirmTitle", "actionTitle"}
# 앱의 ISO8601DateFormatter 기본 형식: 초까지, 시간대(Z 또는 +09:00) 필수, 소수 초 없음.
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})$")
VERSION_PATTERN = re.compile(r"^\d+(\.\d+)*$")
# 추가 버튼 링크: 이 접두어 뒤의 퍼센트 인코딩된 https 주소는 앱 안 브라우저, 그 밖은 앱 밖에서 연다.
APP_SCHEME = "catnap-pandagom"
INTERNAL_PREFIX = f"{APP_SCHEME}://internal-url="
REQUIRED_LANGUAGES = ["ko", "en"]  # ko: 앱이 마지막에 고르는 언어, en: 지원하지 않는 언어 기기가 보는 언어

errors: list[str] = []


def error(where: str, message: str) -> None:
    errors.append(f"{where}: {message}")


def non_empty(value) -> bool:
    return isinstance(value, str) and value.strip() != ""


def is_https(value: str) -> bool:
    url = urlparse(value)
    return url.scheme.lower() == "https" and bool(url.hostname)


def parse_date(where: str, value):
    if not isinstance(value, str) or not DATE_PATTERN.match(value):
        error(where, f"날짜는 2026-12-01T00:00:00+09:00 형식이어야 합니다: {value!r}")
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        error(where, f"없는 날짜입니다: {value!r}")
        return None


def parse_version(where: str, value):
    if not isinstance(value, str) or not VERSION_PATTERN.match(value):
        error(where, f"버전은 1.2.3 처럼 점으로 나눈 숫자여야 합니다: {value!r}")
        return None
    return [int(part) for part in value.split(".")]


def version_less(a: list[int], b: list[int]) -> bool:
    count = max(len(a), len(b))
    return a + [0] * (count - len(a)) < b + [0] * (count - len(b))


def image_size(data: bytes):
    """PNG·JPEG 의 (가로, 세로). 모르는 형식이면 None."""
    if data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
        return struct.unpack(">II", data[16:24])
    if data[:2] == b"\xff\xd8":
        index = 2
        while index + 9 < len(data):
            if data[index] != 0xFF:
                index += 1
                continue
            marker = data[index + 1]
            if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7 or marker == 0xFF:
                index += 1 if marker == 0xFF else 2
                continue
            length = struct.unpack(">H", data[index + 2 : index + 4])[0]
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                height, width = struct.unpack(">HH", data[index + 5 : index + 9])
                return width, height
            index += 2 + length
    return None


def check_image(where: str, value: str) -> None:
    if not is_https(value):
        error(where, f"그림 주소는 https 여야 합니다: {value!r}")
        return
    if not value.startswith(SITE):
        return  # 다른 호스트의 그림은 주소 형식만 본다.
    path = ROOT / value[len(SITE) :]
    if not path.is_file():
        error(where, f"레포에 그림 파일이 없습니다: {path.relative_to(ROOT)}")
        return
    data = path.read_bytes()
    if len(data) > IMAGE_BYTE_LIMIT:
        error(where, f"그림이 2MB 를 넘습니다 ({len(data)} 바이트): {path.relative_to(ROOT)}")
    size = image_size(data)
    if size is None:
        error(where, f"PNG·JPEG 가 아니거나 읽을 수 없습니다: {path.relative_to(ROOT)}")
    elif min(size) <= 0 or max(size) > IMAGE_MAX_PIXELS:
        error(where, f"그림 긴 변이 {IMAGE_MAX_PIXELS}px 를 넘습니다 ({size[0]}x{size[1]}): {path.relative_to(ROOT)}")


def check_link(where: str, value) -> None:
    """앱 규칙(냥자리 Core `LinkDestination`): `catnap-pandagom://internal-url=<완전히 인코딩한 https 주소>` 는 앱 안 브라우저,
    https·itms-apps(host 있음)·mailto(주소 있음)는 앱 밖에서 연다. 그 밖은 앱이 팝업만 닫으므로 여기서 막는다."""
    if not non_empty(value):
        error(where, "비어 있지 않은 문자열이어야 합니다")
        return
    if value != value.strip() or re.search(r"\s", value):
        error(where, f"공백이 섞이면 앱이 열지 않습니다: {value!r}")
        return
    if value.startswith(INTERNAL_PREFIX):
        encoded = value[len(INTERNAL_PREFIX) :]
        # quote(주소, safe="") 결과만 받는다. 인코딩하지 않은 문자가 섞인 형태는 앱이 지원하지 않는다.
        if not re.fullmatch(r"[A-Za-z0-9._~%-]+", encoded) or not is_https(unquote(encoded)):
            error(where, f"internal-url= 뒤에는 퍼센트 인코딩한 https 주소가 와야 합니다: {value!r}")
        return
    url = urlparse(value)
    scheme = url.scheme.lower()
    if scheme == APP_SCHEME:
        error(where, f"{APP_SCHEME}:// 링크는 internal-url= 형태만 씁니다. 그 밖은 앱이 무시합니다: {value!r}")
    elif scheme in ("https", "itms-apps"):
        if not url.hostname:
            error(where, f"주소에 host 가 없습니다: {value!r}")
    elif scheme == "mailto":
        if not url.path:
            error(where, f"mailto: 뒤에 메일 주소가 없습니다: {value!r}")
    else:
        error(where, f"앱이 여는 링크는 catnap-pandagom://internal-url=…·https·itms-apps·mailto 뿐입니다: {value!r}")


def check_block(where: str, block, has_link: bool) -> None:
    if not isinstance(block, dict):
        error(where, "언어 블록은 객체여야 합니다")
        return
    for key in block.keys() - BLOCK_KEYS:
        error(where, f"모르는 키 {key!r} (쓸 수 있는 키: {', '.join(sorted(BLOCK_KEYS))})")
    for key in BLOCK_KEYS & block.keys():
        if not isinstance(block[key], str):
            error(where, f"{key} 는 문자열이어야 합니다")
    if not non_empty(block.get("text")) and not non_empty(block.get("image")):
        error(where, "text 와 image 중 하나는 있어야 합니다")
    if non_empty(block.get("image")):
        check_image(f"{where}.image", block["image"])
        if not non_empty(block.get("imageDescription")):
            error(where, "image 가 있으면 VoiceOver 용 imageDescription 도 넣어 주세요")
    has_title = non_empty(block.get("actionTitle"))
    if has_title and not has_link:
        error(where, "actionTitle 이 있는데 공지에 actionLink 가 없습니다")
    if has_link and not has_title:
        error(where, "공지에 actionLink 가 있는데 이 언어에 actionTitle 이 없어 버튼이 안 보입니다")


def check_notice(index: int, notice, seen_ids: set[str]) -> None:
    where = f"notices[{index}]"
    if not isinstance(notice, dict):
        error(where, "공지는 객체여야 합니다")
        return
    for key in notice.keys() - NOTICE_KEYS:
        error(where, f"모르는 키 {key!r} (쓸 수 있는 키: {', '.join(sorted(NOTICE_KEYS))})")

    notice_id = notice.get("id")
    if not non_empty(notice_id):
        error(where, "id 는 비어 있지 않은 문자열이어야 합니다")
    else:
        where = f"notices[{index}] ({notice_id})"
        if notice_id.strip() in seen_ids:
            error(where, "id 가 겹칩니다. 앱은 앞의 공지만 봅니다")
        seen_ids.add(notice_id.strip())

    starts = parse_date(f"{where}.startsAt", notice["startsAt"]) if "startsAt" in notice else None
    ends = parse_date(f"{where}.endsAt", notice["endsAt"]) if "endsAt" in notice else None
    if starts and ends and starts >= ends:
        error(where, "startsAt 은 endsAt 보다 앞이어야 합니다")

    low = parse_version(f"{where}.minAppVersion", notice["minAppVersion"]) if "minAppVersion" in notice else None
    high = parse_version(f"{where}.maxAppVersion", notice["maxAppVersion"]) if "maxAppVersion" in notice else None
    if low and high and version_less(high, low):
        error(where, "minAppVersion 이 maxAppVersion 보다 큽니다")

    has_link = "actionLink" in notice
    if has_link:
        check_link(f"{where}.actionLink", notice["actionLink"])

    blocks = notice.get("localizations")
    if not isinstance(blocks, dict) or not blocks:
        error(where, "localizations 는 언어별 블록이 든 객체여야 합니다")
        return
    for key in blocks.keys() - set(LANGUAGES):
        error(where, f"모르는 언어 {key!r} (쓸 수 있는 언어: {', '.join(LANGUAGES)})")
    for language in REQUIRED_LANGUAGES:
        if language not in blocks:
            error(where, f"{language} 블록은 꼭 있어야 합니다 (ko·en 필수)")
    for language in LANGUAGES:
        if language in blocks:
            check_block(f"{where}.localizations.{language}", blocks[language], has_link)


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "notices.json"
    raw = path.read_bytes()
    if len(raw) > FEED_BYTE_LIMIT:
        error(path.name, f"파일이 64KB 를 넘습니다 ({len(raw)} 바이트). 앱이 받지 않습니다")
    try:
        feed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exception:
        error(path.name, f"JSON 이 아닙니다: {exception}")
        feed = None

    if feed is not None:
        if not isinstance(feed, dict) or not isinstance(feed.get("notices"), list):
            error(path.name, '최상위는 {"notices": [...]} 여야 합니다')
        else:
            for key in feed.keys() - {"notices"}:
                error(path.name, f"모르는 최상위 키 {key!r}")
            seen_ids: set[str] = set()
            for index, notice in enumerate(feed["notices"]):
                check_notice(index, notice, seen_ids)

    if errors:
        print(f"FAIL: {path.name} 에 문제 {len(errors)}개", file=sys.stderr)
        for line in errors:
            print(f"  - {line}", file=sys.stderr)
        return 1
    count = len(feed["notices"])
    print(f"PASS: {path.name} (공지 {count}개)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
