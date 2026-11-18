"use strict";
/* Lia Agent Hub — cliente local. Sem dependências, sem eval, sem rede externa. */

const TOKEN = document.querySelector('meta[name="lia-token"]')?.content || window.__LIA_TOKEN__ || "";
const $ = (sel, root = document) => root.querySelector(sel);
const el = (tag, attrs = {}, ...kids) => {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") n.className = v;
    else if (k === "text") n.textContent = v;
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else n.setAttribute(k, v);
  }
  for (const kid of kids.flat()) {
    if (kid == null || kid === false) continue;
    n.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  }
  return n;
};

const RISK_LABEL = { low: "Risco baixo", medium: "Risco médio", high: "Risco alto", unknown: "Risco não avaliado" };
const RISK_CLASS = { low: "ok", medium: "warn", high: "bad", unknown: "info" };
const TRUST_LABEL = {
  unreviewed: "Não revisado", "user-provided": "Fornecido por você",
  "reviewed-external": "Revisado externamente", "first-party": "Primeira parte",
};
const TYPE_LABEL = {
  "agent-skill": "Agent Skill", "mcp-server": "Servidor MCP", prompt: "Prompt",
  workflow: "Workflow", reference: "Referência", dataset: "Dataset",
  plugin: "Plugin", template: "Template", collection: "Coleção", unknown: "Desconhecido",
};

async function api(path, opts = {}) {
  const res = await fetch(path, {
    ...opts,
    headers: { "X-Lia-Token": TOKEN, "Content-Type": "application/json", ...(opts.headers || {}) },
  });
  let data = null;
  try { data = await res.json(); } catch { /* resposta sem corpo */ }
  if (!res.ok) {
    const err = new Error(data?.error || `Falha (HTTP ${res.status})`);
    err.hint = data?.hint || "";
    throw err;
  }
  return data;
}

let toastTimer = null;
function toast(msg, bad = false) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.toggle("bad", bad);
  t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { t.hidden = true; }, bad ? 7000 : 4000);
}

function banner(msg, bad = false) {
  const b = $("#banner");
  if (!msg) { b.hidden = true; return; }
  b.textContent = msg;
  b.classList.toggle("bad", bad);
  b.hidden = false;
}

/* ---------------- navegação ---------------- */
const VIEWS = ["library", "quarantine", "import", "shared", "settings", "diagnostics"];
function show(view) {
  VIEWS.forEach(v => {
    const s = $(`#view-${v}`);
    if (s) s.hidden = v !== view;
  });
  document.querySelectorAll(".tab").forEach(t =>
    t.setAttribute("aria-current", t.dataset.view === view ? "page" : "false"));
  $("#main").focus({ preventScroll: true });
  if (view === "library") loadLibrary();
  if (view === "quarantine") loadQuarantine();
  if (view === "shared") loadIndex();
  if (view === "settings") loadSettings();
  if (view === "diagnostics") loadDiagnostics();
}
document.querySelectorAll(".tab").forEach(t =>
  t.addEventListener("click", () => show(t.dataset.view)));

/* ---------------- biblioteca ---------------- */
function filters() {
  return {
    q: $("#search").value.trim(),
    type: $("#ftype").value,
    trust: $("#ftrust").value,
    tag: $("#ftag").value.trim(),
    lifecycle: "active",
  };
}

function card(item, kind) {
  const chips = el("div", { class: "chips" },
    el("span", { class: `chip ${RISK_CLASS[item.risk] || "info"}`, text: RISK_LABEL[item.risk] || item.risk }),
    el("span", { class: "chip", text: TRUST_LABEL[item.trust] || item.trust }),
    el("span", { class: "chip", text: TYPE_LABEL[item.type] || item.type }),
    !item.licenseKnown && el("span", { class: "chip warn", text: "licença desconhecida" }),
    item.containsScripts && el("span", { class: "chip warn", text: "contém scripts" }),
  );
  const conteudo = [
    el("h3", {}, item.name, el("span", { class: "meta", text: `v${item.version}` })),
    el("p", { class: "meta", text: item.description || "Sem descrição." }),
    chips,
  ];
  if (kind !== "active") {
    return el("button", {
      class: "card click", role: "listitem", onclick: () => openDetail(item.id, kind),
      "aria-label": `Abrir detalhes de ${item.name}`,
    }, ...conteudo);
  }
  // Biblioteca: a seleção é opt-in. Um checkbox dentro do card não pode
  // disparar o clique que abre o detalhe.
  const marcar = el("input", {
    type: "checkbox", class: "pick", "aria-label": `Selecionar ${item.name}`,
    onclick: (ev) => { ev.stopPropagation(); toggleSelection(item.id, ev.target.checked); },
  });
  marcar.dataset.id = item.id;
  return el("button", {
    class: "card click", role: "listitem", onclick: () => openDetail(item.id, kind),
    "aria-label": `Abrir detalhes de ${item.name}`,
  }, el("div", { class: "row" }, marcar), ...conteudo);
}

