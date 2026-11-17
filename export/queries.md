# 예시 질의

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
PRE = "PREFIX s: <https://hogeony.github.io/SC26/schema#> PREFIX id: <https://hogeony.github.io/SC26/id/> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> "
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
