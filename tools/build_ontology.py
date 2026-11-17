#!/usr/bin/env python3
"""ontology/verification.yaml 에서 OWL(Turtle), 도출 결과(JSON), 설명 문서를 만듦.

    python tools/build_ontology.py

규칙(도출)은 이 스크립트 안에 파이썬으로 구현되어 있음. OWL 추론기를 쓰지 않음.
"""
import json, sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
O = ROOT / "ontology"
d = yaml.safe_load((O / "verification.yaml").read_text(encoding="utf-8"))
T, F, M, A = d["targets"], d["failures"], d["methods"], d["assets"]
pres = {}
man = yaml.safe_load((ROOT / "data/manifest.yaml").read_text(encoding="utf-8"))
for f in man["presentations"]:
    p = yaml.safe_load((ROOT / "data" / f).read_text(encoding="utf-8")); pres[p["id"]] = p

def anc(tree, k):                       # 자신과 모든 상위 항목
    out = [k]
    while tree[k].get("parent"): k = tree[k]["parent"]; out.append(k)
    return out
leaf = lambda tree: [k for k in tree if not any(v.get("parent") == k for v in tree.values())]
L = lambda tree, k: tree[k]["label"]
applies = lambda m, t: any(a in (M[m].get("applies") or []) for a in anc(T, t))
cases, observed = d["cases"], d["observed"]

# ---- 제약 검사 ----
errors = []
for c in cases:
    if c["pres"] not in pres: errors.append(f"없는 발표: {c['pres']}")
    if c["outcome"] not in ("caught", "partial", "missed", "used"): errors.append(f"잘못된 결과 값: {c}")
    if not M[c["method"]].get("assurance"): errors.append(f"사례의 수단이 말단 수단이 아님: {c['method']}")
    elif not applies(c["method"], c["target"]): errors.append(f"수단의 적용 대상 밖: {L(M, c['method'])} → {L(T, c['target'])} ({c['pres']})")
    if c["target"] not in leaf(T) and c["target"] not in ("workflow", "data"): errors.append(f"사례의 대상이 말단이 아님: {c['target']}")
for k, m in M.items():
    if m.get("assurance") and m["assurance"] not in ("sample", "scope", "runtime", "judgment"): errors.append(f"잘못된 보증 수준: {k}")
    if m.get("assurance") == "scope" and not m.get("det"): errors.append(f"범위 보증인데 결정론적이지 않음: {k}")

# ---- 도출 ----
ref = lambda c: dict(pres=c["pres"], title=pres[c["pres"]]["label"], session=pres[c["pres"]]["session"], note=c.get("note", ""), outcome=c.get("outcome", "observed"), method=c.get("method"))
pairs = {}                              # (대상, 실패) → 사례들
for c in cases: pairs.setdefault((c["target"], c["failure"]), []).append(c)
for c in observed: pairs.setdefault((c["target"], c["failure"]), [])
obs = {}
for c in observed: obs.setdefault((c["target"], c["failure"]), []).append(c)
caught = lambda cs: sorted({c["method"] for c in cs if c["outcome"] == "caught"})
with_ = lambda cs, o: sorted({c["method"] for c in cs if c["outcome"] == o})

base = [k for k, m in M.items() if m.get("baseline")][0]
q1 = {}
for c in cases:
    if c["method"] == base and c["outcome"] == "missed":
        x = q1.setdefault(c["failure"], dict(failure=c["failure"], label=L(F, c["failure"]), targets=set(), refs=[], caught_by=set()))
        x["targets"].add(c["target"]); x["refs"].append(ref(c))
for f, x in q1.items():
    for c in cases:
        if c["failure"] == f and c["outcome"] == "caught": x["caught_by"].add(c["method"])
    x["targets"] = [L(T, t) for t in sorted(x["targets"])]; x["caught_by"] = [L(M, m) for m in sorted(x["caught_by"])]

q2 = []
for (t, f), cs in pairs.items():
    if caught(cs): continue
    kind = "수단 보고 없음" if not cs else "놓침만 보고됨" if all(c["outcome"] == "missed" for c in cs) else "일부만 잡음" if any(c["outcome"] == "partial" for c in cs) else "채택만 보고됨"
    q2.append(dict(target=t, failure=f, tl=L(T, t), fl=L(F, f), kind=kind, methods=[L(M, m) for m in sorted({c["method"] for c in cs})], refs=[ref(c) for c in cs] + [ref(c) for c in obs.get((t, f), [])]))
