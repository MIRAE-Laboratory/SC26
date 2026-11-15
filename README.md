wlrma

# SC26 온톨로지

SC26 세션의 초록을 읽고 세션별 고찰을 도출한 저장소입니다. 발표·문제·기법·대상 시스템의 관계를 정리한 온톨로지가 고찰의 근거입니다.
데이터는 `data/`의 YAML이고, `index.html`이 이를 브라우저에서 직접 읽어 대화형 그래프로 보여 줍니다.

## 구조

| 경로                                        | 내용                                                                             |
| ------------------------------------------- | -------------------------------------------------------------------------------- |
| `index.html`                              | 뷰어. 브라우저에서 YAML을 직접 읽어 검증하고 그래프로 그립니다 (빌드 단계 없음). |
| `schema.yaml`                             | 클래스 7종과 관계 8종 정의. 위반 사항은 뷰어 상단에 경고로 표시됩니다.           |
| `data/manifest.yaml`                      | 뷰어가 읽을 세션·발표 파일 목록                                                 |
| `data/overview.yaml`                      | 세션 전체를 묶은 종합 고찰                                                       |
| `data/sessions/`, `data/presentations/` | 세션·발표당 파일 하나 (세션은 고찰, 발표는 요약과 핵심 주장 포함)               |
| `data/concepts.yaml`                      | 세션 간에 공유되는 Problem / Method / System 개념                                |
| `data/people.yaml`, `data/orgs.yaml`    | 인물과 소속 기관                                                                 |
| `media/`, `transcripts/`                | 현장 사진과 발표 녹취록 (세션별 하위 폴더)                                       |
| `vendor/`                                 | Cytoscape.js, js-yaml (외부 CDN 없이 동작)                                       |

## 사용법

GitHub에 올린 뒤 Settings → Pages → Source를 **Deploy from a branch**, `main` / `/ (root)`로 지정하면 끝입니다. YAML을 수정해 push하면 페이지에 바로 반영됩니다.

로컬에서는 파일을 직접 열면 브라우저가 YAML 읽기를 막으므로 간단한 서버로 엽니다.

```bash
python -m http.server 8000   # http://localhost:8000
```

세션을 추가하려면 `data/sessions/`와 `data/presentations/`에 파일을 넣고 `data/manifest.yaml`에 경로를 적습니다. 새 개념만 `data/concepts.yaml`에 더하고, 기존 개념 id를 재사용할수록 세션 간 연결이 드러납니다.

## 현장 자료 (사진·녹취록)

발표 YAML에 아래 필드를 더하면 뷰어 상세 패널에 표시됩니다. 모두 선택 사항입니다.

```yaml
photos:
  - {file: media/sess126/ws_shpc101-01.jpg, caption: 공격 트리 슬라이드}
transcript: transcripts/sess126/ws_shpc101.md
claims:
  - 문자열만 쓰면 출처 표시 없이 나옵니다.
  - {text: 발표에서만 언급된 내용, source: talk, at: "07:42"}   # source: abstract | talk | slide | qa
```

## 수록 세션

- `sess126` — S-HPC 2026: 5th International Workshop on Cyber Security in HPC (2026-11-15)
- `sess114` — AI4S: 8th Workshop on Artificial Intelligence and Machine Learning for Scientific Applications (2026-11-15)
- `sess120` — AgenticAI4HPC'26: The First International Workshop on Agentic AI for HPC (2026-11-15)

요약과 주장은 공개 프로그램 페이지의 초록을 한국어로 요약한 것이며 원문 인용이 아닙니다. 패널(`miscp115`)과 초청 강연 세 건(`misc226`, `misc217`, `misc187`)은 공개된 설명문이 없어 제목과 참여자만 담았습니다.

## 고찰

세션별 고찰은 각 세션 파일(`data/sessions/*.yaml`)의 `insights`에, 세션 전체 종합은 `data/overview.yaml`에 있습니다. 뷰어 왼쪽에 기본으로 표시되고, 세션을 고르면 그 세션의 고찰로 바뀝니다. 네 관점으로 정리합니다.

1. `decision` — 결정 주체와 기준: 누가, 무엇을 근거로 판단하는가
2. `trial` — 시행착오와 조건: 무엇이 안 됐고, 어떤 조건에서 됐는가
3. `korea` — 한국 연구기관으로의 적용: 초록을 바탕으로 한 제안이며 발표 내용이 아닙니다
4. `extra` — 그 밖의 포인트

```yaml
insights:
  decision:
    - head: 한 줄 요지.
      text: 근거가 되는 설명 한두 문장.
      refs: [ws_shpc101]        # 근거 발표 id. 뷰어에서 누르면 그래프의 해당 발표로 이동
```

뷰어 오른쪽 위의 버튼으로 글씨 크기(가−, 가+)와 밝은·어두운 테마를 바꿀 수 있고, 선택은 브라우저에 저장됩니다.
