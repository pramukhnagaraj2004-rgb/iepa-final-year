"""
IEPA dataset expansion (147 -> 500+).

Every sample is a real buggy program that is EXECUTED; the traceback you see in
error_raw / error_normalized is what Python actually printed, not hand-typed.

Run:  python build_dataset_v2.py
Out:  labeled_dataset_new.json   (new samples only, same schema as labeled_dataset.json
                                  + two extra fields: template_id, split)

Note: file names inside tracebacks are neutral (sample_0001.py). An earlier version named
files after the concept, which leaked the label; concept_mapper.py also scrubs paths.

Labeling rule used:
  off_by_one          -> loop / range / len() boundary slip that overruns by one
  array_out_of_bounds -> hardcoded or unchecked index (empty list, index 7 of 3 items, pop(9))
"""
import json, os, random, re, subprocess, sys, tempfile, uuid
from concurrent.futures import ThreadPoolExecutor

try:
    import resource
except ImportError:  # Windows has no 'resource'; memory-limit step is skipped there
    resource = None

SEED = 42
TIMEOUT = 2
WIN_DIR = r"C:\Users\Pramukh\Music\final_yr_project\data\synthetic\python"
OUT = "labeled_dataset_new.json"

# samples we want per concept in the final dataset (existing + new)
TARGET_PER_CONCEPT = 52
EXISTING = {
    "off_by_one": 17, "logical_operator_confusion": 16, "type_mismatch": 16,
    "wrong_return_type": 16, "missing_return": 15, "redundant_condition": 15,
    "uninitialized_variable": 15, "indentation_logic": 14, "infinite_loop": 14,
    "array_out_of_bounds": 9,
}

DOMAINS = [
    dict(L="scores",    item="score",    vals=[85, 90, 78, 92], low=20),
    dict(L="prices",    item="price",    vals=[12, 45, 30, 8],  low=5),
    dict(L="temps",     item="temp",     vals=[21, 25, 19, 30], low=10),
    dict(L="ages",      item="age",      vals=[18, 22, 35, 41], low=9),
    dict(L="orders",    item="order",    vals=[3, 7, 2, 9],     low=1),
    dict(L="marks",     item="mark",     vals=[66, 71, 88, 54], low=33),
    dict(L="distances", item="distance", vals=[5, 12, 8, 20],   low=2),
    dict(L="weights",   item="weight",   vals=[60, 72, 55, 80], low=15),
    dict(L="ratings",   item="rating",   vals=[4, 5, 3, 2],     low=1),
    dict(L="speeds",    item="speed",    vals=[40, 65, 80, 55], low=12),
]

def render(t, d):
    v = d["vals"]
    out = t
    for k, val in {
        "<L>": d["L"], "<item>": d["item"], "<vals>": repr(v), "<vals3>": repr(v[:3]),
        "<v0>": str(v[0]), "<v1>": str(v[1]), "<v2>": str(v[2]), "<low>": str(d["low"]),
    }.items():
        out = out.replace(k, val)
    return out.rstrip("\n") + "\n"

TEMPLATES = {}

TEMPLATES["off_by_one"] = [
("""def total_<L>(<L>):
    total = 0
    for i in range(len(<L>) + 1):
        total += <L>[i]
    return total

print(total_<L>(<vals>))
""", {"IndexError"}),
("""<L> = <vals>
i = 0
while i <= len(<L>):
    print(<L>[i])
    i += 1
""", {"IndexError"}),
("""<L> = <vals>
last_<item> = <L>[len(<L>)]
print(last_<item>)
""", {"IndexError"}),
("""def count_rises(<L>):
    rises = 0
    for i in range(len(<L>)):
        if <L>[i] < <L>[i + 1]:
            rises += 1
    return rises

print(count_rises(<vals>))
""", {"IndexError"}),
("""<L> = <vals>
for i in range(1, len(<L>) + 1):
    print("<item>", i, <L>[i])
""", {"IndexError"}),
("""<L> = <vals>
for i in range(len(<L>), -1, -1):
    print(<L>[i])
""", {"IndexError"}),
]

