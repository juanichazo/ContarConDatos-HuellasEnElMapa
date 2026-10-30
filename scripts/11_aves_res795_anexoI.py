"""Transcribe el Anexo I de la Res. MAyDS 795/2017 (categorización de aves) desde el PDF oficial a CSV.
Uso: python -I scripts/11_aves_res795_anexoI.py raw/res795_2017/res795-1.pdf raw/res795_2017/anexoI_aves_transcripcion.csv
Método: posiciones de palabras (pdfplumber). Columna de la "X" -> categoría, por la posición x del encabezado:
  ~278 En peligro de extinción | ~342 Amenazada | ~415 Vulnerable | ~489 No amenazada | ~562 Insuficientemente conocida
Cada X se asigna a la fila de nombre científico más cercana en vertical. Nombres partidos en dos líneas se unen.
"""
import re, sys, csv
import pdfplumber

pdf_path, out = sys.argv[1:3]
COLS = [(310, "En peligro de extinción", "EN"), (380, "Amenazada", "VU"), (450, "Vulnerable", "NT"),
        (525, "No amenazada", "LC"), (9999, "Insuficientemente conocida", "DD")]
col = lambda x: next((t, u) for lim, t, u in COLS if x < lim)
rows = []
for pi, p in enumerate(pdf_path and pdfplumber.open(pdf_path).pages, 1):
    ws = p.extract_words()
    left, mid, xs = [], [], []
    for w in ws:
        t = w["text"]
        if t == "X" and w["x0"] > 255:
            xs.append(w); continue
        if w["x0"] < 175:
            m = re.match(r"^([a-z\-]+)([A-ZÁÉÍÓÚÑ].*)$", t)  # p.ej. 'falculariusPicapalo'
            if m:
                left.append((w["top"], w["x0"], m.group(1)))
                mid.append((w["top"], 181, m.group(2)))
            else:
                left.append((w["top"], w["x0"], t))
        elif w["x0"] < 255:
            mid.append((w["top"], w["x0"], t))
    # agrupar por línea
    def lines(items):
        d = {}
        for top, x, t in items:
            k = next((kk for kk in d if abs(kk - top) < 2.5), top)
            d.setdefault(k, []).append((x, t))
        return [(k, " ".join(t for x, t in sorted(v))) for k, v in sorted(d.items())]
    L = lines(left)
    ents, i = [], 0
    while i < len(L):
        top, s = L[i]
        if s.startswith(("Orden ", "Fam. ")) or s in ("Nombre Científico",):
            i += 1; continue
        if re.match(r"^[A-Z][a-z]+$", s) and i + 1 < len(L) and re.match(r"^[a-z]", L[i + 1][1]) and L[i + 1][0] - top < 15:
            s = s + " " + L[i + 1][1]; top = (top + L[i + 1][0]) / 2; i += 1
        if re.match(r"^[A-Z][a-z]+ [a-z\-]+( [a-z\-]+)?$", s):
            ents.append({"top": top, "sci": s, "com": [], "x": []})
        i += 1
    if not ents:
        continue
    for top, s in lines(mid):
        e = min(ents, key=lambda e: abs(e["top"] - top))
        if abs(e["top"] - top) < 16 and s not in ("Nombre Vulgar",):
            e["com"].append(s)
    for w in xs:
        e = min(ents, key=lambda e: abs(e["top"] - w["top"]))
        e["x"].append(w["x0"])
    for e in ents:
        if not e["x"]:
            continue
        for x in e["x"]:
            t, u = col(x)
            rows.append([e["sci"], " ".join(e["com"]), t, u, pi, len(e["x"])])
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["nombre_cientifico", "nombre_comun", "categoria_res795", "equiv_uicn_decreto666", "pagina_pdf", "n_marcas_en_fila"])
    w.writerows(rows)
print(len(rows))
