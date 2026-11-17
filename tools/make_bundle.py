#!/usr/bin/env python3
"""YAML 원본에서 뷰어용 묶음 파일과 내보내기 파일을 만듦.

    pip install pyyaml
    python tools/make_bundle.py

만드는 파일
  data/bundle-core.json   첫 화면용 (스키마, 종합, 심층 요약, 세션, 용어, 갱신 이력)
  data/bundle-rest.json   이어서 읽는 부분 (기관, 인물, 개념, 발표)
  export/graph.jsonld  JSON-LD 그래프
  export/nodes.csv, export/edges.csv, export/insights.csv

YAML을 손으로 고친 뒤에는 이 스크립트를 다시 돌려야 뷰어에 반영됨.
돌릴 수 없으면 data/manifest.yaml 의 bundle 항목을 지우면 뷰어가 YAML을 직접 읽음.
"""
import csv, json, re, sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data"
BASE = "https://hogeony.github.io/SC26/"
load = lambda p: yaml.safe_load(p.read_text(encoding="utf-8")) or {}
dump = lambda p, o: p.write_text(json.dumps(o, ensure_ascii=False, separators=(",", ":"), default=str), encoding="utf-8")

man = load(D / "manifest.yaml")
schema = load(ROOT / "schema.yaml")
overview, themes = load(D / man["overview"]), load(D / man["themes"])
glossary = load(D / man["glossary"]) if man.get("glossary") else {}
changelog = load(D / man["changelog"]) if man.get("changelog") else []
sessions = [load(D / f) for f in man["sessions"]]
pres = [load(D / f) for f in man["presentations"]]
debates = (load(D / man["debates"]).get("debates") or []) if man.get("debates") else []
numx = load(D / man["numbers"]) if man.get("numbers") else {}
orgs, people, concepts = load(D / "orgs.yaml"), load(D / "people.yaml"), load(D / "concepts.yaml")

dump(D / "bundle-core.json", dict(schema=schema, overview=overview, themes=themes, sessions=sessions, glossary=glossary, changelog=changelog))
dump(D / "bundle-rest.json", dict(orgs=orgs, people=people, concepts=concepts, presentations=pres, debates=debates, numbers=numx))
if man.get("bundle") != {"core": "bundle-core.json", "rest": "bundle-rest.json"}:
    t = (D / "manifest.yaml").read_text(encoding="utf-8")
    t = re.sub(r"^bundle:.*\n(?:[ \t]+.*\n)*", "", t, flags=re.M)
    (D / "manifest.yaml").write_text("bundle: {core: bundle-core.json, rest: bundle-rest.json}\n" + t, encoding="utf-8")

# ---- 노드와 관계 ----
NUM = re.compile(r"\d[\d,.]*(?:~\d[\d,.]*)?\s?(?:%|배|건|개|초|분|주|시간|PB|TB/s|TB|GB/s|GB|Gbps|ms|µs|TFLOP/s|kHz|대|명)(?![A-Za-z])")
def evidence(p):
    cl = [c if isinstance(c, str) else c.get("text", "") for c in p.get("claims") or []]
    txt = " ".join(cl) + " " + (p.get("summary_ko") or "")
    if not cl and re.search(r"설명문이 없|읽지 못했|만 기록함", txt): return "none"
    return "num" if NUM.search(txt) else "qual"

nodes, edges = [], []
N = lambda i, t, label, **k: nodes.append(dict(id=i, type=t, label=label, **k))
E = lambda s, r, t: edges.append((s, r, t))
for i, name in orgs.items(): N(i, "Organization", name)
for i, p in people.items():
    N(i, "Person", p["name"])
    for o in p.get("orgs") or []: E(i, "affiliatedWith", o)
for t, items in concepts.items():
    for i, c in (items or {}).items():
        N(i, t, c["label"], label_ko=c.get("label_ko", ""), group=c.get("group", ""))
        for r in c.get("related") or []: E(i, "relatedTo", r)
for s in sessions:
    N(s["id"], "Session", s["label"], topic=s.get("topic", ""), date=str(s.get("date", "")), url=s.get("url", ""))
    for c in s.get("chairs") or []: E(s["id"], "chairedBy", c)