order = ["수단 보고 없음", "놓침만 보고됨", "채택만 보고됨", "일부만 잡음"]
q2.sort(key=lambda x: order.index(x["kind"]))

q3 = []
for f in leaf(F):
    ms = sorted({c["method"] for c in cases if c["failure"] == f and c["outcome"] == "caught"})
    if len(ms) == 1: q3.append(dict(failure=f, fl=L(F, f), method=L(M, ms[0]), refs=[ref(c) for c in cases if c["failure"] == f and c["outcome"] == "caught"]))

q4 = []
for (t, f), cs in pairs.items():
    for a in cs:
        if a["outcome"] in ("missed", "partial"):
            for b in cs:
                if b["outcome"] == "caught" and b["method"] != a["method"]:
                    q4.append(dict(tl=L(T, t), fl=L(F, f), weak=L(M, a["method"]), weak_outcome=a["outcome"], strong=L(M, b["method"]), refs=[ref(a), ref(b)]))

q5 = []
for a in A:
    ms = [m for m in M if a in (M[m].get("requires") or [])]
    cs = [c for c in cases if c["method"] in ms and c["outcome"] == "caught"]
    q5.append(dict(asset=a, label=L(A, a), methods=[L(M, m) for m in ms], used_methods=[L(M, m) for m in sorted({c["method"] for c in cs})], failures=[L(F, f) for f in sorted({c["failure"] for c in cs})], targets=[L(T, t) for t in sorted({c["target"] for c in cs})], n=len(cs)))
q5.sort(key=lambda x: (-len(x["failures"]), -len(x["methods"])))

q6, q7 = [], []
for (t, f), cs in pairs.items():
    eff = [c for c in cs if c["outcome"] in ("caught", "partial", "used")]
    if not eff: continue
    lv = {M[c["method"]]["assurance"] for c in eff}
    if lv <= {"sample", "judgment"}: q6.append(dict(tl=L(T, t), fl=L(F, f), methods=[L(M, m) for m in sorted({c["method"] for c in eff})], levels=sorted(lv), refs=[ref(c) for c in eff]))
    if all(not M[c["method"]].get("det") for c in eff): q7.append(dict(tl=L(T, t), fl=L(F, f), methods=[L(M, m) for m in sorted({c["method"] for c in eff})], refs=[ref(c) for c in eff]))

q8 = []
gap = {(x["target"], x["failure"]) for x in q2}
for (t2, f) in sorted(gap):
    for c in cases:
        if c["failure"] == f and c["outcome"] == "caught" and c["target"] != t2 and applies(c["method"], t2):
            tried = {x["method"] for x in pairs.get((t2, f), [])}
            if c["method"] in tried: continue
            q8.append(dict(to=L(T, t2), fl=L(F, f), method=L(M, c["method"]), frm=L(T, c["target"]), requires=[L(A, a) for a in M[c["method"]].get("requires") or []], refs=[ref(c)]))

# 대상 × 실패 표
tl, fl = [t for t in leaf(T) if any(k[0] == t for k in pairs)], [f for f in leaf(F) if any(k[1] == f for k in pairs)]
def cell(t, f):
    if (t, f) not in pairs: return None
    cs = pairs[(t, f)]
    st = "caught" if caught(cs) else "partial" if with_(cs, "partial") else "used" if with_(cs, "used") else "missed" if cs else "observed"
    return dict(status=st, refs=[ref(c) for c in cs] + [ref(c) for c in obs.get((t, f), [])])
matrix = dict(targets=[dict(id=t, label=L(T, t), parent=L(T, T[t]["parent"]) if T[t].get("parent") else "") for t in tl], failures=[dict(id=f, label=L(F, f), parent=L(F, F[f]["parent"])) for f in fl],
              cells={t + "|" + f: cell(t, f) for t in tl for f in fl if cell(t, f)})

