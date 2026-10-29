"""Arma tienda.html desde template.html + catalogo.json.

Para sincronizar con el inventario: exportar los documentos de la colección
"muebles" del artefacto de inventario a una carpeta (un JSON por mueble) y
pasar esa carpeta con --inventario. Las fotos (ids de assets) se incrustan
si están descargadas en --fotos/<id>.<ext>.
"""
import argparse, base64, glob, json, mimetypes, os

PUBLIC = ["tipo", "subtipo", "sku", "nombre", "material", "color", "origen",
          "ancho", "alto", "fondo", "stock", "aPedido", "precio", "precioAnterior", "ejemplo"]

def photo_uri(path, max_side=900):
    """Foto reducida a JPEG para que la página no pese de más."""
    try:
        from PIL import Image, ImageOps
        import io
        im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
        im.thumbnail((max_side, max_side))
        buf = io.BytesIO(); im.save(buf, "JPEG", quality=82, optimize=True)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        mt = mimetypes.guess_type(path)[0] or "image/jpeg"
        return f"data:{mt};base64," + base64.b64encode(open(path, "rb").read()).decode()

def from_inventory(folder, fotos_dir):
    out = []
    for f in sorted(glob.glob(os.path.join(folder, "**", "*.json"), recursive=True)):
        doc = json.load(open(f))
        d = doc.get("data", doc)
        item = {k: d.get(k) for k in PUBLIC if k in d}
        item["id"] = doc.get("id") or os.path.splitext(os.path.basename(f))[0]
        urls = []
        for fid in (d.get("fotos") or [])[:2]:
            hits = glob.glob(os.path.join(fotos_dir or "", f"{fid}.*")) if fotos_dir else []
            if hits:
                urls.append(photo_uri(hits[0]))
        if urls:
            item["fotosUrl"] = urls
        out.append(item)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventario")
    ap.add_argument("--fotos")
    ap.add_argument("--actualizado")
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    cat = json.load(open(os.path.join(here, "catalogo.json")))
    if a.inventario:
        cat["muebles"] = sorted(from_inventory(a.inventario, a.fotos), key=lambda x: (x.get("sku") or "~", x.get("nombre") or ""))
    if a.actualizado:
        cat["tienda"]["actualizado"] = a.actualizado
    data = json.dumps(cat, ensure_ascii=False).replace("</", "<\\/")
    logos = open(os.path.join(here, "logos.json")).read().replace("</", "<\\/")
    html = open(os.path.join(here, "template.html")).read()
    html = html.replace("__CATALOGO__", data).replace("__LOGOS__", logos)
    open(os.path.join(here, "tienda.html"), "w").write(html)
    print("tienda.html", len(html), "bytes,", len(cat["muebles"]), "muebles")

main()