TEMPLATES["array_out_of_bounds"] = [
("""def get_<item>():
    <L> = <vals3>
    return <L>[7]

get_<item>()
""", {"IndexError"}),
("""def read_<item>(<L>, position):
    return <L>[position]

print(read_<item>(<vals3>, 10))
""", {"IndexError"}),
("""<L> = []
print("first <item>:", <L>[0])
""", {"IndexError"}),
("""grid = [<vals3>, <vals3>, <vals3>]
print(grid[3][0])
""", {"IndexError"}),
("""line = "<item>1,<item>2,<item>3"
parts = line.split(",")
print(parts[4])
""", {"IndexError"}),
("""<L> = <vals3>
removed = <L>.pop(9)
print(removed)
""", {"IndexError"}),
]

TEMPLATES["type_mismatch"] = [
("""<item> = <v0>
print("The <item> is " + <item>)
""", {"TypeError"}),
("""total = <v0> + "<v1>"
print(total)
""", {"TypeError"}),
("""<item>_count = <v0>
print(len(<item>_count))
""", {"TypeError"}),
("""print(sum(["<v0>", "<v1>", "<v2>"]))
""", {"TypeError"}),
("""limit = <v0>
user_<item> = "<v1>"
if user_<item> > limit:
    print("too high")
""", {"TypeError"}),
("""<L> = <vals>
print(<L> + <v0>)
""", {"TypeError"}),
]

TEMPLATES["wrong_return_type"] = [
("""def get_<item>():
    return "<v0>"

total = get_<item>() + <v1>
print(total)
""", {"TypeError"}),
("""def collect_<L>():
    return <vals>

print(collect_<L>() + 1)
""", {"TypeError"}),
("""def min_max(<L>):
    return (min(<L>), max(<L>))

spread = min_max(<vals>) / 2
print(spread)
""", {"TypeError"}),
("""def how_many_<item>s():
    return "<v0>"

for i in range(how_many_<item>s()):
    print(i)
""", {"TypeError"}),
("""def average(<L>):
    return sum(<L>) / len(<L>), len(<L>)

result = average(<vals>)
print(round(result))
""", {"TypeError"}),
("""def build_<item>():
    return {"value": <v0>}

print(build_<item>() * 2.5)
""", {"TypeError"}),
]

TEMPLATES["missing_return"] = [
("""def add_<item>(a, b):
    result = a + b

total = add_<item>(<v0>, <v1>) * 2
print(total)
""", {"TypeError"}),
("""def load_<L>():
    <L> = <vals>

load_<L>().append(<v0>)
""", {"AttributeError"}),
("""def make_<L>():
    data = <vals>
    data.sort()

for <item> in make_<L>():
    print(<item>)
""", {"TypeError"}),
("""def grade(<item>):
    if <item> >= 50:
        return "pass"

print(grade(<low>).upper())
""", {"AttributeError"}),
("""def clean_<L>(<L>):
    <L> = [x for x in <L> if x > 0]

print(len(clean_<L>(<vals>)))
""", {"TypeError"}),
("""def first_<item>(<L>):
    <L>[0]

print(first_<item>(<vals>)[0])
""", {"TypeError"}),
]

TEMPLATES["uninitialized_variable"] = [
("""print(<item>_total)
""", {"NameError"}),
("""<item>_count = 0

def bump():
    <item>_count += 1

bump()
""", {"UnboundLocalError"}),
("""def label_<item>(<item>):
    if <item> > 50:
        label = "high"
    return label

print(label_<item>(<low>))
""", {"UnboundLocalError"}),
("""<L> = <vals>
for <item> in <L>:
    total = total + <item>
print(total)
""", {"NameError"}),
("""def compute():
    result = <v0> * 2

compute()
print(result)
""", {"NameError"}),
("""def average(<L>):
    for x in <L>:
        running += x
    return running / len(<L>)

print(average(<vals>))
""", {"UnboundLocalError"}),
]