function emptyState(title, body, actionLabel, action) {
  const e = el("div", { class: "empty" }, el("strong", { text: title }), el("span", { text: body }));
  if (actionLabel) e.append(el("div", { class: "actions" },
    el("button", { class: "primary", text: actionLabel, onclick: action })));
  return e;
}

async function loadLibrary() {
  const f = filters();
  const qs = new URLSearchParams(Object.entries(f).filter(([, v]) => v)).toString();
  try {
    const { items } = await api(`/api/items?${qs}`);
    const box = $("#liblist");
    box.replaceChildren();
    $("#libcount").textContent = items.length === 0 ? "Nenhum item"
      : `${items.length} ${items.length === 1 ? "capacidade" : "capacidades"}`;
    if (items.length === 0) {
      const hasFilter = f.q || f.type || f.trust || f.tag;
      box.append(hasFilter
        ? emptyState("Nada corresponde a esses filtros.",
            "Tente outro termo ou limpe os filtros.", "Limpar filtros", () => { clearFilters(); })
        : emptyState("Sua biblioteca está vazia.",
            "Importe uma skill, um servidor MCP ou um pacote .lia-capability para começar.",
            "Importar agora", () => show("import")));
      return;
    }
    items.forEach(i => box.append(card(i, "active")));
    renderSelection(items);
  } catch (e) {
    banner(`Não foi possível carregar a biblioteca: ${e.message}`, true);
  }
}

/* ---------------- seleção múltipla e exportação em lote ---------------- */
const selected = new Set();
let currentItems = [];

function toggleSelection(id, marcado) {
  if (marcado) selected.add(id); else selected.delete(id);
  renderSelection(currentItems);
}

function renderSelection(items) {
  currentItems = items || [];
  // Um id selecionado que saiu da lista (filtro mudou) não deve continuar
  // contando em silêncio: o usuário exportaria algo que não está vendo.
  const visiveis = new Set(currentItems.map(i => i.id));
  for (const id of Array.from(selected)) if (!visiveis.has(id)) selected.delete(id);

  const bar = $("#selbar");
  const n = selected.size;
  bar.hidden = n === 0;
  $("#selinfo").textContent = n === 1 ? "1 selecionada" : `${n} selecionadas`;
  document.querySelectorAll(".pick").forEach(cb => { cb.checked = selected.has(cb.dataset.id); });
}

$("#selall").addEventListener("click", () => {
  currentItems.forEach(i => selected.add(i.id));
  renderSelection(currentItems);
});
$("#selnone").addEventListener("click", () => {
  selected.clear();
  renderSelection(currentItems);
});
$("#selexport").addEventListener("click", () => exportMany());
$("#selbar").hidden = true;

async function exportMany() {
  const ids = Array.from(selected);
  if (!ids.length) { toast("Nenhuma capacidade selecionada.", true); return; }
  const target = prompt(
    `Exportar ${ids.length} capacidade(s).\n\n` +
    "private — só para você\nshared — para compartilhar\npublic — publicação\n\ntarget:",
    settingsCache?.default_export_target || "private");
  if (!target) return;
  try {
    const r = await api("/api/export-many", { method: "POST",
      body: JSON.stringify({ ids, target: target.trim() }) });
    // Contrato de `export_many`: {ok, exported, failed, results[]}.
    const resultados = r.results || [];
    const falhas = resultados.filter(x => !x.ok);
    toast(`Pacotes criados: ${r.exported} de ${resultados.length}.`, falhas.length > 0);
    if (falhas.length) {
      // Falha parcial precisa ser visível: exportar 12 e falhar 1 em silêncio
      // faz o usuário acreditar que tem 12 pacotes.
      banner(`${falhas.length} não puderam ser exportadas: ` +
        falhas.map(f => `${f.id} (${f.refusedReason || f.reason || "motivo não informado"})`).join("; "), true);
    }
    selected.clear();
    renderSelection(currentItems);
  } catch (e) { toast(`${e.message} ${e.hint || ""}`, true); }
}

function clearFilters() {
  ["search", "ftag"].forEach(id => { $("#" + id).value = ""; });
  ["ftype", "ftrust"].forEach(id => { $("#" + id).value = ""; });
  loadLibrary();
}
["search", "ftag"].forEach(id => $("#" + id).addEventListener("input", debounce(loadLibrary, 220)));
["ftype", "ftrust"].forEach(id => $("#" + id).addEventListener("change", loadLibrary));
$("#clear-filters").addEventListener("click", clearFilters);

function debounce(fn, ms) {
  let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
}

/* ---------------- quarentena ---------------- */
async function loadQuarantine() {
  try {
    const { items } = await api("/api/quarantine");
    $("#qcount").textContent = items.length ? String(items.length) : "";
    const box = $("#qlist");
    box.replaceChildren();
    if (items.length === 0) {
      box.append(emptyState("Nada na quarentena.",
        "Todo recurso importado passa por aqui antes de entrar na biblioteca."));
      return;
    }
    items.forEach(i => box.append(card(i, "quarantined")));
  } catch (e) {
    banner(`Falha ao carregar a quarentena: ${e.message}`, true);
  }
}

