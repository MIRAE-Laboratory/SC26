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
| `data/themes.yaml`                        | 여러 세션을 개념 묶음으로 가로지른 심층 요약                                     |
| `data/sessions/`, `data/presentations/` | 세션·발표당 파일 하나 (세션은 고찰, 발표는 요약과 핵심 주장 포함)               |
| `data/concepts.yaml`                      | 세션 간에 공유되는 Problem / Method / System 개념                                |
| `data/people.yaml`, `data/orgs.yaml`    | 인물과 소속 기관                                                                 |
| `media/`, `transcripts/`                | 현장 사진과 발표 녹취록 (세션별 하위 폴더)                                       |
| `tools/make_bundle.py` | YAML에서 묶음 파일(`data/bundle-*.json`)과 내보내기 파일(`export/`)을 만드는 스크립트 |
| `export/` | JSON-LD 그래프와 노드·관계·고찰 CSV |
| `vendor/`                                 | Cytoscape.js, js-yaml (외부 CDN 없이 동작)                                       |

## 사용법

GitHub에 올린 뒤 Settings → Pages → Source를 **Deploy from a branch**, `main` / `/ (root)`로 지정하면 끝입니다. YAML을 수정해 push하면 페이지에 바로 반영됩니다.

로컬에서는 파일을 직접 열면 브라우저가 YAML 읽기를 막으므로 간단한 서버로 엽니다.

```bash
python -m http.server 8000   # http://localhost:8000
```

뷰어는 `data/manifest.yaml`에 `bundle:` 항목이 있으면 YAML 수백 개 대신 묶음 파일 두 개만 읽어 첫 화면을 빨리 띄웁니다. **YAML을 손으로 고친 뒤에는 묶음을 다시 만들어야 화면에 반영됩니다.**

```bash
pip install pyyaml
python tools/make_bundle.py   # data/bundle-*.json 과 export/ 를 다시 만듦
```

스크립트를 돌릴 수 없으면 `data/manifest.yaml` 첫 줄의 `bundle:` 항목을 지우면 뷰어가 예전처럼 YAML을 직접 읽습니다.

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

