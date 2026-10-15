"""Simple 3D model of a line layout: OBJ (opens in Blender, FreeCAD, SketchUp, Windows 3D Viewer)
plus an HTML viewer you can rotate in a browser. Machines are boxes at their layout
positions; replace them with real models from a 3D library later (layout JSON keeps
the positions).
"""

from __future__ import annotations

import json
import re

from .tools import tool

PALETTE = ["#4e79a7", "#f28e2b", "#59a14f", "#e15759", "#76b7b2", "#edc948", "#b07aa1", "#9c755f"]


def _box(x, y, z, l, w, h):
    v = [(x, y, z), (x + l, y, z), (x + l, y + w, z), (x, y + w, z),
         (x, y, z + h), (x + l, y, z + h), (x + l, y + w, z + h), (x, y + w, z + h)]
    f = [(1, 2, 3, 4), (5, 8, 7, 6), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 8, 4), (4, 8, 5, 1)]
    return v, f


@tool
def layout_3d(title: str, machines: list[dict], room_length_mm: float = 0, room_width_mm: float = 0,
              default_height_mm: float = 1500) -> dict:
    """Export the layout as a 3D model (OBJ in metres) and an HTML 3D viewer (top/front/side by rotating).

    Args:
        title: model title
        machines: list of {"name", "x_mm", "y_mm", "length_mm", "width_mm", "height_mm" (opt)} - e.g. layout_line's "machines"
        room_length_mm: room length for the floor (0 = fit to machines)
        room_width_mm: room width for the floor (0 = fit)
        default_height_mm: height for machines without height_mm, default 1500
    """
    from .config import load
    if not machines:
        raise ValueError("machines is empty")
    stem = re.sub(r"[^\w\-]+", "_", title).strip("_") or "layout"
    out = load().output_dir
    L = room_length_mm or max(m["x_mm"] + m["length_mm"] for m in machines) + 1000
    W = room_width_mm or max(m["y_mm"] + m["width_mm"] for m in machines) + 1000
    lines = [f"# {title} - Improvise layout model, units: metres (Z up)"]
    offset = 0
    objs = [("floor", 0, 0, -10, L, W, 10)] + [
        (m["name"], m["x_mm"], m["y_mm"], 0, m["length_mm"], m["width_mm"], m.get("height_mm", default_height_mm))
        for m in machines]
    for name, x, y, z, l, w, h in objs:
        v, f = _box(x / 1000, y / 1000, z / 1000, l / 1000, w / 1000, h / 1000)
        oname = re.sub(r"\s+", "_", name)
        lines.append(f"o {oname}")
        lines += [f"v {a:.3f} {b:.3f} {c:.3f}" for a, b, c in v]
        lines += ["f " + " ".join(str(i + offset) for i in face) for face in f]
        offset += 8
    obj = out / f"{stem}.obj"
    obj.write_text("\n".join(lines) + "\n", encoding="utf-8")

    data = [{"name": m["name"], "x": m["x_mm"] / 1000, "y": m["y_mm"] / 1000, "l": m["length_mm"] / 1000,
             "w": m["width_mm"] / 1000, "h": m.get("height_mm", default_height_mm) / 1000,
             "c": PALETTE[i % len(PALETTE)]} for i, m in enumerate(machines)]
    page = """<!doctype html><html><head><meta charset="utf-8"><title>%TITLE%</title>
<style>body{margin:0;font-family:Arial}#t{position:absolute;top:8px;left:8px;background:#fff9;padding:6px 10px;border-radius:6px}
#b{position:absolute;top:8px;right:8px}button{margin-left:4px}</style></head><body>
<div id="t"><b>%TITLE%</b><br><span id="list"></span></div>
<div id="b"><button onclick="view('iso')">3D</button><button onclick="view('top')">Top</button><button onclick="view('front')">Front</button><button onclick="view('side')">Side</button></div>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}</script>
<script type="module">
import * as THREE from 'three'; import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
const M=%DATA%, L=%L%, W=%W%;
const scene=new THREE.Scene(); scene.background=new THREE.Color(0xf4f6f8);
const cam=new THREE.PerspectiveCamera(45,innerWidth/innerHeight,0.1,500); cam.up.set(0,0,1);
const r=new THREE.WebGLRenderer({antialias:true}); r.setSize(innerWidth,innerHeight); document.body.appendChild(r.domElement);
scene.add(new THREE.HemisphereLight(0xffffff,0x888888,1.2)); const d=new THREE.DirectionalLight(0xffffff,1); d.position.set(L,-W,20); scene.add(d);
const floor=new THREE.Mesh(new THREE.PlaneGeometry(L,W),new THREE.MeshStandardMaterial({color:0xdddddd})); floor.position.set(L/2,W/2,0); scene.add(floor);
scene.add(Object.assign(new THREE.GridHelper(Math.max(L,W),Math.ceil(Math.max(L,W))),{rotation:new THREE.Euler(Math.PI/2,0,0),position:new THREE.Vector3(L/2,W/2,0.001)}));
const list=[]; M.forEach((m,i)=>{const b=new THREE.Mesh(new THREE.BoxGeometry(m.l,m.w,m.h),new THREE.MeshStandardMaterial({color:m.c}));
b.position.set(m.x+m.l/2,m.y+m.w/2,m.h/2); scene.add(b); const e=new THREE.LineSegments(new THREE.EdgesGeometry(b.geometry),new THREE.LineBasicMaterial({color:0x222222})); e.position.copy(b.position); scene.add(e); list.push((i+1)+'. '+m.name);});
document.getElementById('list').innerHTML=list.join('<br>');
const c=new OrbitControls(cam,r.domElement); c.target.set(L/2,W/2,0);
window.view=v=>{const R=Math.max(L,W); if(v=='top')cam.position.set(L/2,W/2+0.01,R*1.4); else if(v=='front')cam.position.set(L/2,-R*1.2,2); else if(v=='side')cam.position.set(L+R*1.2,W/2,2); else cam.position.set(L*1.1,-W*0.9,R*0.8); c.update();};
view('iso'); (function a(){requestAnimationFrame(a); r.render(scene,cam);})();
addEventListener('resize',()=>{cam.aspect=innerWidth/innerHeight;cam.updateProjectionMatrix();r.setSize(innerWidth,innerHeight);});
</script></body></html>"""
    page = (page.replace("%TITLE%", title).replace("%DATA%", json.dumps(data))
            .replace("%L%", f"{L / 1000:.3f}").replace("%W%", f"{W / 1000:.3f}"))
    htm = out / f"{stem}_3d.html"
    htm.write_text(page, encoding="utf-8")
    return {"obj": str(obj), "viewer_html": str(htm), "machines": len(machines),
            "note": "Boxes at layout positions. Open the HTML in a browser (Top/Front/Side buttons) or the OBJ in Blender/FreeCAD."}