/* ---------------- detalhe ---------------- */
function integrityLabel(agora) {
  if (!agora || !agora.treeHash) return el("span", { class: "muted", text: "não verificada" });
  const combinam = agora.contentHash && agora.treeHash;
  return el("span", { class: `chip ${combinam ? "ok" : "warn"}`,
    text: combinam ? "hashes conferem com o registro" : "hash ausente no registro" });
}

function kv(pairs) {
  const dl = el("dl", { class: "kv" });
  for (const [k, v] of pairs) {
    if (v === null || v === undefined || v === "") continue;
    dl.append(el("dt", { text: k }), el("dd", {}, v));
  }
  return dl;
}

function issuesList(issues) {
  if (!issues || issues.length === 0) return el("p", { class: "muted small", text: "Nenhum problema encontrado." });
  const ul = el("ul", { class: "issues" });
  for (const i of issues) {
    ul.append(el("li", { class: i.severity },
      el("strong", { text: `${i.severity.toUpperCase()} · ${i.code}` }),
      el("div", { text: i.message }),
      i.where ? el("div", { class: "muted small", text: `em ${i.where}` }) : null));
  }
  return ul;
}

async function openDetail(id, kind) {
  const drawer = $("#drawer");
  drawer.hidden = false;
  $("#dtitle").textContent = "Carregando…";
  $("#dbody").replaceChildren(el("p", { class: "muted", text: "Lendo metadados…" }));
  try {
    const d = await api(`/api/items/${encodeURIComponent(id)}`);
    renderDetail(d, kind);
  } catch (e) {
    $("#dtitle").textContent = "Erro";
    $("#dbody").replaceChildren(
      el("div", { class: "notice bad", text: e.message }),
      e.hint ? el("p", { class: "muted small", text: e.hint }) : null);
  }
}
$("#dclose").addEventListener("click", () => { $("#drawer").hidden = true; });
document.addEventListener("keydown", e => {
  if (e.key === "Escape" && !$("#drawer").hidden) { $("#drawer").hidden = true; }
});