TEMPLATES["indentation_logic"] = [
("""def show_<L>(<L>):
print(<L>)

show_<L>(<vals>)
""", {"IndentationError"}),
("""<L> = <vals>
for <item> in <L>:
print(<item>)
""", {"IndentationError"}),
("""total = 0
    total += <v0>
print(total)
""", {"IndentationError"}),
("""def check(<item>):
    if <item> > <v0>:
        print("high")
      print("done")

check(<v1>)
""", {"IndentationError"}),
("""<item> = <v0>
if <item> > 10:
print("big")
else:
    print("small")
""", {"IndentationError"}),
("""def total_<L>(<L>):
    s = 0
\tfor x in <L>:
\t\ts += x
    return s

print(total_<L>(<vals>))
""", {"TabError", "IndentationError"}),
]

TEMPLATES["logical_operator_confusion"] = [
("""<item> = <v0>
if <item> > 5 && <item> < 100:
    print("ok")
""", {"SyntaxError"}),
("""<item> = <v0>
if <item> < 5 || <item> > 100:
    print("out of range")
""", {"SyntaxError"}),
("""<item>_ready = False
if !<item>_ready:
    print("wait")
""", {"SyntaxError"}),
("""<item> = <v0>
if <item> = <v1>:
    print("match")
""", {"SyntaxError"}),
("""name = "<item>"
age = <v0>
if name == "<item>" & age > 5:
    print("both")
""", {"TypeError"}),
("""<item> = <v0>
if <item> > 5 and < 100:
    print("ok")
""", {"SyntaxError"}),
]

TEMPLATES["infinite_loop"] = [
("""def total_<L>(n):
    return n + total_<L>(n - 1)

print(total_<L>(<v0>))
""", {"RecursionError"}),
("""attempts = 0
while attempts < <v0>:
    <item> = attempts * 2
""", {"TimeoutError"}),
("""i = 0
while i < len(<vals>):
    if i % 2 == 0:
        i += 1
""", {"TimeoutError"}),
("""def is_even_<item>(n):
    return is_odd_<item>(n - 1)

def is_odd_<item>(n):
    return is_even_<item>(n - 1)

is_even_<item>(<v0>)
""", {"RecursionError"}),
("""<L> = <vals>
for x in <L>:
    <L>.append(x)
""", {"TimeoutError", "MemoryError"}),
("""def retry_<item>(n):
    while True:
        n = n + 0
        if n > <v0>:
            break

retry_<item>(1)
""", {"TimeoutError"}),
]

TEMPLATES["redundant_condition"] = [
("""<item> = <v0>
if <item> is <v0> or <item> is <v0>:
    print("match")
""", {"SyntaxWarning"}),
("""def check_<item>(<item>):
    assert (<item> > 0, "<item> must be positive")
    return <item>

print(check_<item>(<v0>))
""", {"SyntaxWarning"}),
("""status = "<item>"
if status is "<item>" or status is "<item>":
    print("ok")
""", {"SyntaxWarning"}),
("""def is_valid(<item>):
    if <item> is 0 or <item> is 0:
        return False
    return True

print(is_valid(<v0>))
""", {"SyntaxWarning"}),
("""def verify_<item>(<item>):
    assert (<item> == <v0>, "mismatch")
    return True

print(verify_<item>(<v0>))
""", {"SyntaxWarning"}),
("""status = "<item>"
if status is not "<item>" and status is not "<item>":
    print("different")
""", {"SyntaxWarning"}),
]


def _limits():
    if resource:
        resource.setrlimit(resource.RLIMIT_AS, (400 * 1024 * 1024, 400 * 1024 * 1024))


def execute(code):
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "sample.py")
        with open(path, "w", newline="\n") as f:
            f.write(code)
        try:
            p = subprocess.run([sys.executable, path], capture_output=True, text=True,
                               timeout=TIMEOUT, preexec_fn=_limits if resource else None)
            return path, p.stderr, False
        except subprocess.TimeoutExpired:
            return path, "", True


