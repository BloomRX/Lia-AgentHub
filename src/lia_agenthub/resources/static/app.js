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
const VIEWS = ["library", "quarantine", "import", "shared", "diagnostics"];
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
  return el("button", {
    class: "card click", role: "listitem", onclick: () => openDetail(item.id, kind),
    "aria-label": `Abrir detalhes de ${item.name}`,
  },
    el("h3", {}, item.name, el("span", { class: "meta", text: `v${item.version}` })),
    el("p", { class: "meta", text: item.description || "Sem descrição." }),
    chips,
  );
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
  } catch (e) {
    banner(`Não foi possível carregar a biblioteca: ${e.message}`, true);
  }
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
    ["hashes", el("code", { text: (d.hashes?.treeHash || "").slice(0, 16) + "…" })],
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

  if (d.history && d.history.length) {
    body.append(el("div", { class: "section" },
      el("h3", { text: "Histórico" }),
      el("ul", { class: "issues" }, d.history.slice().reverse().map(h =>
        el("li", { text: `${h.at || ""} · ${h.action}${h.trustAfter ? ` → ${h.trustAfter}` : ""}` })))));
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
      el("button", { class: "primary", text: "Exportar", onclick: () => doExport(d.id) }));
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
  if (!confirm("Descartar este recurso? A remoção é irreversível.")) return;
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

async function doExport(id) {
  const target = prompt(
    "Destino da exportação:\n\nprivate — só para você\nshared — para compartilhar com alguém\npublic — publicação (exige base de redistribuição)\n\ntarget:",
    "private");
  if (!target) return;
  try {
    const r = await api("/api/export", { method: "POST", body: JSON.stringify({ id, target: target.trim() }) });
    if (!r.ok) {
      toast(`${r.refusedReason} ${r.hint || ""}`, true);
      return;
    }
    const extra = (r.warnings || []).join("\n");
    toast(`Pacote criado: ${r.path.split(/[\\/]/).pop()}`);
    if (extra) alert(`Pacote criado.\n\n${extra}`);
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
            el("div", { text: `${f.file} · posição ${f.offset} · ${f.note}` }))))));
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