function renderDetail(d, kind) {
  $("#dtitle").textContent = d.name;
  const body = $("#dbody");
  body.replaceChildren();

  const risk = d.risk || {};
  body.append(el("div", { class: "chips" },
    el("span", { class: `chip ${RISK_CLASS[risk.level] || "info"}`, text: RISK_LABEL[risk.level] || risk.level }),
    el("span", { class: "chip", text: TRUST_LABEL[d.trust] || d.trust }),
    el("span", { class: "chip", text: TYPE_LABEL[d.type] || d.type }),
    el("span", { class: "chip info", text: d.lifecycle })
  ));

  if (risk.disclaimer) body.append(el("div", { class: "notice info small", text: risk.disclaimer }));

  body.append(kv([
    ["Id", el("code", { text: d.id })],
    ["Versão", d.version],
    ["Domínio", d.domain],
    ["Autor declarado", d.author || el("span", { class: "muted", text: "não informado" })],
    ["Licença", d.license?.code || el("span", { class: "chip warn", text: "desconhecida — ausência não é permissão" })],
    ["Redistribuível", d.license?.redistributable ? "sim (base registrada)" : "não verificado"],
    ["Origem", d.source?.upstream || "—"],
    ["Importado em", d.source?.imported_at || "—"],
    // `detail()` devolve os hashes na RAIZ (treeHash/contentHash), não num
    // objeto `hashes`. Antes esta linha lia `d.hashes.treeHash`, que é sempre
    // undefined — a UI mostrava "…" em toda capacidade, sem erro nenhum.
    ["hash da árvore", d.treeHash
      ? el("code", { title: d.treeHash, text: d.treeHash.slice(0, 16) + "…" })
      : el("span", { class: "muted", text: "não registrado" })],
    ["hash do conteúdo", d.contentHash
      ? el("code", { title: d.contentHash, text: d.contentHash.slice(0, 16) + "…" })
      : el("span", { class: "muted", text: "não registrado" })],
    // Integridade conferida agora, contra o disco. É isto que detecta
    // alteração posterior à importação — o hash registrado sozinho não.
    ["integridade agora", integrityLabel(d.integrityNow)],
  ]));

  if (risk.factors && risk.factors.length) {
    const ul = el("ul", { class: "issues" });
    risk.factors.forEach(f => ul.append(el("li", { class: f.severity || "warning" },
      el("strong", { text: f.label || f.code }), el("div", { text: f.detail || "" }))));
    body.append(el("div", { class: "section" }, el("h3", { text: "Fatores de risco observados" }), ul));
  }
  if (risk.notEvaluated) {
    body.append(el("div", { class: "section" },
      el("h3", { text: "O que este risco NÃO avalia" }),
      el("ul", { class: "issues" }, risk.notEvaluated.map(t =>
        el("li", { class: "info", text: t })))));
  }

  body.append(el("div", { class: "section" },
    el("h3", { text: "Arquivos" }),
    el("ul", { class: "issues" }, (d.files || []).map(f => el("li", { text: f })))));

  if (d.validation) {
    body.append(el("div", { class: "section" },
      el("h3", { text: "Última validação" }),
      el("p", { class: "muted small", text: `em ${d.validation.at || "—"}` }),
      issuesList(d.validation.issues)));
  }

  if (d.duplicates && d.duplicates.length) {
    body.append(el("div", { class: "notice warn",
      text: `Conteúdo idêntico já existe em: ${d.duplicates.join(", ")}. Mesmo hash não significa mesma origem.` }));
  }

  if (d.lineage && d.lineage.length > 1) {
    const ul = el("ul", { class: "issues" });
    d.lineage.forEach((v, i) => ul.append(el("li", { class: v.lifecycle === "active" ? "info" : "" },
      el("strong", { text: `v${v.version}` }),
      el("span", { class: "muted small",
        text: ` · ${v.lifecycle}${i === 0 ? " (atual)" : " (anterior, preservada)"}` }))));
    body.append(el("div", { class: "section" },
      el("h3", { text: "Versões" }),
      ul,
      el("p", { class: "muted small",
        text: "Versões anteriores continuam no disco. Atualizar não apaga o que existia." })));
  }

  if (d.history && d.history.length) {
    body.append(el("div", { class: "section" },
      el("h3", { text: "Histórico" }),
      el("ul", { class: "issues" }, d.history.slice().reverse().slice(0, 5).map(h =>
        el("li", { text: `${h.at || ""} · ${h.action}${h.trustAfter ? ` → ${h.trustAfter}` : ""}` }))),
      d.history.length > 5
        ? el("button", { class: "ghost", text: `Ver histórico completo (${d.history.length})`,
                         onclick: () => showFullHistory(d.id, d.name) })
        : null,
      el("p", { class: "muted small",
        text: "O registro completo fica no disco, em history.json. Nada é apagado ao atualizar." })));
  }

  const actions = el("div", { class: "actions" });
  if (kind === "quarantined") {
    actions.append(
      el("button", { class: "primary", text: "Promover à biblioteca", onclick: () => promote(d.id) }),
      el("button", { class: "danger", text: "Descartar", onclick: () => discard(d.id) }));
  } else {
    actions.append(
      el("button", { class: "ghost", text: "Validar", onclick: () => validate(d.id) }),
      el("button", { class: "ghost", text: "Marcar como revisado", onclick: () => setTrust(d.id, "user-provided") }),
      el("button", { class: "ghost", text: "Licença…", onclick: () => setLicense(d.id) }),
      el("button", { class: "ghost", text: "Atualizar versão", onclick: () => doUpdate(d) }),
      el("button", { class: "primary", text: "Exportar", onclick: () => doExport(d.id) }));
    if (d.type === "mcp-server") {
      actions.append(el("button", {
        class: "ghost", text: "Configuração para o host…",
        onclick: () => showMcpConfig(d.id, d.name),
      }));
    }
    // Comparar com a versão anterior: só faz sentido se existe anterior.
    const anteriores = (d.lineage || []).filter(v => v.id !== d.id);
    if (anteriores.length) {
      actions.append(el("button", {
        class: "ghost", text: "Comparar com anterior",
        onclick: () => showDiff(anteriores[0].id, d.id, d.name),
      }));
    } else {
      // Cadeia pode ter mudado desde que o detalhe foi lido (outra aba
      // atualizou a versão). Perguntar à rota é barato e evita oferecer um
      // botão que falharia.
      actions.append(el("button", {
        class: "ghost", text: "Verificar versões",
        onclick: () => checkLineage(d.id, d.name),
      }));
    }
  }
  body.append(el("div", { class: "section" }, el("h3", { text: "Ações" }), actions));
}

async function promote(id) {
  try {
    await api("/api/promote", { method: "POST", body: JSON.stringify({ id }) });
    toast("Promovido à biblioteca.");
    $("#drawer").hidden = true;
    show("quarantine");
    loadQuarantine();
  } catch (e) { toast(`${e.message} ${e.hint || ""}`, true); }
}

async function discard(id) {
  const pedirConfirma = !settingsCache ? true : settingsCache.confirm_discard !== false;
  if (pedirConfirma && !confirm("Descartar este recurso? A remoção é irreversível.")) return;
  try {
    await api("/api/discard", { method: "POST", body: JSON.stringify({ id }) });
    toast("Descartado.");
    $("#drawer").hidden = true;
    loadQuarantine();
  } catch (e) { toast(`${e.message} ${e.hint || ""}`, true); }
}

async function validate(id) {
  try {
    const r = await api("/api/validate", { method: "POST", body: JSON.stringify({ id }) });
    const s = r.summary;
    toast(`Validação: ${s.error} erro(s), ${s.warning} aviso(s), ${s.review} para revisão.`);
    openDetail(id, "active");
  } catch (e) { toast(`${e.message} ${e.hint || ""}`, true); }
}