# 수단 표
mt = []
for k in leaf(M):
    cs = [c for c in cases if c["method"] == k]
    mt.append(dict(id=k, label=L(M, k), parent=L(M, M[k]["parent"]), path=[L(M, x) for x in anc(M, k)][::-1], det=bool(M[k].get("det")), assurance=M[k]["assurance"], requires=[L(A, a) for a in M[k].get("requires") or []], applies=[L(T, a) for a in M[k].get("applies") or []], kg=M[k].get("kg") or [],
                   caught=len([c for c in cs if c["outcome"] == "caught"]), partial=len([c for c in cs if c["outcome"] == "partial"]), missed=len([c for c in cs if c["outcome"] == "missed"]), used=len([c for c in cs if c["outcome"] == "used"]), refs=[ref(c) for c in cs]))

res = dict(Q1=list(q1.values()), Q2=q2, Q3=q3, Q4=q4, Q5=q5, Q6=q6, Q7=q7, Q8=q8)
tree = lambda X: [dict(id=k, label=v["label"], parent=v.get("parent", "")) for k, v in X.items()]
out = dict(id=d["id"], label=d["label"], scope=d["scope"], questions=d["questions"], results=res, matrix=matrix, methods=mt, process=d["process"], findings=d.get("findings") or {}, errors=errors,
           trees=dict(targets=tree(T), failures=tree(F), methods=tree(M), assets=tree(A)),
           counts=dict(targets=len(T), failures=len(F), methods=len(M), assets=len(A), cases=len(cases), observed=len(observed), presentations=len({c["pres"] for c in cases + observed}), kg_concepts=len({x for m in M.values() for x in m.get("kg") or []})))
