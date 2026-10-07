"""
Génère la page web de la liste de courses Almanax (checklist + bouton copier).
Les cases cochées sont mémorisées dans le navigateur (localStorage), par période.
"""

import json

TEMPLATE = r"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITRE__</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Alegreya+SC:wght@700&family=Alegreya+Sans:wght@400;500;700&display=swap" rel="stylesheet">
<style>
/* Liste de courses en une colonne : en-tête + progression collante, puis une ligne par objet */
:root {
  --bg: #eef1ef; --surface: #ffffff; --fg: #1d2a2a; --muted: #5d6e6c;
  --line: #d3dbd8; --accent: #b8860b; --accent-ink: #ffffff; --done: #2f7d5b;
  --done-bg: #e3f1ea;
  --display: "Alegreya SC", Georgia, serif;
  --body: "Alegreya Sans", system-ui, sans-serif;
  color-scheme: light;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #131b1b; --surface: #1b2626; --fg: #e5ecea; --muted: #93a5a2;
    --line: #2c3a3a; --accent: #e0aa3e; --accent-ink: #1a1405; --done: #6cc79c;
    --done-bg: #1d3329; color-scheme: dark;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--fg); font: 17px/1.45 var(--body); }
.wrap { max-width: 760px; margin: 0 auto; padding-inline: 16px; padding-block: 24px 64px; }
header h1 { font: 700 clamp(26px, 5vw, 34px)/1.1 var(--display); margin: 0 0 6px; text-wrap: balance; }
.meta { color: var(--muted); margin: 0; }
.bar { position: sticky; top: 0; z-index: 2; background: var(--bg); padding-block: 14px; margin-top: 12px;
       display: flex; flex-wrap: wrap; gap: 10px 16px; align-items: center; border-bottom: 1px solid var(--line); }
.progress { flex: 1 1 220px; display: flex; align-items: center; gap: 12px; font-variant-numeric: tabular-nums; }
.track { flex: 1; height: 8px; border-radius: 4px; background: var(--line); overflow: hidden; }
.fill { height: 100%; width: 0; background: var(--done); transition: width .25s; }
.controls { display: flex; flex-wrap: wrap; gap: 8px; }
.seg { display: inline-flex; border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
.seg button, .btn { font: 500 15px var(--body); border: 0; background: var(--surface); color: var(--fg);
       padding: 6px 12px; cursor: pointer; }
.seg button[aria-pressed="true"] { background: var(--accent); color: var(--accent-ink); }
.btn { border: 1px solid var(--line); border-radius: 8px; }
button:focus-visible, input:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.legend { color: var(--muted); font-size: 15px; margin: 14px 0 6px; }
ul { list-style: none; margin: 0; padding: 0; }
.item { display: grid; grid-template-columns: 40px minmax(0, 1fr) auto auto; align-items: center; gap: 12px;
        padding: 10px 12px; border-bottom: 1px solid var(--line); background: var(--surface); }
.item:first-child { border-top-left-radius: 10px; border-top-right-radius: 10px; }
.item:last-child { border-bottom: 0; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px; }
.actions { display: flex; align-items: center; gap: 10px; }
.item input { width: 26px; height: 26px; margin: 0; accent-color: var(--done); cursor: pointer; }
.item img { width: 40px; height: 40px; object-fit: contain; }
.name { min-width: 0; }
.name label { font-weight: 700; cursor: pointer; overflow-wrap: anywhere; }
.name small { display: block; color: var(--muted); font-size: 14px; }
.qty { font-variant-numeric: tabular-nums; font-weight: 700; font-size: 20px; text-align: right; white-space: nowrap; }
.qty small { display: block; font-weight: 400; font-size: 12px; color: var(--muted); letter-spacing: .04em; text-transform: uppercase; }
.copy { font: 500 14px var(--body); border: 1px solid var(--line); background: var(--bg); color: var(--fg);
        border-radius: 8px; padding: 6px 10px; cursor: pointer; white-space: nowrap; }
.copy.ok { background: var(--done-bg); color: var(--done); border-color: var(--done); }
.item.done { background: var(--done-bg); }
.item.done .name label, .item.done .qty { text-decoration: line-through; color: var(--muted); }
.hide-done .item.done, .hide-done tr.done { display: none; }
h2 { font: 700 22px var(--display); margin: 36px 0 10px; }
.days { width: 100%; border-collapse: collapse; background: var(--surface); border-radius: 10px; overflow: hidden; }
.days td { padding: 8px 12px; border-bottom: 1px solid var(--line); }
.days td:first-child { color: var(--muted); font-variant-numeric: tabular-nums; white-space: nowrap; width: 1%; }
.days tr.done td:last-child { text-decoration: line-through; color: var(--muted); }
.empty { color: var(--muted); padding: 16px 0; }
@media (max-width: 520px) {
  .item { grid-template-columns: 32px minmax(0, 1fr) auto; }
  .item img { width: 32px; height: 32px; }
  .actions { grid-column: 2 / 4; justify-self: end; }
}
@media (prefers-reduced-motion: reduce) { .fill { transition: none; } }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1 id="titre"></h1>
    <p class="meta" id="meta"></p>
  </header>

  <div class="bar">
    <div class="progress">
      <span id="compteur">0 / 0</span>
      <div class="track"><div class="fill" id="fill"></div></div>
    </div>
    <div class="controls">
      <div class="seg" role="group" aria-label="Nombre de personnages" id="persos"></div>
      <button class="btn" id="masquer" aria-pressed="true">Masquer achetés</button>
      <button class="btn" id="reset">Tout décocher</button>
    </div>
  </div>

  <p class="legend" id="legende"></p>
  <ul id="liste"></ul>

  <h2>Détail par jour</h2>
  <table class="days"><tbody id="jours"></tbody></table>
</div>

<script id="data" type="application/json">__DATA__</script>
<script>
const D = JSON.parse(document.getElementById("data").textContent);
const CLE = "almanax:" + D.debut + "_" + D.fin;
const LOGOS = D.logos;

function lire() { try { return JSON.parse(localStorage.getItem(CLE)) || {}; } catch (e) { return {}; } }
function ecrire(s) { try { localStorage.setItem(CLE, JSON.stringify(s)); } catch (e) {} }

let etat = Object.assign({ coches: {}, persos: D.persos[D.persos.length - 1], masquer: true }, lire());
if (!D.persos.includes(etat.persos)) etat.persos = D.persos[D.persos.length - 1];

document.getElementById("titre").textContent = D.titre;
document.title = D.titre;
document.getElementById("meta").textContent =
  D.items.length + " objets sur " + D.jours.length + " jours · " +
  D.kamas.toLocaleString("fr-FR") + " kamas gagnés par perso";
document.getElementById("legende").textContent =
  Object.values(LOGOS).map(l => l[0] + " " + l[1]).join("   ·   ");

const persos = document.getElementById("persos");
D.persos.forEach(n => {
  const b = document.createElement("button");
  b.textContent = n + " perso" + (n > 1 ? "s" : "");
  b.dataset.n = n;
  b.addEventListener("click", () => { etat.persos = n; ecrire(etat); rendre(); });
  persos.appendChild(b);
});

const masquer = document.getElementById("masquer");
masquer.addEventListener("click", () => { etat.masquer = !etat.masquer; ecrire(etat); rendre(); });
document.getElementById("reset").addEventListener("click", e => {
  const b = e.currentTarget;
  if (b.dataset.confirm !== "1") {
    b.dataset.confirm = "1"; b.textContent = "Confirmer ?";
    setTimeout(() => { b.dataset.confirm = ""; b.textContent = "Tout décocher"; }, 3000);
    return;
  }
  etat.coches = {}; ecrire(etat); b.dataset.confirm = ""; b.textContent = "Tout décocher"; rendre();
});

async function copier(nom, bouton) {
  try {
    await navigator.clipboard.writeText(nom);
  } catch (e) {
    const t = document.createElement("textarea");
    t.value = nom; document.body.appendChild(t); t.select();
    try { document.execCommand("copy"); } catch (_) {}
    t.remove();
  }
  bouton.textContent = "Copié ✓"; bouton.classList.add("ok");
  setTimeout(() => { bouton.textContent = "Copier"; bouton.classList.remove("ok"); }, 1500);
}

const liste = document.getElementById("liste");
D.items.forEach((it, i) => {
  const li = document.createElement("li");
  li.className = "item";
  li.dataset.nom = it.nom;
  const id = "c" + i;
  li.innerHTML =
    '<img alt="" loading="lazy">' +
    '<div class="name"><label for="' + id + '"></label><small></small></div>' +
    '<div class="qty"><span></span><small></small></div>' +
    '<div class="actions"><button class="copy" type="button">Copier</button>' +
    '<input type="checkbox" id="' + id + '" aria-label="Acheté"></div>';
  const img = li.querySelector("img");
  img.addEventListener("error", () => { img.style.visibility = "hidden"; });
  if (it.icone) img.src = it.icone; else img.style.visibility = "hidden";
  li.querySelector("label").textContent = it.nom;
  li.querySelector(".name small").textContent =
    LOGOS[it.type] ? LOGOS[it.type][0] + " " + LOGOS[it.type][1] : "❔ autre";
  li.querySelector("input").addEventListener("change", e => {
    if (e.target.checked) etat.coches[it.nom] = true; else delete etat.coches[it.nom];
    ecrire(etat); rendre();
  });
  li.querySelector(".copy").addEventListener("click", e => copier(it.nom, e.currentTarget));
  liste.appendChild(li);
});

const jours = document.getElementById("jours");
D.jours.forEach(j => {
  const tr = document.createElement("tr");
  tr.dataset.nom = j.nom;
  const logo = LOGOS[j.type] ? LOGOS[j.type][0] : "❔";
  tr.innerHTML = "<td></td><td></td>";
  tr.children[0].textContent = j.date.slice(8, 10) + "/" + j.date.slice(5, 7);
  tr.children[1].textContent = logo + " " + j.nom + " ×" + j.qte;
  jours.appendChild(tr);
});

function rendre() {
  let fait = 0;
  liste.querySelectorAll(".item").forEach((li, i) => {
    const it = D.items[i];
    const coche = !!etat.coches[it.nom];
    if (coche) fait++;
    li.classList.toggle("done", coche);
    li.querySelector("input").checked = coche;
    li.querySelector(".qty span").textContent = it.qte * etat.persos;
    li.querySelector(".qty small").textContent = etat.persos > 1 ? "pour " + etat.persos : "pour 1";
  });
  jours.querySelectorAll("tr").forEach(tr => tr.classList.toggle("done", !!etat.coches[tr.dataset.nom]));
  document.getElementById("compteur").textContent = fait + " / " + D.items.length + " achetés";
  document.getElementById("fill").style.width = (D.items.length ? 100 * fait / D.items.length : 0) + "%";
  persos.querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", String(+b.dataset.n === etat.persos)));
  masquer.setAttribute("aria-pressed", String(etat.masquer));
  document.body.classList.toggle("hide-done", etat.masquer);
}
rendre();
</script>
</body>
</html>
"""


def generer_page(titre, debut, fin, jours, items, persos, logos):
    data = {
        "titre": titre,
        "debut": debut.isoformat(),
        "fin": fin.isoformat(),
        "persos": persos,
        "logos": logos,
        "kamas": sum(j.get("reward_kamas", 0) for j in jours),
        "items": [
            {"nom": nom, "qte": it["qte"], "type": it["type"], "icone": it.get("icone", "")}
            for nom, it in sorted(items.items(), key=lambda kv: kv[0].lower())
        ],
        "jours": [
            {"date": j["date"], "nom": j["tribute"]["item"]["name"],
             "qte": j["tribute"]["quantity"], "type": j["tribute"]["item"].get("subtype", "")}
            for j in jours
        ],
    }
    # "</" échappé pour ne jamais fermer la balise <script> par accident
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return TEMPLATE.replace("__TITRE__", titre.replace("<", "&lt;")).replace("__DATA__", blob)