async function setTrust(id, trust) {
  if (!confirm(`Marcar confiança como "${TRUST_LABEL[trust]}"?\n\nConfiança é uma decisão sua. O Hub registra quem decidiu e quando.`)) return;
  try {
    await api("/api/trust", { method: "POST", body: JSON.stringify({ id, trust }) });
    toast("Confiança registrada no histórico.");
    openDetail(id, "active");
  } catch (e) { toast(`${e.message} ${e.hint || ""}`, true); }
}

/* ---------------- cadeia de versões ---------------- */
async function checkLineage(id, nome) {
  try {
    const { lineage } = await api(`/api/lineage?id=${encodeURIComponent(id)}`);
    const anteriores = (lineage || []).filter(v => v.id !== id);
    if (!anteriores.length) {
      toast(`"${nome}" está na primeira versão registrada.`);
      return;
    }
    showDiff(anteriores[0].id, id, nome);
  } catch (e) { toast(`${e.message} ${e.hint || ""}`, true); }
}

/* ---------------- configuração de host para MCP ---------------- */
async function showMcpConfig(id, nome) {
  try {
    const r = await api(`/api/mcp-config?id=${encodeURIComponent(id)}`);
    const drawer = $("#drawer");
    drawer.hidden = false;
    $("#dtitle").textContent = `Configuração — ${nome}`;
    const body = $("#dbody");
    body.replaceChildren();

    body.append(el("div", { class: "notice warn" },
      el("strong", { text: "O Hub não conecta, não instala e não autoriza. " }),
      "Este é um bloco de texto para você colar no seu cliente. Quem conecta é o host."));

    body.append(el("p", { class: "muted small", text: r.label }));
    body.append(el("pre", { class: "code" }, el("code", { text: JSON.stringify(r.bloco, null, 2) })));
    body.append(el("div", { class: "actions" },
      el("button", { class: "primary", text: "Copiar bloco",
        onclick: () => copiar(JSON.stringify(r.bloco, null, 2)) })));

    if (r.nota) body.append(el("p", { class: "muted small", text: r.nota }));

    if ((r.pendencias || []).length) {
      // Pendências ANTES de colar: um bloco colado sem a chave falha e o
      // usuário culpa o servidor.
      body.append(el("div", { class: "section" },
        el("h3", { text: "Você precisa providenciar" }),
        el("ul", { class: "issues" },
          r.pendencias.map(p => el("li", { class: "warn", text: p })))));
    }
    body.append(el("div", { class: "section" },
      el("h3", { text: "Limites deste bloco" }),
      el("ul", { class: "issues" },
        (r.avisos || []).map(a => el("li", { class: "info", text: a })))));
  } catch (e) { toast(`${e.message} ${e.hint || ""}`, true); }
}

async function copiar(texto) {
  try {
    await navigator.clipboard.writeText(texto);
    toast("Bloco copiado. Cole no seu cliente.");
  } catch {
    // Clipboard pode ser negado; selecionar o texto é o fallback honesto.
    toast("Não foi possível copiar automaticamente. Selecione o bloco e copie.", true);
  }
}

/* ---------------- histórico completo ---------------- */
async function showFullHistory(id, nome) {
  try {
    const { history } = await api(`/api/history?id=${encodeURIComponent(id)}`);
    const drawer = $("#drawer");
    drawer.hidden = false;
    $("#dtitle").textContent = `Histórico de ${nome}`;
    const body = $("#dbody");
    body.replaceChildren();
    if (!history || !history.length) {
      body.append(el("div", { class: "notice info", text: "Nenhum evento registrado." }));
      return;
    }
    // Mais recente primeiro: é a pergunta que o usuário faz.
    const lista = el("ul", { class: "issues" });
    history.slice().reverse().forEach(h => {
      const partes = [`${h.at || "(sem data)"}`, h.action];
      if (h.trustBefore || h.trustAfter) partes.push(`${h.trustBefore || "—"} → ${h.trustAfter || "—"}`);
      if (h.decidedBy) partes.push(`por ${h.decidedBy}`);
      if (h.license) partes.push(`licença ${h.license}`);
      if (h.target) partes.push(`destino ${h.target}`);
      lista.append(el("li", { class: h.action === "discard" ? "warn" : "" },
        el("strong", { text: h.action }),
        el("div", { class: "small", text: partes.join(" · ") }),
        h.note ? el("div", { class: "muted small", text: h.note }) : null));
    });
    body.append(el("div", { class: "section" }, el("h3", { text: `${history.length} evento(s)` }), lista));
  } catch (e) { toast(`${e.message} ${e.hint || ""}`, true); }
}

