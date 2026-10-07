"""Prueba funcional: módulo Registro de Avances con 3 evidencias.

Ejecutar manualmente (requiere backend Docker):
    python tests/manual/test_registro_avances_3ev.py
"""

import struct
import zlib

import httpx


def make_png(color, w=80, h=80):
    def chunk(t, d):
        c = t + d
        return struct.pack(">I", len(d)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + bytes(color) * w for _ in range(h))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def make_pdf():
    from io import BytesIO

    from pypdf import PdfWriter

    w = PdfWriter()
    w.add_blank_page(width=612, height=792)
    buf = BytesIO()
    w.write(buf)
    return buf.getvalue()


def main() -> None:
    c = httpx.Client(base_url="http://backend:8000", timeout=30)

    # 1. Login
    r = c.post(
        "/api/v1/auth/login",
        json={
            "username": "enemova",
            "password": "EneldoGestor2026!",
            "municipio_codigo": "00000",
        },
    )
    assert r.status_code == 200, f"login fail {r.status_code}"
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    print("[1] Login OK - enemova")

    # 2. Producto asignado
    r = c.get("/api/v1/gestor/dashboard/mis-productos", headers=h)
    assert r.status_code == 200 and r.json()
    pid = r.json()[0]["id"]
    print(f"[2] Producto OK: {pid}")

    # 3. Crear avance
    r = c.post(
        f"/api/v1/gestor/dashboard/avances?producto_id={pid}",
        headers=h,
        json={
            "avance_porcentaje": 75.0,
            "avance_valor": 7500000,
            "observaciones": "Prueba funcional: registro con 3 evidencias multiples",
            "periodo": "Julio - Septiembre 2026",
            "estado_revision": "PENDIENTE",
        },
    )
    assert r.status_code == 201, f"create avance fail {r.status_code}: {r.text}"
    av = r.json()
    av_id = av["id"]
    print(f"[3] Avance creado: {av_id}")
    print(
        f"    porcentaje={av['avance_porcentaje']} valor={av['avance_valor']} estado={av['estado_revision']}"
    )

    # 4. Subir 3 evidencias en UNA sola petición
    files = [
        ("files", ("informe_avance.png", make_png((10, 43, 41)), "image/png")),
        ("files", ("fotos_obra.png", make_png((47, 111, 78)), "image/png")),
        ("files", ("acta_reunion.pdf", make_pdf(), "application/pdf")),
    ]
    data = {"descripcion": "Evidencias de la prueba funcional 3 archivos"}
    r = c.post(
        f"/api/v1/gestor/dashboard/avances/{av_id}/evidencias",
        headers=h,
        files=files,
        data=data,
    )
    assert r.status_code == 201, f"upload 3 fail {r.status_code}: {r.text}"
    evs = r.json()
    assert len(evs) == 3, f"expected 3 got {len(evs)}"
    print("[4] 3 evidencias subidas OK:")
    for e in evs:
        print(
            f"    - {e['nombre']} ({e['tipo']}, {e.get('tamano_almacenado', 0)} bytes) desc={e.get('descripcion')!r}"
        )

    # 5. Listar
    r = c.get(f"/api/v1/gestor/dashboard/avances/{av_id}/evidencias", headers=h)
    assert r.status_code == 200
    listed = r.json()
    assert len(listed) == 3
    print(f"[5] Listado OK: {len(listed)} evidencias")

    # 6. Descargar cada una
    for e in listed:
        r = c.get(f"/api/v1/gestor/dashboard/avances/{av_id}/evidencias/{e['id']}", headers=h)
        assert r.status_code == 200, f"download {e['nombre']} fail {r.status_code}"
        ct = r.headers.get("content-type", "")
        size = len(r.content)
        assert size > 0
        print(f"[6] Descarga OK: {e['nombre']} -> {ct} ({size} bytes)")

    # 7. Editar descripción
    ev1 = listed[0]["id"]
    r = c.put(
        f"/api/v1/gestor/dashboard/avances/{av_id}/evidencias/{ev1}",
        headers=h,
        json={"descripcion": "Editada: informe actualizado"},
    )
    assert r.status_code == 200
    assert r.json()["descripcion"] == "Editada: informe actualizado"
    print("[7] Editar descripcion OK")

    # 8. Verificar avance en historial del producto (endpoint devuelve lista por producto_id)
    r = c.get(f"/api/v1/gestor/dashboard/avances/{pid}", headers=h)
    assert r.status_code == 200
    avances = r.json()
    match = next((a for a in avances if a["id"] == av_id), None)
    assert match is not None, "avance no aparece en historial del producto"
    print(
        f"[8] Avance en historial: pct={match['avance_porcentaje']} "
        f"evidencia_nombre={match.get('evidencia_nombre')} "
        f"evidencia_tipo={match.get('evidencia_tipo')}"
    )

    # 9. Eliminar UNA evidencia
    ev_del = listed[1]["id"]
    r = c.delete(f"/api/v1/gestor/dashboard/avances/{av_id}/evidencias/{ev_del}", headers=h)
    assert r.status_code == 200 and r.json()["eliminada"] is True
    print("[9] Eliminar 1 evidencia OK")

    # 10. Quedan 2
    r = c.get(f"/api/v1/gestor/dashboard/avances/{av_id}/evidencias", headers=h)
    remaining = r.json()
    assert len(remaining) == 2
    print(f"[10] Quedan {len(remaining)} evidencias OK")

    # 11. Validaciones negativas
    r = c.post(
        f"/api/v1/gestor/dashboard/avances/{av_id}/evidencias",
        headers=h,
        files=[("files", ("malware.exe", b"MZ", "application/x-msdownload"))],
    )
    assert r.status_code == 422
    print("[11a] MIME invalido rechazado (422) OK")

    r = c.post(
        f"/api/v1/gestor/dashboard/avances/{av_id}/evidencias",
        headers=h,
        files=[("files", ("fake.png", b"not really a png at all", "image/png"))],
    )
    assert r.status_code == 422
    print("[11b] Firma PNG falsa rechazada (422) OK")

    r = c.get(
        f"/api/v1/gestor/dashboard/avances/{av_id}/evidencias/00000000-0000-0000-0000-000000000000",
        headers=h,
    )
    assert r.status_code == 404
    print("[11c] Evidencia inexistente 404 OK")

    r = c.get(f"/api/v1/gestor/dashboard/avances/{av_id}/evidencias")
    assert r.status_code == 401
    print("[11d] Sin token 401 OK")

    # 12. Historial final del producto (estado final)
    r = c.get(f"/api/v1/gestor/dashboard/avances/{pid}", headers=h)
    assert r.status_code == 200
    assert any(a["id"] == av_id for a in r.json())
    print("[12] Historial de avances del producto OK")

    print()
    print("=== TODAS LAS PRUEBAS DEL MODULO REGISTRO DE AVANCES CON 3 EVIDENCIAS: PASARON ===")
    print(f"Avance de prueba: {av_id}")


if __name__ == "__main__":
    main()
