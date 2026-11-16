#!/usr/bin/env python3
"""YAML 원본에서 뷰어용 묶음 파일과 내보내기 파일을 만듦.

    pip install pyyaml
    python tools/make_bundle.py

만드는 파일
  data/bundle-core.json   첫 화면용 (스키마, 종합, 심층 요약, 세션, 용어, 갱신 이력)
  data/bundle-rest.json   이어서 읽는 부분 (기관, 인물, 개념, 발표)
  export/ontology.jsonld  JSON-LD 그래프
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
orgs, people, concepts = load(D / "orgs.yaml"), load(D / "people.yaml"), load(D / "concepts.yaml")

dump(D / "bundle-core.json", dict(schema=schema, overview=overview, themes=themes, sessions=sessions, glossary=glossary, changelog=changelog))
dump(D / "bundle-rest.json", dict(orgs=orgs, people=people, concepts=concepts, presentations=pres))
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
        N(i, t, c["label"], label_ko=c.get("label_ko", ""))
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
cols = ["id", "type", "label", "label_ko", "session", "topic", "date", "evidence", "url"]
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

rels = {}
for s, r, t in edges: rels.setdefault(s, {}).setdefault(r, []).append({"@id": "sc26:" + t})
ctx = {"@vocab": BASE + "schema#", "sc26": BASE + "id/", "label": "http://www.w3.org/2000/01/rdf-schema#label", "url": {"@id": "http://schema.org/url", "@type": "@id"}}
graph = []
for n in nodes:
    g = {"@id": "sc26:" + n["id"], "@type": n["type"], "label": n["label"]}
    for k in ("label_ko", "topic", "date", "evidence", "url"):
        if n.get(k): g[k] = n[k]
    g.update(rels.get(n["id"], {}))
    graph.append(g)
(X / "ontology.jsonld").write_text(json.dumps({"@context": ctx, "@graph": graph}, ensure_ascii=False, indent=1), encoding="utf-8")

print(f"세션 {len(sessions)} · 발표 {len(pres)} · 노드 {len(nodes)} · 관계 {len(edges)} · 고찰 {len(rows)}")
if bad:
    print("스키마 경고 %d건" % len(bad)); print("\n".join(bad)); sys.exit(1)
