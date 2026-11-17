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
- 언어 블록은 앱 언어 → `en` → `ko` 순으로 고른다. 기기 언어를 앱이 지원하지 않으면 앱 언어가 영어라 `en` 을 본다. 그래서 `ko`·`en` 은 필수다.
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
      "actionLink": "catnap-pandagom://internal-url=https%3A%2F%2Fzopandagom.github.io%2Fcatnap-notice%2F",
      "localizations": {
        "ko": {
          "text": "겨울 장 20개가 새로 열렸어요!",
          "image": "https://zopandagom.github.io/catnap-notice/images/winter.png",
          "imageDescription": "눈 쌓인 창가에서 자는 고양이들",
          "confirmTitle": "좋아요",
          "actionTitle": "자세히 보기"
        },
        "en": {
          "text": "20 new winter chapters are here!",
          "image": "https://zopandagom.github.io/catnap-notice/images/winter.png",
          "imageDescription": "Cats sleeping by a snowy window",
          "actionTitle": "Learn more"
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
| `actionLink` | | 추가 버튼을 누르면 팝업을 닫고 여는 링크. 아래 "링크 규칙" |
| `localizations` | ✅ | 언어별 블록. 언어는 `ko`(필수) `en`(필수) `ja` `zh-Hans` `zh-Hant` `fr` `es` `de` `pt-BR` `it` |

## 링크 규칙 (`actionLink`)
| 링크 | 앱 동작 |
|---|---|
| `catnap-pandagom://internal-url=<퍼센트 인코딩한 https 주소>` | 디코딩한 주소를 앱 안 브라우저(Safari 화면)로 연다 |
| `https://…` | 앱 밖 Safari 에서 연다 |
| `itms-apps://…` | 앱 밖 App Store 에서 연다 |
| `mailto:…` | 앱 밖 메일 작성 화면을 연다 |
| 그 밖 (`http:`·`tel:`·`shortcuts:`·다른 앱 스킴, `internal-url=` 이 아닌 `catnap-pandagom://` 등) | 열지 않고 팝업만 닫는다. CI 가 막는다 |

- 앱 밖으로 여는 스킴을 셋으로 좁힌 것은 공지 파일이 외부 입력이라서다(사용자는 누르기 전에 어디로 가는지 모른다). 늘리려면 앱(냥자리 Core `LinkDestination`)과 이 검사를 함께 바꾼다.
- 인코딩은 주소 전체를 퍼센트 인코딩한다(인코딩하지 않은 문자가 섞이면 앱이 열지 않는다): `python3 -c "from urllib.parse import quote; print('catnap-pandagom://internal-url=' + quote('https://example.com/a?b=1', safe=''))"`
- 링크에 사용자·기기 식별자를 덧붙이지 않는다.

언어 블록:

| 키 | 설명 |
|---|---|
| `text` | 본문. `text`·`image` 중 하나는 있어야 한다 |
| `image` | https 그림 주소. 이 레포의 `images/` 에 두면 CI 가 크기(2MB 이하, 긴 변 2048px 이하, PNG·JPEG)도 본다 |
| `imageDescription` | 그림을 VoiceOver 로 읽을 설명. `image` 가 있으면 필수 |
| `confirmTitle` | 확인 버튼 글. 없으면 앱 기본 "확인"(언어별) |
| `actionTitle` | 추가 버튼 글. `actionLink` 가 있으면 모든 언어 블록에 필수, 없으면 넣지 않는다 |

CI 는 앱보다 엄격하다: 앱은 잘못된 공지를 조용히 빼지만, CI 는 모르는 키(오타)도 오류로 잡는다.

## 강제 업데이트 (`"type": "forceUpdate"`)
공지 항목에 `"type": "forceUpdate"` 를 두면 강제 업데이트 팝업이 된다(`type` 이 없으면 `"notice"`, 일반 공지).

```json
{
  "id": "force-build-12",
  "type": "forceUpdate",
  "forceUpdateBuildNumber": 12,
  "appStoreURL": "itms-apps://apps.apple.com/app/id1234567890",
  "localizations": {
    "ko": { "text": "새 버전이 나왔어요. 업데이트한 뒤 계속 즐겨 주세요.", "actionTitle": "업데이트" },
    "en": { "text": "A new version is out. Please update to keep playing.", "actionTitle": "Update" }
  }
}
```

| 키 | 필수 | 설명 |
|---|---|---|
| `forceUpdateBuildNumber` | ✅ | 앱 **빌드 번호**(`CFBundleVersion`)가 이보다 **낮으면** 팝업을 띄운다. 1 이상 정수, 따옴표 없이(`12`. `"12"`·`12.5` 는 틀림). 앱 버전(`1.2` 같은 마케팅 버전)은 보지 않는다 |
| `appStoreURL` | ✅ | 버튼을 누르면 앱 밖에서 여는 App Store 주소. `itms-apps://apps.apple.com/app/id<숫자>` 또는 `https://apps.apple.com/kr/app/id<숫자>`(`/kr/app/<이름>/id<숫자>` 도 된다). 쿼리·포트 없음 |
| `localizations` | ✅ | `ko`·`en` 필수. 블록에는 `text`(필수)·`actionTitle`(선택, 없으면 앱 기본 "업데이트")만 쓴다 |

`startsAt`·`endsAt`·`minAppVersion`·`maxAppVersion`·`actionLink`·`image`·`confirmTitle` 은 쓰지 않는다(CI 가 막는다). 강제 업데이트는 기간·앱 버전과 상관없이 앱 빌드 번호가 `forceUpdateBuildNumber` 보다 낮으면 **무조건** 뜬다. 냥자리는 빌드 번호를 버전이 바뀌어도 정수로 이어서 올린다(예: 1.0 은 빌드 1, 1.1 은 빌드 2).

앱 동작:
- 빌드 번호가 낮은 앱은 **매 실행** 닫을 수 없는 팝업을 띄운다(본 공지 기억과 무관). 버튼은 App Store 로 가고, 업데이트하지 않고 돌아오면 팝업이 그대로 있다.
- 강제 업데이트가 뜨는 앱에는 같은 파일의 일반 공지가 보이지 않는다. 첫 실행에도 뜬다(받기가 튜토리얼보다 먼저 끝나면 튜토리얼 대신, 늦으면 튜토리얼을 마친 뒤).
- 판을 푸는 중이면 판을 닫거나 깨고 목록으로 돌아올 때 뜬다. 구매 창·설정 같은 창이 떠 있으면 닫힐 때 뜬다.
- 앱을 새로 켤 때만 받으므로, 백그라운드에 있던 앱은 다음에 새로 켤 때 뜬다. 오프라인이면 뜨지 않는다.
- **풀려면 항목을 지운다**(다음 실행부터 풀린다. 날짜로 끝낼 수 없다). 형식이 틀린 항목은 앱이 조용히 뺀다(사용자가 갇히지 않게).

CI 가 막는 것:
- 강제 업데이트 항목은 하나만 둔다.
- `scripts/validate.py` 의 `RELEASED_BUILD_NUMBER`(App Store 에 나온 가장 높은 빌드 번호)가 설정되어 있으면 그보다 큰 `forceUpdateBuildNumber` 를 막는다. **App Store 에 새 빌드가 나오면 먼저 `RELEASED_BUILD_NUMBER` 를 올리고, 그다음에 강제 업데이트를 올린다.** App Store 조회(iTunes lookup)는 빌드 번호를 알려 주지 않아 손으로 적는다.
- `APP_STORE_ID` 가 설정되어 있으면 냥자리가 아닌 앱 ID 의 `appStoreURL` 을 막는다.
- 둘 다 비어 있으면(출시 전) 이 검사를 건너뛰고 형식만 본다(경고만 남긴다). 테스트용 강제 업데이트는 출시 전에 지운다. **출시하면 `APP_STORE_ID`·`RELEASED_BUILD_NUMBER` 를 꼭 넣는다.**