(O / "verification.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

# ---- OWL (Turtle) ----
BASE = "https://hogeony.github.io/SC26/"
q = lambda s: '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'
ttl = [f"@prefix : <{BASE}ontology/verification#> .", f"@prefix kg: <{BASE}id/> .", "@prefix owl: <http://www.w3.org/2002/07/owl#> .", "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .", "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .", "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .", "@prefix skos: <http://www.w3.org/2004/02/skos/core#> .", "",
       f"<{BASE}ontology/verification> rdf:type owl:Ontology ; rdfs:label {q(d['label'])}@ko ; rdfs:comment {q(d['scope'])}@ko .", ""]
for c, lab in (("Target", "검증 대상"), ("FailureMode", "실패 유형"), ("VerificationMethod", "검증 수단"), ("Asset", "전제 자산"), ("VerificationCase", "검증 사례"), ("Observation", "수단 없이 보고된 실패 관찰")):
    ttl.append(f":{c} rdf:type owl:Class ; rdfs:label {q(lab)}@ko .")
ttl.append("[] rdf:type owl:AllDisjointClasses ; owl:members ( :Target :FailureMode :VerificationMethod :Asset :VerificationCase :Observation ) .")
for p, dom, rng, lab in (("usesMethod", "VerificationCase", "VerificationMethod", "쓴 수단"), ("onTarget", None, "Target", "대상"), ("concernsFailure", None, "FailureMode", "실패 유형"), ("requires", "VerificationMethod", "Asset", "전제 자산"), ("appliesTo", "VerificationMethod", "Target", "적용 대상")):
    ttl.append(f":{p} rdf:type owl:ObjectProperty ; " + (f"rdfs:domain :{dom} ; " if dom else "") + f"rdfs:range :{rng} ; rdfs:label {q(lab)}@ko .")
ttl.append(":evidencedBy rdf:type owl:ObjectProperty ; rdfs:label \"근거 발표\"@ko .")
ttl.append(":outcome rdf:type owl:DatatypeProperty ; rdfs:range xsd:string ; rdfs:comment \"caught | partial | missed | used\" .")
ttl.append(":deterministic rdf:type owl:DatatypeProperty ; rdfs:domain :VerificationMethod ; rdfs:range xsd:boolean .")
ttl.append(":assuranceLevel rdf:type owl:DatatypeProperty ; rdfs:domain :VerificationMethod ; rdfs:range xsd:string ; rdfs:comment \"sample | scope | runtime | judgment\" .")
ttl.append(":VerificationCase rdfs:subClassOf [ rdf:type owl:Restriction ; owl:onProperty :usesMethod ; owl:cardinality \"1\"^^xsd:nonNegativeInteger ] , [ rdf:type owl:Restriction ; owl:onProperty :onTarget ; owl:cardinality \"1\"^^xsd:nonNegativeInteger ] , [ rdf:type owl:Restriction ; owl:onProperty :concernsFailure ; owl:cardinality \"1\"^^xsd:nonNegativeInteger ] .")
ttl.append("")
# 종류는 개체로 두고 위계는 skos:broader 로 적음 (사례가 종류를 직접 가리키게 하기 위함)
for X, cls, pre in ((T, "Target", "t-"), (F, "FailureMode", "f-"), (A, "Asset", "a-"), (M, "VerificationMethod", "m-")):
    for k, v in X.items():
        s = f":{pre}{k} rdf:type :{cls} ; rdfs:label {q(v['label'])}@ko"
        if v.get("parent"): s += f" ; skos:broader :{pre}{v['parent']}"
        if cls == "VerificationMethod" and v.get("assurance"):
            s += f" ; :deterministic {'true' if v.get('det') else 'false'} ; :assuranceLevel {q(v['assurance'])}"
            if v.get("requires"): s += " ; :requires " + " , ".join(":a-" + a for a in v["requires"])
            if v.get("applies"): s += " ; :appliesTo " + " , ".join(":t-" + a for a in v["applies"])
            if v.get("kg"): s += " ; skos:closeMatch " + " , ".join("kg:" + a for a in v["kg"])
        ttl.append(s + " .")
    ttl.append("")
for i, c in enumerate(cases, 1):
    ttl.append(f":case-{i:02d} rdf:type :VerificationCase ; :usesMethod :m-{c['method']} ; :onTarget :t-{c['target']} ; :concernsFailure :f-{c['failure']} ; :outcome {q(c['outcome'])} ; :evidencedBy kg:{c['pres']} ; rdfs:comment {q(c.get('note', ''))}@ko .")
for i, c in enumerate(observed, 1):
    ttl.append(f":obs-{i:02d} rdf:type :Observation ; :onTarget :t-{c['target']} ; :concernsFailure :f-{c['failure']} ; :evidencedBy kg:{c['pres']} ; rdfs:comment {q(c.get('note', ''))}@ko .")
(O / "verification.ttl").write_text("\n".join(ttl) + "\n", encoding="utf-8")

# ---- 설명 문서 ----
R = res
md = [f"# {d['label']}", "", f"SC26 지식그래프(`data/`)에서 \"검증\"에 해당하는 부분을 추려 따로 구성한 온톨로지임. {d['scope']}", "",
      "큐레이션된 지식그래프를 먼저 만들고, 그 안에서 쓸모 있는 것만 골라 온톨로지로 올리는 접근을 시험한 기록이기도 함.", "",
      "## 파일", "",
      "| 파일 | 내용 |", "|---|---|",
      "| `verification.yaml` | 원본. 역량 질문, 대상·실패 유형·수단·자산의 정의와 위계, 검증 사례, 구성 과정 기록 |",
      "| `verification.ttl` | 같은 내용의 OWL(Turtle). `tools/build_ontology.py`가 만듦 |",
      "| `verification.json` | 규칙을 적용한 도출 결과. 뷰어의 \"검증 온톨로지\" 화면이 읽음 |", "",
      "## 방법", "",
      "1. 역량 질문 여덟 개를 먼저 정함(아래).",
      "2. 지식그래프에서 검증 범주의 문제·기법 개념과 연결된 발표 97건을 읽고, 수단이 실패를 잡았는지 놓쳤는지를 보고한 발표를 사례로 고름.",
      f"3. 클래스 넷을 정의함: 검증 대상 {len(T)}, 실패 유형 {len(F)}, 검증 수단 {len(M)}, 전제 자산 {len(A)}. 수단에는 결정론 여부, 보증 수준, 전제 자산, 적용 대상을 붙임.",
      f"4. 발표를 검증 사례 {len(cases)}건(수단, 대상, 실패, 결과)과 관찰 {len(observed)}건(수단 없이 보고된 실패)으로 다시 적음. 근거 발표는 {out['counts']['presentations']}건임.",
      "5. 제약을 검사함: 사례의 수단은 그 대상에 적용 가능해야 하고, 범위 보증 수단은 결정론적이어야 함.",
      "6. 규칙 여덟 개를 적용해 질문에 답함.", "",
      "## 구조", "",
      "- `VerificationCase` —usesMethod→ `VerificationMethod`, —onTarget→ `Target`, —concernsFailure→ `FailureMode`, outcome(caught, partial, missed, used), —evidencedBy→ 지식그래프의 발표",
      "- `VerificationMethod` —requires→ `Asset`, —appliesTo→ `Target`, deterministic, assuranceLevel(sample, scope, runtime, judgment), skos:closeMatch → 지식그래프의 개념",
      "- 위계는 skos:broader. 수단과 대상의 적용 범위는 상위 항목에서 하위 항목으로 물려받음.", "",
      "## 역량 질문과 답", ""]
ans = {"Q1": f"실패 유형 {len(R['Q1'])}가지: " + ", ".join(x["label"] for x in R["Q1"]),
       "Q2": f"{len(R['Q2'])}개 조합: " + "; ".join(f"{x['tl']} × {x['fl']} ({x['kind']})" for x in R["Q2"]),
       "Q3": f"{len(R['Q3'])}개: " + "; ".join(f"{x['fl']} ← {x['method']}" for x in R["Q3"]),
       "Q4": f"보완 관계 {len(R['Q4'])}쌍. 예: " + "; ".join(f"{x['weak']} → {x['strong']} ({x['tl']} × {x['fl']})" for x in R["Q4"][:4]),
       "Q5": "; ".join(f"{x['label']}: 실패 유형 {len(x['failures'])}종" for x in R["Q5"][:5]),
       "Q6": f"{len(R['Q6'])}개 조합: " + "; ".join(f"{x['tl']} × {x['fl']}" for x in R["Q6"]),
       "Q7": f"{len(R['Q7'])}개 조합: " + "; ".join(f"{x['tl']} × {x['fl']}" for x in R["Q7"]),
       "Q8": f"{len(R['Q8'])}개: " + "; ".join(f"{x['to']}의 {x['fl']} ← {x['method']} ({x['frm']}에서 잡음)" for x in R["Q8"])}
for qn in d["questions"]: md += [f"**{qn['id']}. {qn['text']}**", "", ans[qn["id"]], ""]
fd = d.get("findings") or {}
md += ["## 결과의 평가", "", "### 새로 나온 것", ""] + [f"- {x}" for x in fd.get("new", [])] + ["", "### 이미 고찰에 있던 것", ""] + [f"- {x}" for x in fd.get("known", [])] + ["", "### 한계", ""] + [f"- {x}" for x in fd.get("limits", [])]
pr = d["process"]
md += ["", "## 지식그래프에서 온톨로지로: 구성 과정의 기록", "", f"**올린 것.** {pr['promoted']}", "", "**나눈 것.**", ""] + [f"- {x}" for x in pr["split"]] + ["", "**새로 만든 것.**", ""] + [f"- {x}" for x in pr["added"]] + ["", f"**올리지 않은 것.** {pr['dropped']}", "", "**지식그래프의 맹점과 순서의 효과.**", ""] + [f"- {x}" for x in pr["blind_spots"]]
md += ["", "## 다시 만들기", "", "```bash", "pip install pyyaml", "python tools/build_ontology.py", "```", "", "`verification.yaml`을 고친 뒤 다시 돌리면 OWL 파일과 도출 결과가 갱신됨. 제약 위반이 있으면 목록을 내고 멈춤."]
(O / "README.md").write_text("\n".join(md) + "\n", encoding="utf-8")

print(f"온톨로지: 대상 {len(T)} · 실패 유형 {len(F)} · 수단 {len(M)} · 자산 {len(A)} · 사례 {len(cases)} · 관찰 {len(observed)} · 근거 발표 {out['counts']['presentations']}")
print("도출: " + " · ".join(f"{k} {len(v)}" for k, v in res.items()))
if errors:
    print("제약 위반 %d건" % len(errors)); print("\n".join(errors)); sys.exit(1)