- (126) 5th International Workshop on Cyber Security in High Performance Computing (S-HPC 2026) (2026-11-15)
- (114) AI4S: 8th Workshop on Artificial Intelligence and Machine Learning for Scientific Applications (2026-11-15)
- (120) AgenticAI4HPC'26: The First International Workshop on Agentic AI for HPC (2026-11-15)
- (125) EESP 2026: 3rd International Workshop on Energy Efficiency with Sustainable Performance (2026-11-15)
- (124) High Performance Python for Science at Scale (2026-11-15)
- (123) ISAV26: In Situ AI, Analysis and Visualization (2026-11-15)
- (117) XLOOP 2026: The 8th Annual Workshop on Extreme-Scale Experiment-in-the-Loop Computing (2026-11-15)
- (113) 21st Workshop on Workflows in Support of Large-Scale Science (WORKS26) (2026-11-15)
- (118) 15th International Workshop on Runtime and Operating Systems for Supercomputers (ROSS 2026) (2026-11-15)
- (111) 13th Annual International Workshop on Innovating the Network for Data Intensive Science (INDIS) (2026-11-15)
- (109) PMBS26: The 17th International Workshop on Performance Modeling, Benchmarking, and Simulation of High Performance Computer Systems (2026-11-15)
- (517) HUST-26: 13th International Workshop on HPC User Support Tools (2026-11-15)
- (110) 2026 International Workshop on Performance, Portability, and Productivity in HPC (P3HPC) (2026-11-15)
- (134) 10th International Workshop on Software Correctness for HPC Applications (Correctness '26) (2026-11-16)
- (142) FTXS: Workshop for Faults, Trustworthiness, and eXplainability for AI Systems at Scale (2026-11-16)
- (138) Sovereign AI Supercomputing Cloud Workshop (2026-11-16)
- (132) HPC Systems Professionals Workshop (HPCSYSPROS26) (2026-11-16)
- (129) PDSW'26: The 11th International Parallel Data Systems Workshop (2026-11-16)
- (141) AI on HPC: Performance Engineering, Challenges and Opportunities (2026-11-16)
- (147) High-Accuracy Computing on Low-Precision Hardware (2026-11-16)
- (128) 8th International Workshop on Containers and New Orchestration Paradigms for Isolated Environments in HPC (CANOPIE-HPC) (2026-11-16)
- (131) 8th Workshop on Programming and Performance Visualization Tools (ProTools) (2026-11-16)
- (112) The 2nd International Workshop for Software Frameworks and Workload Management on Quantum-HPC Ecosystems (2026-11-15)
- (148) Scale to See: Scalable AI for Scientific Imaging and Spatiotemporal Data (2026-11-20)
- (149) 4th Annual Trillion Parameter Workshop: Building Open AI Infrastructure, Models, and Agentic Systems for Science (2026-11-20)
- (153) Workshop on Operational Data Analytics in HPC (HPC-ODA) (2026-11-20)
- (155) Fourth International Workshop on HPC Testing and Evaluation of Systems, Tools, and Software (HPCTESTS 2026) (2026-11-20)
- (156) The 1st International Workshop on Edge-Cloud-HPC Operational Continuum (ECHO) (2026-11-20)
- (157) Sustainable Supercomputing (2026-11-20)

프로그램 페이지를 열지 못해 제목과 저자만 기록한 발표: `ws_hust101`, `ws_p3hpc125`, `ws_corr114`. 공개된 설명이 없는 초청 강연과 패널도 제목과 연사만 기록했습니다.

## 화면 구성

- 왼쪽 요약 칸: 핵심 수치 카드(`data/overview.yaml`의 `highlights`), 심층 요약 카드, 네 관점의 요지. 검색창은 고찰, 발표, 개념, 인물을 함께 찾고 관련 발표를 세션·시간순으로 이어 보여 줍니다.
- 오른쪽 탭: 세션–개념 지도, 문제–기법 대응, 세션 사이의 다리, 기관·저자, 온톨로지 그래프. 표는 모두 YAML에서 브라우저가 계산합니다.
- 첫 화면은 고찰에 필요한 파일만 먼저 읽어 그리고, 발표 파일과 그래프는 뒤이어 또는 탭을 열 때 읽습니다.
- 근거 수준: 고찰 항목과 근거 발표에 ● 수치 제시, ○ 수치 없이 설명, ◌ 제목만 확인 표시가 붙습니다(발표 요약에서 자동 판정).
- 적용 모아 보기: 한국 연구기관 적용 제안을 실행 단계(바로 / 준비 필요 / 장기 / 참고 사례) 또는 영역으로 묶습니다. 항목의 `stage: now|prep|long|ref`, `area:`, `needs:`(선행 조건)를 읽습니다.
- 세션 주제: 세션 파일의 `topic:`으로 세션 메뉴와 세션–개념 지도의 열을 묶습니다. 주제 순서는 `data/overview.yaml`의 `topics`, 한국 기관 표시는 `korea_orgs`에 적습니다.
- 자료 탭: 고찰 보고서(각주로 근거 발표 표시, 근거가 약한 항목 표시), 슬라이드(발표 모드와 가로 인쇄), 동향 요약(수렴한 것 / 갈리는 것 / 비어 있는 것), 열람 목록(전문을 읽을 발표 20편), 내보내기. 모두 온톨로지에서 브라우저가 만들어 내므로 데이터가 바뀌면 함께 바뀝니다.
- 기관·협력 후보: 심층 요약이나 세션 주제를 고르면 그 주제의 기관과 저자가 발표 수 순으로 나옵니다.
- 좁은 화면에서는 세션–개념 지도가 세션 하나의 개념 목록으로 바뀌고, 넓은 대응표는 숨깁니다.
- 용어 풀이는 `data/glossary.yaml`(용어: 한 줄 설명), 갱신 이력은 `data/changelog.yaml`에 적습니다.
- 주소(#s=세션&v=탭&n=노드&q=검색어)에 지금 화면이 담기므로 그대로 공유할 수 있습니다. "인쇄" 버튼은 지금 보이는 요약을 인쇄하거나 PDF로 저장합니다.
- 그래프는 전체 보기에서 세션과 여러 세션에 걸친 개념만 그리고, 세션을 누르면 발표가 펼쳐집니다. 데이터 점검 탭은 태그나 소속이 빈 곳을 보여 줍니다.

## 심층 요약

`data/themes.yaml`은 여러 세션을 가로지르는 관점별 심층 요약입니다. 뷰어의 세션 목록에서 "심층 요약 N"을 고르면 표시됩니다. 각 항목의 `concepts`에 개념 id를 적으면 그 개념과 연결된 발표가 자동으로 모여 그래프와 세션별 분포에 나타납니다.

```yaml
themes:
  - id: agents
    label: 관점 제목
    summary_ko: 두세 문장 요약
    concepts: [ai-agents, mcp-tools]      # concepts.yaml 의 id
    diagram: {type: layers, title: ..., items: [...]}
    sections:
      - {head: 요지 한 문장, text: 풀이, refs: [발표 id]}
```

요약과 주장은 공개 프로그램 페이지의 초록을 한국어로 요약한 것이며 원문 인용이 아닙니다. 패널(`miscp115`)과 초청·주제 강연 다섯 건(`misc226`, `misc217`, `misc187`, `misc173`, `misc198`)과 단편 발표 세 건(`misc179`, `misc180`, `misc181`)은 공개된 설명문이 없어 제목과 참여자만 담았습니다.

## 고찰

세션별 고찰은 각 세션 파일(`data/sessions/*.yaml`)의 `insights`에, 세션 전체 종합은 `data/overview.yaml`에 있습니다. 뷰어 왼쪽에 기본으로 표시되고, 세션을 고르면 그 세션의 고찰로 바뀝니다. 네 관점으로 정리합니다.

1. `decision` — 결정 주체와 기준: 누가, 무엇을 근거로 판단하는가
2. `trial` — 시행착오와 조건: 무엇이 안 됐고, 어떤 조건에서 됐는가
3. `korea` — 한국 연구기관으로의 적용: 초록을 바탕으로 한 제안이며 발표 내용이 아닙니다
4. `extra` — 그 밖의 포인트

세션 요약 아래에는 한눈에 보는 도식이 나옵니다. 세션 파일의 `diagram`에 정의하며, 종류는 전환(`shift`: 이전 → 지금), 흐름(`flow`: 단계의 연쇄), 계층(`layers`: 층별 정리) 세 가지입니다.

```yaml
diagram:
  type: shift            # shift | flow | layers
  title: 도식 제목
  items:
    - {from: 이전 상태, to: 바뀐 상태}        # flow, layers는 {label: 이름, note: 설명}
```

고찰과 요약의 문장은 "~함.", "~임."으로 끝나는 개조식으로 씁니다.

```yaml
insights:
  decision:
    - head: 한 줄 요지.
      text: 근거가 되는 설명 한두 문장.
      refs: [ws_shpc101]        # 근거 발표 id. 뷰어에서 누르면 그래프의 해당 발표로 이동
```

뷰어 왼쪽 패널 위의 버튼으로 글씨 크기(가−, 가+)와 밝은·어두운 테마를 바꿀 수 있습니다. 패널과 그래프 사이의 세로 칸막이는 끌어서 옮길 수 있고, 두 번 누르면 처음 너비로 돌아갑니다. 선택은 브라우저에 저장됩니다. 모바일에서는 고찰이 화면 전체에 나오고, 아래의 "온톨로지 펼치기" 버튼으로 그래프를 열고 닫습니다.