for p in pres:
    N(p["id"], "Presentation", p["label"], session=p["session"], evidence=evidence(p), url=p.get("url", ""))
    E(p["id"], "partOf", p["session"])
    for f, r in (("authors", "authoredBy"), ("addresses", "addresses"), ("proposes", "proposes"), ("targets", "targets")):
        for t in p.get(f) or []: E(p["id"], r, t)

ids = {n["id"]: n["type"] for n in nodes}
bad = []
for s, r, t in edges:
    rule = (schema.get("relations") or {}).get(r)
    if s not in ids or t not in ids: bad.append(f"{r}: 없는 노드 ({s} -> {t})")
    elif not rule or ids[s] not in rule["from"] or ids[t] not in rule["to"]: bad.append(f"{r}: {ids[s]}({s}) -> {ids[t]}({t}) 허용되지 않음")

X = ROOT / "export"; X.mkdir(exist_ok=True)
cols = ["id", "type", "label", "label_ko", "group", "session", "topic", "date", "evidence", "url"]
with open(X / "nodes.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f); w.writerow(cols); [w.writerow([n.get(c, "") for c in cols]) for n in nodes]
with open(X / "edges.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f); w.writerow(["source", "relation", "target"]); w.writerows(edges)

PERS = dict(decision="결정 주체와 기준", trial="시행착오와 조건", korea="한국 연구기관으로의 적용", extra="그 밖의 포인트")
rows = []
def ins(src, groups):
    for k, items in (groups or {}).items():
        for o in items or []:
            rows.append([src, PERS.get(k, k), o.get("head", ""), o.get("text", ""), " ".join(o.get("refs") or []), o.get("stage", ""), o.get("area", ""), o.get("needs", "")])
ins("전체 종합", overview.get("insights"))
for th in themes.get("themes") or []:
    for o in th.get("sections") or []:
        rows.append(["심층 요약: " + th["label"], "한국 연구기관으로의 적용" if o.get("head", "").startswith("한국 연구기관") else "심층 요약", o.get("head", ""), o.get("text", ""), " ".join(o.get("refs") or []), o.get("stage", ""), o.get("area", ""), o.get("needs", "")])
for s in sessions: ins(s["id"], s.get("insights"))
with open(X / "insights.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f); w.writerow(["source", "perspective", "head", "text", "refs", "stage", "area", "needs"]); w.writerows(rows)

# ---- 수치 모음과 에이전트용 자료 ----
NUMG = re.compile(NUM.pattern)
cl_ko = {i: (c.get("label_ko") or c["label"]) for items in concepts.values() for i, c in (items or {}).items()}
sess_by = {s["id"]: s for s in sessions}
with open(X / "numbers.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f); w.writerow(["what", "numbers", "condition", "claim", "targets", "addresses", "presentation_id", "presentation", "session", "url"])
    for p in pres:
        for k, c in enumerate(p.get("claims") or []):
            t = c if isinstance(c, str) else c.get("text", "")
            x = numx.get(f"{p['id']}#{k}") or {}
            m = [x.strip() for x in NUMG.findall(t)]
            if m and "수치가 없" not in t:
                w.writerow([x.get("what", ""), " / ".join(m), x.get("cond", ""), t, ", ".join(cl_ko.get(x, x) for x in p.get("targets") or []), ", ".join(cl_ko.get(x, x) for x in p.get("addresses") or []), p["id"], p["label"], p["session"], p.get("url", "")])
with open(X / "presentations.jsonl", "w", encoding="utf-8") as f:
    for p in pres:
        s_ = sess_by[p["session"]]
        rec = dict(id=p["id"], title=p["label"], kind=p.get("kind", ""), session_id=p["session"], session=s_["label"], topic=s_.get("topic", ""), date=str(s_.get("date", "")), url=p.get("url", ""),
                   authors=[dict(name=people[a]["name"], orgs=[orgs.get(o, o) for o in people[a].get("orgs") or []]) for a in p.get("authors") or [] if a in people],
                   problems=[cl_ko.get(x, x) for x in p.get("addresses") or []], methods=[cl_ko.get(x, x) for x in p.get("proposes") or []], systems=[cl_ko.get(x, x) for x in p.get("targets") or []],
                   concept_ids=(p.get("addresses") or []) + (p.get("proposes") or []) + (p.get("targets") or []),
                   summary_ko=p.get("summary_ko", ""), claims=[c if isinstance(c, str) else c.get("text", "") for c in p.get("claims") or []], evidence=evidence(p))
        f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
nC = sum(len(v or {}) for v in concepts.values())
(X / "AGENT.md").write_text(f"""# SC26 워크숍 지식그래프: 에이전트용 설명서

이 폴더는 SC26(2026년 11월, 시카고) 워크숍 {len(sessions)}개의 발표 {len(pres)}건을 정리한 지식그래프를 기계가 읽는 형식으로 담고 있음.
주소: {BASE}export/ (뷰어는 {BASE})

## 먼저 알아 둘 것

- 모든 요약과 주장은 **공개 프로그램 페이지의 초록을 한국어로 요약한 것**임. 논문 전문이나 현장 발표 내용이 아니며 원문 인용도 아님.
- `evidence` 값: `num`은 수치를 제시한 발표, `qual`은 수치 없이 설명한 발표, `none`은 공개 설명문이 없어 제목과 저자만 기록한 발표임. `none`인 발표를 근거로 단정하지 말 것.
- "한국 연구기관으로의 적용"(`perspective`가 그 값인 고찰)은 **발표 내용이 아니라 정리한 사람이 붙인 제안**임. 답변에서 발표자의 주장과 구분해서 전할 것.
- 문제·기법·대상 태그는 초록을 읽고 붙인 분류임. 초록에 없는 내용은 반영되지 않음.
- 수치를 인용할 때는 발표의 `url`(프로그램 페이지)을 함께 제시하고, 측정 조건은 원문에서 확인하라고 안내할 것.

## 파일

| 파일 | 내용 | 쓰임 |
|---|---|---|
| `presentations.jsonl` | 발표마다 한 줄. 제목, 세션, 저자와 소속, 문제·기법·대상(이름으로 풀어 씀), 요약, 주장, 근거 수준, 주소 | 검색 색인(RAG)에 그대로 넣기 좋음. 대부분의 질문은 이 파일로 답할 수 있음 |
| `insights.csv` | 고찰 {len(rows)}개. 출처(전체 종합, 심층 요약, 세션), 관점, 요지(`head`), 풀이(`text`), 근거 발표 id(`refs`, 공백 구분), 실행 단계, 영역, 선행 조건 | "무엇을 배울 수 있나", "우리 기관에 어떻게 적용하나" 같은 질문 |
| `numbers.csv` | 수치가 든 주장 문장을 무엇이(`what`), 얼마나(`numbers`), 어떤 조건에서(`condition`)로 나눈 표 | 정량 근거를 찾는 질문 |
| `debates.csv` | 같은 질문에 발표들이 다른 결과를 낸 쟁점. 입장별 요약과 근거 발표, 차이를 읽는 법 | "의견이 갈리는 곳은?" 같은 질문. 정리한 사람의 대비이며 발표자 간 반박이 아님 |
| `nodes.csv`, `edges.csv` | 노드 {len(nodes)}개와 관계 {len(edges)}개 | 표 계산, 그래프 분석 |
| `graph.jsonld` | 같은 그래프의 JSON-LD | RDF 저장소, SPARQL |
| `queries.md` | 예시 질의 | 아래 질문 유형의 구현 예 |

## 구조

노드 종류: Session(세션) {len(sessions)}, Presentation(발표) {len(pres)}, Person(인물) {len(people)}, Organization(기관) {len(orgs)}, Problem(다루는 문제)·Method(제안 기법)·System(대상 시스템) 합쳐 {nC}.

| 관계 | 방향 | 뜻 |
|---|---|---|
| `partOf` | 발표 → 세션 | 그 세션에서 발표됨 |
| `chairedBy` | 세션 → 인물 | 좌장 |
| `authoredBy` | 발표 → 인물 | 저자·발표자 |
| `affiliatedWith` | 인물 → 기관 | 소속 |
| `addresses` | 발표 → 문제 | 다루는 문제 |
| `proposes` | 발표 → 기법 | 제안하거나 쓰는 기법 |
| `targets` | 발표 → 대상 시스템 | 적용 대상 |
| `relatedTo` | 개념 ↔ 개념 | 관련 개념 |

id 규칙: 세션은 `sess126`, 발표는 프로그램의 id(`ws_...`, `misc...`), 개념과 인물과 기관은 영문 소문자와 붙임표. JSON-LD에서는 `{BASE}id/<id>`.
개념의 상위 범주: 문제·기법·대상 개념마다 `group`(nodes.csv)과 `skos:broader`(JSON-LD)로 상위 범주 하나가 붙어 있음. 범주는 종류별로 따로 있고 한 층뿐임. 이 자료는 형식 온톨로지가 아니라 가벼운 스키마와 분류 체계를 갖춘 지식그래프이며, 공리나 추론 규칙은 없음.
insights.csv의 `stage`: `now` 바로 할 수 있음, `prep` 준비 필요, `long` 장기 과제, `ref` 참고 사례.
세션의 `topic`: {", ".join(overview.get("topics") or [])}.

## 질문 유형별로 읽을 곳

| 질문 | 방법 |
|---|---|
| "X를 다룬 발표는?" | `presentations.jsonl`에서 `problems`, `methods`, `systems`, `summary_ko`, `claims`를 검색 |
| "X 문제에 어떤 기법이 쓰였나?" | `problems`에 X가 있는 발표들의 `methods`를 세기 (또는 edges.csv에서 addresses와 proposes를 발표 id로 잇기) |
| "X에 관한 정량 근거는?" | `numbers.csv`에서 `claim`, `targets`, `addresses`를 검색 |
| "이 주제의 주요 기관과 사람은?" | 해당 발표들의 `authors[].orgs`를 세기 |
| "A에게 닿으려면 누구를 거치나?" | 같은 발표의 저자끼리 이은 공저 그래프에서 최단 경로 |
| "우리 기관이 지금 할 수 있는 일은?" | `insights.csv`에서 `stage`가 `now`인 행. `needs`가 선행 조건 |
| "대회 전체의 흐름은?" | `insights.csv`에서 `source`가 "전체 종합"이거나 "심층 요약:"으로 시작하는 행 |

## 답변할 때

1. 발표 제목과 세션 번호, 프로그램 페이지 주소를 근거로 붙일 것.
2. 초록 요약에 근거한다는 점을 밝히고, `evidence`가 `none`인 발표는 "제목만 확인"이라고 알릴 것.
3. 적용 제안은 제안이라고 밝힐 것.
""", encoding="utf-8")
(X / "queries.md").write_text("""# 예시 질의

같은 질문을 파이썬(표준 라이브러리)과 SPARQL로 푸는 예임. SPARQL은 `graph.jsonld`를 RDF 저장소에 올리거나 rdflib로 읽어 실행함.
파이썬 예시는 실제 데이터로 돌려 확인했음. **SPARQL 예시는 실행 환경이 없어 돌려 보지 못했으므로** 처음 쓸 때 결과를 파이썬 예시와 대조해 볼 것.

## 준비

```python
import json, csv, collections
P = [json.loads(l) for l in open("export/presentations.jsonl", encoding="utf-8")]
I = list(csv.DictReader(open("export/insights.csv", encoding="utf-8-sig")))
N = list(csv.DictReader(open("export/numbers.csv", encoding="utf-8-sig")))
```

```python
from rdflib import Graph
g = Graph().parse("export/graph.jsonld", format="json-ld")
PRE = "PREFIX s: <""" + BASE + """schema#> PREFIX id: <""" + BASE + """id/> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> "
```

## 1. 어떤 개념을 다룬 발표 찾기

```python
hits = [p for p in P if "AI 에이전트" in p["systems"]]
for p in hits: print(p["session_id"], p["title"], p["url"])
```

```sparql
SELECT ?title ?sess WHERE { ?p s:targets id:ai-agents ; rdfs:label ?title ; s:partOf ?sess . }
```

## 2. 어떤 문제에 어떤 기법이 쓰였나

```python
c = collections.Counter(m for p in P if "에너지와 성능의 절충" in p["problems"] for m in p["methods"])
print(c.most_common(10))
```

```sparql
SELECT ?m (COUNT(?p) AS ?n) WHERE { ?p s:addresses id:energy-performance-tradeoff ; s:proposes ?method . ?method rdfs:label ?m . }
GROUP BY ?m ORDER BY DESC(?n)
```

## 3. 주제별 주요 기관

```python
c = collections.Counter(o for p in P if p["topic"] == "검증·신뢰" for o in {o for a in p["authors"] for o in a["orgs"]})
print(c.most_common(10))
```

```sparql
SELECT ?org (COUNT(DISTINCT ?p) AS ?n) WHERE { ?p s:partOf ?s ; s:authoredBy ?a . ?s s:topic "검증·신뢰" . ?a s:affiliatedWith ?o . ?o rdfs:label ?org . }
GROUP BY ?org ORDER BY DESC(?n) LIMIT 10
```

## 4. 정량 근거 찾기

```python
for r in N:
    if "전력" in r["claim"]: print(r["numbers"], "|", r["claim"], "|", r["url"])
```

## 5. 지금 시작할 수 있는 적용 제안과 선행 조건

```python
for r in I:
    if r["stage"] == "now": print(r["area"], "|", r["head"], "| 선행 조건:", r["needs"])
```

## 6. 고찰의 근거 발표 따라가기

```python
byid = {p["id"]: p for p in P}
r = next(r for r in I if r["source"] == "전체 종합")
print(r["head"]); [print(" -", byid[x]["title"], byid[x]["evidence"]) for x in r["refs"].split() if x in byid]
```

## 7. 두 사람 사이의 공저 경로

```python
co = collections.defaultdict(set)
for p in P:
    names = [a["name"] for a in p["authors"]]
    for a in names: co[a].update(n for n in names if n != a)
def path(a, b):
    prev, q = {a: None}, [a]
    while q:
        x = q.pop(0)
        if x == b:
            out = []
            while x: out.append(x); x = prev[x]
            return out[::-1]
        for y in co[x]:
            if y not in prev: prev[y] = x; q.append(y)
print(path("Kangryeol Kim", "Michael E. Papka"))
```

## 8. 수치를 제시한 발표만 고르기

```sparql
SELECT ?title WHERE { ?p a s:Presentation ; s:evidence "num" ; rdfs:label ?title . } LIMIT 20
```
""", encoding="utf-8")

with open(X / "debates.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f); w.writerow(["question", "side", "text", "refs", "how_to_read"])
    for d in debates:
        for sd in d.get("sides") or []: w.writerow([d["question"], sd.get("label", ""), sd.get("text", ""), " ".join(sd.get("refs") or []), d.get("read", "")])
rels = {}
for s, r, t in edges: rels.setdefault(s, {}).setdefault(r, []).append({"@id": "sc26:" + t})
ctx = {"@vocab": BASE + "schema#", "skos": "http://www.w3.org/2004/02/skos/core#", "broader": {"@id": "skos:broader", "@type": "@id"}, "sc26": BASE + "id/", "label": "http://www.w3.org/2000/01/rdf-schema#label", "url": {"@id": "http://schema.org/url", "@type": "@id"}}
graph = []
for n in nodes:
    g = {"@id": "sc26:" + n["id"], "@type": n["type"], "label": n["label"]}
    for k in ("label_ko", "topic", "date", "evidence", "url"):
        if n.get(k): g[k] = n[k]
    if n.get("group"): g["broader"] = "sc26:category/" + n["type"] + "/" + n["group"].replace(" ", "_")
    g.update(rels.get(n["id"], {}))
    graph.append(g)
for t, gs in (overview.get("concept_groups") or {}).items():
    for gname in gs: graph.append({"@id": "sc26:category/" + t + "/" + gname.replace(" ", "_"), "@type": "skos:Concept", "label": gname, "categoryOf": t})
(X / "graph.jsonld").write_text(json.dumps({"@context": ctx, "@graph": graph}, ensure_ascii=False, indent=1), encoding="utf-8")

print(f"세션 {len(sessions)} · 발표 {len(pres)} · 노드 {len(nodes)} · 관계 {len(edges)} · 고찰 {len(rows)}")
if bad:
    print("스키마 경고 %d건" % len(bad)); print("\n".join(bad))

# 검증 온톨로지도 함께 다시 만듦 (ontology/verification.yaml 이 있을 때)
if (ROOT / "ontology" / "verification.yaml").exists():
    import subprocess
    sys.exit(subprocess.call([sys.executable, str(ROOT / "tools" / "build_ontology.py")]))
