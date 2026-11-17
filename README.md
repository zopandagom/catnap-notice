# catnap-notice

냥자리 앱 안 공지 데이터. GitHub Pages 로 나가며 앱은 아래 주소 하나만 받는다.

```
https://zopandagom.github.io/catnap-notice/notices.json
```

- 앱에 박힌 주소라 **레포·계정 이름을 바꾸면 이미 깔린 앱이 공지를 못 받는다.**
- 공개 레포라 올린 내용과 기록을 누구나 볼 수 있다. `startsAt` 을 미래로 둔 공지도 레포에서는 미리 보이므로 공개해도 될 때 올린다.
- `main` 에는 PR 로만 들어간다. PR 마다 CI(`validate`)가 형식을 검사하고, 통과해야 머지할 수 있다. 머지 뒤 Pages 배포까지 몇 분 걸린다.
- 로컬 검사: `python3 scripts/validate.py`

## 앱이 공지를 고르는 방식
- 앱을 켤 때마다 `notices.json` 을 받아, 배열 순서대로 띄울 수 있는 첫 공지 **하나**를 띄운다.
- 띄울 수 있는 공지: 기간 안(`startsAt` ≤ 지금 < `endsAt`), 앱 버전 범위 안, 아직 안 본 공지(확인·추가 버튼으로 닫으면 id 를 기억한다).
- 언어 블록은 앱 언어 → `en` → `ko` 순으로 고른다.
- 첫 실행(튜토리얼이 뜬 실행)에는 띄우지 않고 다음 실행에 띄운다. 판·구매 창 같은 다른 창이 떠 있으면 닫힐 때까지 기다린다.
- 같은 공지를 다시 띄우려면 `id` 를 바꾼다.

## 형식

```json
{
  "notices": [
    {
      "id": "2026-12-winter-chapters",
      "startsAt": "2026-12-01T00:00:00+09:00",
      "endsAt": "2026-12-31T00:00:00+09:00",
      "minAppVersion": "1.1",
      "maxAppVersion": "1.9.9",
      "actionLink": "https://apps.apple.com/app/id0000000000",
      "localizations": {
        "ko": {
          "text": "겨울 장 20개가 새로 열렸어요!",
          "image": "https://zopandagom.github.io/catnap-notice/images/winter.png",
          "imageDescription": "눈 쌓인 창가에서 자는 고양이들",
          "confirmTitle": "좋아요",
          "actionTitle": "업데이트하기"
        },
        "en": {
          "text": "20 new winter chapters are here!",
          "image": "https://zopandagom.github.io/catnap-notice/images/winter.png",
          "imageDescription": "Cats sleeping by a snowy window",
          "actionTitle": "Update"
        }
      }
    }
  ]
}
```

| 키 | 필수 | 설명 |
|---|---|---|
| `id` | ✅ | 공지 구분자. 겹치면 안 된다 |
| `startsAt` · `endsAt` | | 보이는 기간. `2026-12-01T00:00:00+09:00` 형식(시간대 필수, 소수 초 없음). 없으면 그쪽이 열려 있다 |
| `minAppVersion` · `maxAppVersion` | | 띄울 앱 버전 범위(양 끝 포함). `1.2.3` 형식 |
| `actionLink` | | 추가 버튼을 누르면 팝업을 닫고 여는 https 주소(앱 안 Safari 화면) |
| `localizations` | ✅ | 언어별 블록. 언어는 `ko`(필수) `en` `ja` `zh-Hans` `zh-Hant` `fr` `es` `de` `pt-BR` `it` |

언어 블록:

| 키 | 설명 |
|---|---|
| `text` | 본문. `text`·`image` 중 하나는 있어야 한다 |
| `image` | https 그림 주소. 이 레포의 `images/` 에 두면 CI 가 크기(2MB 이하, 긴 변 2048px 이하, PNG·JPEG)도 본다 |
| `imageDescription` | 그림을 VoiceOver 로 읽을 설명. `image` 가 있으면 필수 |
| `confirmTitle` | 확인 버튼 글. 없으면 앱 기본 "확인"(언어별) |
| `actionTitle` | 추가 버튼 글. `actionLink` 가 있으면 모든 언어 블록에 필수, 없으면 넣지 않는다 |

CI 는 앱보다 엄격하다: 앱은 잘못된 공지를 조용히 빼지만, CI 는 모르는 키(오타)도 오류로 잡는다.