/* ---------------- licença (M5) ---------------- */
async function setLicense(id) {
  // Licença é decisão registrada, não inferência. O texto do diálogo deixa
  // claro que declarar NÃO é o mesmo que poder redistribuir.
  const codigo = prompt(
    "Código SPDX da licença (ex.: MIT, Apache-2.0).\n\n" +
    "Deixe em branco para registrar como DESCONHECIDA.", "");
  if (codigo === null) return;
  const base = prompt(
    "Base da decisão de redistribuição (ex.: 'LICENSE do repositório de origem').\n\n" +
    "Deixe em branco se a redistribuição NÃO está autorizada.", "");
  if (base === null) return;
  const redistribuivel = !!base.trim();
  if (redistribuivel && !confirm(
    `Marcar como redistribuível com base em:\n"${base}"\n\n` +
    "Isto autoriza exportação pública. A responsabilidade é sua e fica registrada no histórico.")) return;
  try {
    await api("/api/license", { method: "POST", body: JSON.stringify({
      id, code: codigo.trim(), redistributable: redistribuivel, basis: base.trim(),
    }) });
    toast(redistribuivel ? "Licença e base registradas." : "Licença registrada; redistribuição não autorizada.");
    openDetail(id, "active");
  } catch (e) { toast(`${e.message} ${e.hint || ""}`, true); }
}

/* ---------------- diff entre versões (M6) ---------------- */
async function showDiff(idA, idB, nome) {
  try {
    const d = await api("/api/diff", { method: "POST", body: JSON.stringify({ a: idA, b: idB }) });
    const body = $("#dbody");
    const drawer = $("#drawer");
    drawer.hidden = false;
    $("#dtitle").textContent = `Mudanças em ${nome}`;
    body.replaceChildren();

    if (d.identical) {
      body.append(el("div", { class: "notice info", text: "As duas versões têm conteúdo idêntico." }));
      return;
    }

    const resumo = d.resumo || {};
    const lista = el("ul", { class: "issues" });
    if ((resumo.arquivosAdicionados || []).length)
      lista.append(el("li", { class: "info", text: `Adicionados: ${resumo.arquivosAdicionados.join(", ")}` }));
    if ((resumo.arquivosRemovidos || []).length)
      lista.append(el("li", { class: "warn", text: `Removidos: ${resumo.arquivosRemovidos.join(", ")}` }));
    if ((resumo.arquivosAlterados || []).length)
      lista.append(el("li", { text: `Alterados: ${resumo.arquivosAlterados.join(", ")}` }));
    body.append(el("div", { class: "section" }, el("h3", { text: "Arquivos" }), lista));

    const fm = d.frontmatter || {};
    const campos = Object.keys(fm);
    if (campos.length) {
      // Mudança de contrato declarado: é o que o usuário precisa ver primeiro.
      const ul = el("ul", { class: "issues" });
      campos.forEach(c => {
        const va = fm[c].a === null ? "(não declarado)" : fm[c].a;
        const vb = fm[c].b === null ? "(não declarado)" : fm[c].b;
        ul.append(el("li", { class: "warn" },
          el("strong", { text: c }),
          el("div", { class: "small", text: `${va}  →  ${vb}` })));
      });
      body.append(el("div", { class: "section" },
        el("h3", { text: "Contrato declarado mudou" }), ul));
    }

    const corpo = d.corpo || {};
    if (corpo.alterado) {
      let texto = `+${corpo.adicionadas} / -${corpo.removidas} linhas ` +
        `(antes ${corpo.linhasAntes}, depois ${corpo.linhasDepois})`;
      if (corpo.primeiraDiferenca) texto += ` · primeira diferença na linha ${corpo.primeiraDiferenca}`;
      body.append(el("div", { class: "section" },
        el("h3", { text: "Corpo" }),
        el("p", { class: "muted small", text: texto }),
        corpo.detalheOmitido ? el("p", { class: "muted small", text: corpo.detalheOmitido }) : null));
    }
    body.append(el("p", { class: "muted small",
      text: "Este resumo aponta o que mudou. Para linha a linha, use seu editor." }));
  } catch (e) { toast(`${e.message} ${e.hint || ""}`, true); }
}

async function doExport(id) {
  const padrao = settingsCache?.default_export_target || "private";
  const target = prompt(
    "Destino da exportação:\n\nprivate — só para você\nshared — para compartilhar com alguém\npublic — publicação (exige base de redistribuição)\n\ntarget:",
    padrao);
  if (!target) return;
  try {
    const r = await api("/api/export", { method: "POST", body: JSON.stringify({ id, target: target.trim() }) });
    if (!r.ok) {
      toast(`${r.refusedReason} ${r.hint || ""}`, true);
      return;
    }
    const arquivo = r.path.split(/[\\/]/).pop();
    toast(`Pacote criado: ${arquivo}`);
    // O sufixo do nome carrega informação. Deixar o usuário descobrir sozinho
    // por que o arquivo se chama "...-NAO-REVISADO" é o mesmo que não avisar.
    const avisos = (r.warnings || []).slice();
    if (arquivo.includes("-NAO-REVISADO")) {
      avisos.unshift(
        "Esta capacidade não foi revisada por humano. O nome do arquivo leva " +
        "-NAO-REVISADO e o manifesto marca trust: unreviewed — quem receber " +
        "o pacote consegue ver isso sem abrir o Hub.");
    }
    if (avisos.length) alert(`Pacote criado.\n\n${avisos.join("\n\n")}`);
  } catch (e) { toast(`${e.message} ${e.hint || ""}`, true); }
}