def parse(stderr, path, timed_out, code, win_path):
    """Return (error_raw, normalized_dict) or None."""
    if timed_out:
        loop_line = next((i + 1 for i, l in enumerate(code.splitlines())
                          if l.strip().startswith(("while", "for"))), 1)
        msg = f"Execution exceeded {TIMEOUT} seconds (possible infinite loop)"
        raw = (f'Traceback (most recent call last):\n  File "{win_path}", line {loop_line}, in <module>\n'
               f"TimeoutError: {msg}\n")
        return raw, dict(line=loop_line, error_type="TimeoutError", message=msg,
                         raw_error=f"TimeoutError: {msg}")
    text = stderr.replace(path, win_path)
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        return None
    warn = re.match(r"^.*:(\d+): (\w*Warning): (.*)$", lines[0])
    if warn and not any(l.startswith("Traceback") for l in lines):
        ln, et, msg = int(warn.group(1)), warn.group(2), warn.group(3)
        return text, dict(line=ln, error_type=et, message=msg, raw_error=f"{et}: {msg}")
    last = lines[-1]
    m = re.match(r"^([A-Za-z_][\w.]*): ?(.*)$", last)
    if not m:
        return None
    et, msg = m.group(1), m.group(2)
    frames = re.findall(r'line (\d+)', text)
    ln = int(frames[-1]) if frames else 0
    return text, dict(line=ln, error_type=et, message=msg, raw_error=last)


def main():
    rng = random.Random(SEED)
    jobs = []  # (concept, template_idx, code, expected)
    for concept, tpls in TEMPLATES.items():
        need = max(0, TARGET_PER_CONCEPT - EXISTING[concept])
        pool = []
        for ti, (t, exp) in enumerate(tpls):
            doms = DOMAINS[:]
            rng.shuffle(doms)
            for d in doms:
                pool.append((ti, render(t, d), exp))
        # round-robin across templates so every template is represented
        by_t = {}
        for item in pool:
            by_t.setdefault(item[0], []).append(item)
        picked, seen = [], set()
        while len(picked) < need and any(by_t.values()):
            for ti in sorted(by_t):
                if by_t[ti] and len(picked) < need:
                    cand = by_t[ti].pop(0)
                    if cand[1] not in seen:
                        seen.add(cand[1])
                        picked.append(cand)
        jobs += [(concept,) + p for p in picked]

    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(lambda j: execute(j[2]), jobs))

    out, dropped, counters = [], [], {}
    for (concept, ti, code, expected), (path, stderr, timed_out) in zip(jobs, results):
        n = counters[concept] = counters.get(concept, 0) + 1
        win_path = f"{WIN_DIR}\\sample_{n:04d}.py"  # neutral name: a file name must never reveal the label
        parsed = parse(stderr, path, timed_out, code, win_path)
        if not parsed:
            dropped.append((concept, ti, "no error produced"))
            continue
        raw, norm = parsed
        if norm["error_type"] not in expected:
            dropped.append((concept, ti, f"got {norm['error_type']}, expected {sorted(expected)}"))
            continue
        norm.update(language="python", file=win_path, severity="error")
        ordered = {k: norm[k] for k in
                   ("language", "file", "line", "severity", "error_type", "message", "raw_error")}
        out.append({
            "id": str(uuid.uuid4()), "source": "synthetic_v2", "language": "python",
            "code": code, "error_raw": raw, "error_normalized": [ordered],
            "concept_label": concept, "confidence": "high",
            "template_id": f"{concept}:t{ti + 1}",
            # last template of every concept is held out for an honest, unseen-pattern test
            "split": "heldout" if ti == len(TEMPLATES[concept]) - 1 else "train",
        })

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"python {sys.version.split()[0]} | generated {len(out)} | dropped {len(dropped)}")
    for d in dropped:
        print("  DROPPED", d)
    by = {}
    for s in out:
        by.setdefault(s["concept_label"], []).append(s)
    for c, items in by.items():
        types = {}
        for s in items:
            et = s["error_normalized"][0]["error_type"]
            types[et] = types.get(et, 0) + 1
        held = sum(1 for s in items if s["split"] == "heldout")
        print(f"{c:28s} new={len(items):3d} total={len(items) + EXISTING[c]:3d} heldout={held:2d} {types}")


if __name__ == "__main__":
    main()
