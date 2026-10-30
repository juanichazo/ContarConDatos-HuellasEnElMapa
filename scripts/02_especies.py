"""Arma especies_amenazadas.csv a partir de la transcripción del Anexo I de la Res. MAyDS 316/2021.
Uso: python -I scripts/02_especies.py <anexoI_tsv> <out_csv>
"""
import sys, csv
src, out = sys.argv[1:3]
MAP = {"En peligro crítico": "CR", "En peligro": "EN", "Amenazada": "VU"}
MARINOS = {"Balaenoptera borealis", "Balaenoptera musculus", "Balaenoptera physalus", "Cephalorhynchus eutropia",
           "Tursiops truncatus", "Physeter macrocephalus", "Pontoporia blainvillei"}
FUENTE = "Res. MAyDS 316/2021, Anexo I (IF-2021-45350055-APN-DNBI#MAD) https://www.argentina.gob.ar/normativa/354496_res316-1_pdf/archivo"
rows = list(csv.DictReader(open(src, encoding="utf-8"), delimiter="\t"))
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["especie_id", "nombre_cientifico", "nombre_comun", "grupo", "categoria_nacional",
                "categoria_nacional_texto", "sistema_categoria", "ambito", "categoria_uicn_global",
                "fila_anexo", "fuente"])
    for i, r in enumerate(rows, 1):
        n = r["nombre_cientifico"].strip()
        w.writerow([f"MAM{i:03d}", n, r["nombre_vulgar"].strip(), "Mamíferos", MAP[r["categoria_nacional_666_97"]],
                    r["categoria_nacional_666_97"],
                    "Nacional: Categorización SAyDS-SAREM 2019 oficializada por Res. MAyDS 316/2021 (nomenclatura Decreto 666/97; 'Amenazada'=VU UICN según nota 1 del Anexo)",
                    "marino" if n in MARINOS else "terrestre/dulceacuícola", "", r["fila_anexo"], FUENTE])
print(len(rows), "especies")