async function doUpdate(d) {
  const caminho = prompt(
    `Atualizar "${d.name}" a partir de um arquivo ou pasta.\n\n` +
    "A versão atual NÃO é apagada: ela fica guardada como versão anterior.\n\nCaminho:",
    "");
  if (!caminho) return;
  try {
    const r = await api("/api/update", { method: "POST", body: JSON.stringify({ id: d.id, path: caminho }) });
    if (!r.ok) { toast(`${r.reason} ${r.hint || ""}`, true); return; }
    toast(`Atualizado para v${r.item.version}. A versão anterior continua guardada.`);
    openDetail(r.id, "active");
    loadLibrary();
  } catch (e) { toast(`${e.message} ${e.hint || ""}`, true); }
}

/* ---------------- importar ---------------- */
$("#igo").addEventListener("click", () => runImport(false));
$("#idry").addEventListener("click", () => runImport(true));

async function runImport(dryRun) {
  const path = $("#ipath").value.trim();
  const out = $("#ireport");
  if (!path) { toast("Informe um caminho.", true); return; }
  out.replaceChildren(el("p", { class: "muted", text: dryRun ? "Simulando…" : "Importando…" }));
  try {
    const r = await api("/api/import", { method: "POST", body: JSON.stringify({ path, dryRun }) });
    out.replaceChildren();
    if (!r.ok) {
      out.append(
        el("div", { class: "notice bad" }, el("strong", { text: "Importação recusada. " }), r.blockedReason),
        r.hint ? el("p", { class: "muted small", text: r.hint }) : null);
      return;
    }
    out.append(el("div", { class: "notice ok",
      text: `${dryRun ? "Simulação concluída" : "Importado para a quarentena"}: ${r.name} (${TYPE_LABEL[r.resourceType] || r.resourceType})` }));
    out.append(kv([
      ["Id", el("code", { text: r.capabilityId || "—" })],
      ["Licença detectada", r.detectedLicense || el("span", { class: "chip warn", text: "nenhuma — não significa livre" })],
      ["Contém scripts", r.containsScripts ? "sim (não executados)" : "não"],
      ["Arquivos", String((r.files || []).length)],
    ]));
    if (r.files?.length) {
      out.append(el("div", { class: "section" }, el("h3", { text: "Conteúdo" }),
        el("ul", { class: "issues" }, r.files.map(f =>
          el("li", {}, el("code", { text: f.path }), el("span", { class: "muted small", text: ` · ${f.size} bytes` }),
            f.executable ? el("span", { class: "chip warn", text: "executável" }) : null)))));
    }
    if (r.issues?.length) {
      out.append(el("div", { class: "section" }, el("h3", { text: "Problemas" }), issuesList(r.issues)));
    }
    if (r.unicodeFindings?.length) {
      out.append(el("div", { class: "section" }, el("h3", { text: "Caracteres invisíveis" }),
        el("ul", { class: "issues" }, r.unicodeFindings.map(f =>
          el("li", { class: f.category === "A" ? "error" : f.category === "B" ? "review" : "info" },
            el("strong", { text: `${f.category} · ${f.name} (${f.codePoint})` }),
            el("div", { text: `${f.file} · linha ${f.line}, coluna ${f.column} · ${f.context}` }))))));
    }
    if (r.warnings?.length) {
      out.append(el("div", { class: "section" }, el("h3", { text: "Avisos" }),
        el("ul", { class: "issues" }, r.warnings.map(w => el("li", { class: "warning", text: w })))));
    }
    if (!dryRun) {
      out.append(el("div", { class: "notice info",
        text: "Está na quarentena. Revise e promova quando quiser — nada foi executado." }));
      out.append(el("div", { class: "actions" },
        el("button", { class: "primary", text: "Ver na quarentena", onclick: () => show("quarantine") })));
      loadQuarantine();
    }
  } catch (e) {
    out.replaceChildren(el("div", { class: "notice bad", text: `${e.message} ${e.hint || ""}` }));
  }
}

/* ---------------- índice / pacotes ---------------- */
async function loadIndex() {
  try {
    const { index, health } = await api("/api/index");
    const box = $("#idxhealth");
    box.replaceChildren();
    if (!index) {
      box.append(el("div", { class: "notice info", text: "Nenhum índice gerado ainda." }));
    } else {
      box.append(kv([
        ["Capacidades", String(index.capabilities?.length || 0)],
        ["Gerado em", index.generatedAt],
        ["Assinado", "não — hashes não são assinatura"],
      ]));
      if (!health.exists) {
        box.append(el("div", { class: "notice info",
          text: "Nenhum índice publicado ainda. Gerar é seguro: ele só descreve o que já está na biblioteca." }));
      } else if (!health.ok) {
        box.append(el("div", { class: "notice warn",
          text: `Inconsistências: ${health.problems.concat(health.missingPackages.map(p => p.package)).join("; ") || "índice diverge do disco"}` }));
      } else {
        box.append(el("div", { class: "notice ok", text: "Índice consistente com o disco." }));
      }
    }
  } catch (e) {
    banner(`Falha ao ler o índice: ${e.message}`, true);
  }
}

$("#publish").addEventListener("click", async () => {
  try {
    const r = await api("/api/publish-index", { method: "POST", body: "{}" });
    toast(`Índice gerado com ${r.count} capacidade(s).`);
    loadIndex();
  } catch (e) { toast(`${e.message} ${e.hint || ""}`, true); }
});

$("#vgo").addEventListener("click", async () => {
  const path = $("#vpath").value.trim();
  const out = $("#vresult");
  if (!path) { toast("Informe o caminho do pacote.", true); return; }
  out.replaceChildren(el("p", { class: "muted", text: "Verificando…" }));
  try {
    const r = await api("/api/verify-package", { method: "POST", body: JSON.stringify({ path }) });
    out.replaceChildren();
    out.append(r.ok
      ? el("div", { class: "notice ok", text: "Hashes conferem. O conteúdo não mudou desde que o pacote foi montado." })
      : el("div", { class: "notice bad", text: "Verificação falhou." }));
    if (r.problems?.length) {
      out.append(el("ul", { class: "issues" }, r.problems.map(p => el("li", { class: "error", text: p }))));
    }
    out.append(el("p", { class: "muted small",
      text: "Isto prova integridade do arquivo, não autoria nem que o conteúdo seja seguro." }));
  } catch (e) {
    out.replaceChildren(el("div", { class: "notice bad", text: `${e.message} ${e.hint || ""}` }));
  }
});

/* ---------------- configurações ---------------- */
let settingsCache = null;

async function loadSettings() {
  try {
    const s = await api("/api/settings");
    settingsCache = s;
    $("#s-browser").checked = !!s.prefer_browser;
    $("#s-confirm").checked = !!s.confirm_discard;
    $("#s-escape").checked = !!s.escape_invisible;
    $("#s-target").value = s.default_export_target || "private";
    const d = await api("/api/diagnostics");
    $("#s-paths").replaceChildren(
      ...[["Biblioteca", d.paths.library],
          ["Quarentena", d.paths.quarantine],
          ["Exportados", d.paths.exports],
          ["Índice", d.paths.common],
          ["Configuração", d.paths.config],
          ["Logs", d.paths.logs]]
        .flatMap(([k, v]) => [el("dt", { text: k }), el("dd", {}, el("code", { text: v }))]));
  } catch (e) {
    banner(`Falha ao carregar configurações: ${e.message}`, true);
  }
}

$("#s-save").addEventListener("click", async () => {
  try {
    await api("/api/settings", { method: "POST", body: JSON.stringify({
      prefer_browser: $("#s-browser").checked,
      confirm_discard: $("#s-confirm").checked,
      escape_invisible: $("#s-escape").checked,
      default_export_target: $("#s-target").value,
    })});
    toast("Preferências salvas.");
  } catch (e) { toast(`${e.message} ${e.hint || ""}`, true); }
});

$("#s-reset").addEventListener("click", async () => {
  if (!confirm("Restaurar todas as preferências para o padrão?")) return;
  try {
    await api("/api/settings-reset", { method: "POST", body: "{}" });
    toast("Preferências restauradas.");
    loadSettings();
  } catch (e) { toast(`${e.message} ${e.hint || ""}`, true); }
});

/* ---------------- diagnóstico ---------------- */
async function loadDiagnostics() {
  try {
    const d = await api("/api/diagnostics");
    const box = $("#diag");
    box.replaceChildren();
    $("#ver").textContent = d.version;
    box.append(kv([
      ["Versão", d.version],
      ["Python", d.python],
      ["Sistema", d.platform],
      ["Empacotado", d.frozen ? "sim (executável)" : "não (execução a partir do código)"],
      ["Biblioteca", d.paths.library],
      ["Quarentena", d.paths.quarantine],
      ["Exportados", d.paths.exports],
      ["Índice comum", d.paths.common],
      ["Configuração", d.paths.config],
      ["Logs", d.paths.logs],
    ]));
    box.append(el("div", { class: "section" },
      el("h3", { text: "Contagens" }),
      el("p", { text: `${d.counts.library} na biblioteca · ${d.counts.quarantine} na quarentena` })));
    box.append(el("div", { class: "section" },
      el("h3", { text: "Saúde do índice" }),
      el("div", { class: `notice ${!d.index.exists ? "info" : d.index.ok ? "ok" : "warn"}`,
        text: !d.index.exists ? "Nenhum índice publicado ainda — não é um erro."
          : d.index.ok ? "Índice e disco concordam."
          : `Atenção: ${d.index.problems.length + d.index.missingPackages.length} inconsistência(s).` })));
    box.append(el("p", { class: "muted small",
      text: "Nenhuma informação é enviada para fora. Não há telemetria, conta ou sincronização." }));
  } catch (e) {
    banner(`Falha no diagnóstico: ${e.message}`, true);
  }
}

/* ---------------- início ---------------- */
document.addEventListener("DOMContentLoaded", () => {
  show("library");
  loadQuarantine();
});
if (document.readyState !== "loading") { show("library"); loadQuarantine(); }
