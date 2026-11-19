/**
 * Serviço de integração do Studio (F8 — requisito §11).
 *
 * Uma única fachada usada pelos dois hospedeiros reais do produto:
 *   - Electron (`electron/main.cjs`, via IPC) — aplicação desktop;
 *   - Vite (`vite.config.js`, via API HTTP same-origin) — navegador/preview.
 *
 * Isso evita dois sistemas paralelos: as mesmas funções de capability, hub,
 * preflight, planejamento, execução, assets e exportação servem os dois.
 *
 * Regras preservadas: nenhum download/instalação/compra/envio; escritas
 * confinadas a `<projectRoot>/.lia-forge/` com arquivo temporário + rename e
 * recusa de symlink; segredos redigidos; nada é afirmado sem evidência.
 */

import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { createHash, randomUUID } from 'node:crypto';

import { createCapabilityRegistry } from '../capabilities/registry.mjs';
import { createAdapterRegistry } from '../../electron/adapters/index.mjs';
import { discoverHub } from '../hub/provider-hub.mjs';
import { runPreflight } from '../qa/preflight.mjs';
import { listWorkflows, planWorkflow, WORKFLOW_IDS } from '../orchestrator/planner.mjs';
import { ExecutionManager } from '../engine/execution-manager.mjs';
import { isResumableRunState } from '../engine/run-states.mjs';
import { assertSafeWriteTarget, checkAuthorization, redactSecrets, sha256Hex } from '../engine/gates.mjs';
import { isPathContained, resolveContainedPath } from '../fs/path-containment.mjs';
import { MEASURE_LIMITS, compareWithRecord, measureArtifactBytes } from '../assets/inspect.mjs';
import {
  RECONCILIATION_HISTORY_LIMIT,
  RECONCILIATION_OPERATION_LABELS,
  RECONCILIATION_OPERATIONS,
  RECONCILIATION_SCHEMA_VERSION,
  RECONCILIATION_TOKEN_TTL_MS,
  ReconciliationError,
  applyDecision,
  assetFingerprint,
  comparePlanState,
  createPlanLedger,
  describeActor,
  fail,
  fileFingerprint,
  nextVersionLabel,
  normalizeJustification,
  normalizeReviewer,
  planState,
  reconciliationEvidence,
  reconciliationHistory,
  recordedSnapshot,
  storeFingerprint,
  summarizeMeasurement,
} from '../assets/reconciliation.mjs';
import {
  COMPARISON_SCHEMA_VERSION,
  DUPLICATE_GROUP_LIMIT,
  DUPLICATE_MEASURE_BUDGET,
  PREVIEW_CONTENT_TYPES,
  PREVIEW_MAX_BYTES,
  VERSION_MEASURE_BUDGET,
  artifactFields,
  buildDuplicateReport,
  collectHashCandidates,
  contentVerdict,
  describeArtifactSide,
  divergenceNotes,
  duplicateMeasureOrder,
  pairArtifacts,
  previewFor,
  primaryArtifact,
  versionFields,
} from '../assets/comparison.mjs';
import {
  authorizationForScope,
  buildRunScope,
  missingProtectedActions,
  scopeRequiresAuthorization,
} from '../engine/run-authorization.mjs';

// Reexportado para os consumidores existentes (testes, UI) não precisarem saber
// onde a política mora; a implementação é uma só, em run-authorization.mjs.
export {
  authorizationForScope,
  bindAuthorizationToScope,
  buildRunScope,
  missingProtectedActions,
  policyAuthorizationForScope,
  scopeRequiresAuthorization,
} from '../engine/run-authorization.mjs';
import { createAssetManager, classifyRights } from '../assets/manager.mjs';
import { decodePng, encodePngRgba, analyzePngContent } from '../qa/png-codec.mjs';
import { validatePngStructure } from '../qa/png.mjs';
import { inspectGlb } from '../model3d/glb.mjs';
import { validateStepOutputs } from '../qa/validators.mjs';
import { createHostDefaults } from '../integrations/host-defaults.mjs';
import { createProviderStore, isLoopbackEndpoint } from '../integrations/provider-store.mjs';
import { inspectProjectStructure } from '../integrations/project-structure.mjs';
import { adapterError } from '../adapters/sdk.mjs';
import { generateVfxAtlas } from '../vfx/core.mjs';
import { buildExportBundle, checkDestinationCompatibility, listDestinations } from '../destinations/profiles.mjs';

export const STUDIO_SERVICE_SCHEMA_VERSION = 1;
const RUNS_DIRECTORY = '.lia-forge/runs';
/** Pasta das entradas fornecidas pelo usuário (imagens de referência, modelos). */
const INPUT_DIRECTORY = 'input';
const MAX_INPUT_BYTES = 32 * 1024 * 1024;
const MAX_INPUT_ENTRIES = 400;
const MAX_INPUT_DEPTH = 3;
const INPUT_IMAGE_EXTENSIONS = Object.freeze(['png', 'jpg', 'jpeg', 'webp']);
const INPUT_MODEL_EXTENSIONS = Object.freeze(['glb', 'gltf', 'fbx', 'obj', 'stl', 'blend']);
const INPUT_OTHER_EXTENSIONS = Object.freeze(['md', 'json', 'txt']);
const INPUT_EXTENSIONS = Object.freeze([...INPUT_IMAGE_EXTENSIONS, ...INPUT_MODEL_EXTENSIONS, ...INPUT_OTHER_EXTENSIONS]);

/**
 * Nome de arquivo vindo do usuário vira nome de arquivo dentro de `input/`:
 * sem caminho, sem `..`, sem caracteres que dependam de shell ou de sistema de
 * arquivos específico. Colisão nunca sobrescreve o original — ganha sufixo.
 */
function sanitizeInputName(value) {
  const base = path.basename(String(value ?? '').replace(/\\/g, '/')).trim();
  if (!base || base === '.' || base === '..') return null;
  const cleaned = base
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^A-Za-z0-9._-]+/g, '-')
    .replace(/^[-.]+/, '')
    .replace(/\.{2,}/g, '.')
    .slice(0, 120);
  if (!cleaned || cleaned.startsWith('.')) return null;
  return cleaned;
}

function extensionOf(name) {
  const match = /\.([A-Za-z0-9]+)$/.exec(String(name ?? ''));
  return match ? match[1].toLowerCase() : '';
}
const MAX_PREVIEW_BYTES = 6 * 1024 * 1024;

async function pathExists(target) {
  try {
    await fs.access(target);
    return true;
  } catch {
    return false;
  }
}

/**
 * @param {object} options
 * @param {string} options.projectRoot raiz do projeto (escrita confinada aqui)
 * @param {Function} [options.findExternalTool] descoberta de ferramentas
 * @param {object} [options.taskRegistry] registro de processos filhos
 * @param {Function} [options.getWorkflowClient] cliente ComfyUI (Electron)
 * @param {Function} [options.validateStageOutputs] validação de estágio legada
 * @param {{maxConcurrent?:number, ramMb?:number}} [options.limits]
 */
/**
 * `validated` derivado de evidência, não declarado (P0-4).
 *
 * Só é `true` quando o passo concluiu, tem ao menos um validador **aprovado**,
 * nenhum reprovado, e a validação rodou sobre estes bytes — o que é conferido
 * comparando o SHA-256 que o engine gravou para o passo com o do arquivo. Um
 * passo com várias saídas tem um hash gravado (o do artefato principal): para as
 * demais saídas não há como afirmar que a validação as cobriu, e o registro diz
 * isso em vez de marcar `true`.
 *
 * @param {{step:object|null, sha256:string, emittedCount:number}} args
 * @returns {{validated:boolean, validator:string|null, contentMetrics:object|null, validation:object}}
 */
export function deriveArtifactValidation({ step, sha256, emittedCount = 1 }) {
  const validations = step?.validations ?? [];
  const passed = validations.filter((item) => item.status === 'passed');
  const failed = validations.filter((item) => item.status === 'failed');
  const skipped = validations.filter((item) => item.status === 'skipped');
  const validators = validations.map((item) => `${item.validator}=${item.status}`);
  const at = step?.finishedAt ?? null;
  const evidence = (status, reason) => Object.freeze({
    validated: false,
    validator: null,
    contentMetrics: null,
    validation: Object.freeze({
      status,
      reason,
      validators: Object.freeze(validators),
      sha256: sha256 ?? null,
      stepId: step?.id ?? null,
      stepState: step?.state ?? null,
      at,
    }),
  });

  if (!step || step.state !== 'succeeded') {
    return evidence('step-not-succeeded', `O passo ${step ? `"${step.id}" está "${step.state}"` : 'não existe no run'}; nenhuma validação aprovada pode ser atribuída a este arquivo.`);
  }
  if (failed.length > 0) {
    return evidence('validation-failed', `Validação reprovada: ${(failed[0].problems ?? []).join('; ') || failed[0].validator}.`);
  }
  if (passed.length === 0) {
    return evidence('not-validated', skipped.length > 0
      ? `Validadores pulados por falta de entrada: ${skipped.map((item) => `${item.validator} (${item.reason ?? 'sem entrada'})`).join('; ')}.`
      : 'O passo não declara validador: nada foi conferido sobre este arquivo.');
  }
  if (!step.sha256 || step.sha256 !== sha256) {
    return evidence('hash-diverged', emittedCount > 1
      ? 'O passo gravou um único SHA-256 (o do artefato principal) para várias saídas: não há como afirmar que a validação aprovada cobriu este arquivo.'
      : `A validação aprovada não corresponde a estes bytes (passo gravou ${String(step.sha256).slice(0, 12)}…, arquivo é ${String(sha256).slice(0, 12)}…).`);
  }
  return Object.freeze({
    validated: true,
    validator: passed.map((item) => item.validator).join(','),
    contentMetrics: passed.find((item) => item.metrics)?.metrics ?? null,
    validation: Object.freeze({
      status: 'validated',
      reason: `Validado por ${passed.map((item) => item.validator).join(', ')} sobre o SHA-256 gravado pelo passo.`,
      validators: Object.freeze(validators),
      sha256,
      stepId: step.id,
      stepState: step.state,
      at,
    }),
  });
}

export function createStudioService(options = {}) {
  const projectRoot = path.resolve(options.projectRoot ?? process.cwd());
  const limits = { maxConcurrent: 1, ...(options.limits ?? {}) };
  const registry = createCapabilityRegistry();

  const hash = (bytes) => createHash('sha256').update(bytes).digest('hex');

  // As integrações reais do repositório (Blender, ComfyUI, descoberta de
  // ferramentas, validação de estágio, registro de processos) são o padrão em
  // qualquer hospedeiro — não só no Electron. Quem injetar dependências próprias
  // continua tendo precedência.
  const host = options.hostDefaults ?? createHostDefaults();

  const adapterDependencies = {
    findExternalTool: options.findExternalTool ?? host.findExternalTool ?? (() => null),
    taskRegistry: options.taskRegistry ?? host.taskRegistry ?? { start: () => { throw new Error('Task registry indisponível neste hospedeiro.'); } },
    assertPathInsideProject: options.assertPathInsideProject ?? (async (candidate) => {
      const resolved = path.resolve(candidate);
      const gate = await assertSafeWriteTarget({
        root: projectRoot,
        target: resolved,
        resolve: async (value) => path.resolve(value),
        lstat: async (value) => fs.lstat(value),
        realpath: async (value) => fs.realpath(value),
      });
      if (!gate.ok) throw new Error(gate.reason);
      return resolved;
    }),
    buildBlenderSpritesheetArgs: options.buildBlenderSpritesheetArgs ?? host.buildBlenderSpritesheetArgs ?? (() => { throw new Error('buildBlenderSpritesheetArgs indisponível neste hospedeiro.'); }),
    runProcess: options.runProcess ?? host.runProcess ?? (async () => { throw new Error('runProcess indisponível neste hospedeiro.'); }),
    validateSpritesheetFiles: options.validateSpritesheetFiles ?? host.validateSpritesheetFiles ?? (() => { throw new Error('validateSpritesheetFiles indisponível neste hospedeiro.'); }),
    validateStageOutputs: options.validateStageOutputs ?? host.validateStageOutputs ?? (() => {}),
    getWorkflowClient: options.getWorkflowClient ?? (() => workflowClient()),
    hash,
    configuration: options.configuration ?? {},
  };

  // ------------------------------------------------------------- providers
  // Escolha real de backend (§9): local, remoto (autorizado) ou desativado.
  // A configuração vive no projeto, é gravada de forma atômica e nunca contém
  // segredo; o registro de adapters é reconstruído quando ela muda.
  const providerStore = options.providerStore ?? createProviderStore({ projectRoot });
  let adaptersInstance = null;
  let adaptersKey = null;
  let providerCache = null;

  function configurationFor(providers) {
    return {
      'blender-spritesheet': {
        executable: providers.blender.mode === 'path' ? providers.blender.executable : null,
        script: providers.blender.scriptPath ?? host.blenderScriptPath,
        frameSize: providers.blender.frameSize,
        validateContent: true,
      },
      'comfyui-concept': {
        endpoint: providers.comfyui.mode === 'local-loopback' ? providers.comfyui.endpoint : null,
        checkpoint: providers.comfyui.checkpoint,
        workflowId: providers.comfyui.workflowId,
      },
    };
  }

  async function providersNow() {
    return providerStore.read();
  }

  async function currentAdapters() {
    const config = await providersNow();
    const key = JSON.stringify(config.providers);
    if (!adaptersInstance || key !== adaptersKey) {
      adaptersKey = key;
      providerCache = config.providers;
      adaptersInstance = createAdapterRegistry({
        ...adapterDependencies,
        configuration: { ...(options.configuration ?? {}), ...configurationFor(config.providers) },
      });
    }
    return adaptersInstance;
  }

  /**
   * Estado dos providers para a interface: o que está disponível, o que falta e
   * o que precisa de decisão humana. Nada aqui contata um servidor remoto.
   */
  async function providerStates() {
    const config = await providersNow();
    const comfy = config.providers.comfyui;
    const blender = config.providers.blender;
    const client = comfy.mode === 'local-loopback' ? await workflowClient() : null;
    let comfyStatus = null;
    if (client) {
      // includeModels: a lista de checkpoints instalados vem do próprio servidor —
      // é o que permite escolher um modelo real na interface, sem baixar nada.
      try { comfyStatus = await client.getComfyUiStatus({ includeModels: true }); }
      catch (error) { comfyStatus = { connected: false, error: String(error.message ?? error).slice(0, 200) }; }
    }
    const configured = blender.mode === 'disabled' ? null : (blender.executable ?? null);
    // Um caminho digitado pelo usuário não torna a ferramenta disponível: só o
    // teste de executável no disco decide (nunca apresentar ausente como pronto).
    const executable = await (async () => {
      if (configured) {
        try {
          await fs.access(configured, fs.constants.X_OK);
          return configured;
        } catch (error) {
          // Só erro de filesystem vira "indisponível"; erro de programação sobe.
          if (['ENOENT', 'EACCES', 'ENOTDIR', 'EPERM', 'ELOOP'].includes(error?.code)) return null;
          throw error;
        }
      }
      return host.findExternalTool?.('blender') ?? null;
    })();
    const configuredMissing = Boolean(configured) && !executable;
    return Object.freeze({
      schemaVersion: config.schemaVersion,
      updatedAt: config.updatedAt,
      corrupt: config.corrupt ?? null,
      comfyui: {
        mode: comfy.mode,
        endpoint: comfy.endpoint ?? (comfy.mode === 'local-loopback' ? 'http://127.0.0.1:8188' : null),
        checkpoint: comfy.checkpoint,
        workflowId: comfy.workflowId,
        connected: Boolean(comfyStatus?.connected),
        version: comfyStatus?.version ?? null,
        devices: comfyStatus?.devices ?? [],
        queue: comfyStatus?.queue ?? null,
        models: comfyStatus?.models ?? null,
        checkpoints: Array.isArray(comfyStatus?.models?.checkpoints) ? comfyStatus.models.checkpoints : [],
        modelCounts: comfyStatus?.models
          ? Object.fromEntries(Object.entries(comfyStatus.models).map(([folder, list]) => [folder, Array.isArray(list) ? list.length : null]))
          : null,
        detail: comfy.mode === 'local-loopback'
          ? (comfyStatus?.connected
            ? `ComfyUI local respondeu em ${comfyStatus.endpoint ?? comfy.endpoint ?? 'http://127.0.0.1:8188'}.`
            : `ComfyUI local não respondeu (${comfyStatus?.error ?? 'sem servidor em execução'}). Ele não é instalado nem iniciado pela Lia Forge.`)
          : comfy.mode === 'remote'
            ? (comfy.authorization?.granted
              ? `Provider remoto ${comfy.endpoint} autorizado por ${comfy.authorization.grantedBy ?? 'usuário'} em ${comfy.authorization.grantedAt}.`
              : `Provider remoto ${comfy.endpoint ?? '(sem endpoint)'} configurado, mas sem autorização: nada é enviado e nenhum custo é gerado.`)
            : 'ComfyUI desativado por você: nenhum servidor foi contatado.',
        authorization: comfy.authorization,
        maxCostUnits: comfy.maxCostUnits,
        credentialRef: comfy.credentialRef,
      },
      blender: {
        mode: blender.mode,
        executable,
        scriptPath: blender.scriptPath ?? host.blenderScriptPath,
        frameSize: blender.frameSize,
        available: Boolean(executable),
        configuredExecutable: configured,
        // De onde veio o executável aceito: caminho indicado pelo usuário ou PATH.
        executableSource: executable ? (configured ? 'user-configuration' : 'path') : null,
        // Existência + permissão de execução foram medidas; a identidade como
        // Blender não foi (o pré-voo não executa o arquivo), então não é afirmada.
        versionConfirmed: false,
        detail: blender.mode === 'disabled'
          ? 'Blender desativado por você: os passos 3D ficam bloqueados com esse motivo.'
          : executable
            ? (configured
              ? `Caminho configurado por você (${executable}) existe e é executável; a identidade como Blender não foi confirmada (o pré-voo não executa o arquivo).`
              : `Blender encontrado no PATH em ${executable}; versão não confirmada (o pré-voo não executa o arquivo).`)
            : configuredMissing
              ? `O caminho informado (${configured}) não existe ou não é executável. Confira a instalação do Blender.`
              : 'Blender não foi detectado nesta máquina. Ele não é instalado automaticamente: instale por conta própria ou informe o caminho do executável.',
      },
      note: 'Nenhuma ferramenta foi instalada, baixada ou iniciada; nenhum endpoint remoto foi contatado.',
    });
  }

  /**
   * Cliente ComfyUI do hospedeiro, ajustado ao provider escolhido:
   *   - local-loopback → endpoint configurado (ou o padrão 127.0.0.1:8188);
   *   - disabled       → nada é contatado e o motivo é dito com clareza;
   *   - remote         → o cliente local não contata outra máquina; quem faz
   *                      isso é o adapter remoto, com autorização gravada.
   */
  async function workflowClient() {
    const inner = await host.getWorkflowClient();
    const providers = providerCache ?? (await providersNow()).providers;
    const comfy = providers.comfyui;
    if (comfy.mode === 'disabled') {
      const reason = 'ComfyUI está desativado por você em Configurações → Providers. Nenhum servidor foi contatado.';
      return {
        ...inner,
        getComfyUiEndpoint: () => comfy.endpoint ?? 'http://127.0.0.1:8188',
        getComfyUiStatus: async () => ({ connected: false, available: false, endpoint: comfy.endpoint ?? null, detail: reason, version: null, models: null }),
        runComfyUiConcept: async () => { throw adapterError('WORKFLOW_BLOCKED', reason, { adapterId: 'comfyui-concept' }); },
      };
    }
    if (comfy.mode === 'remote') {
      const reason = comfy.authorization?.granted
        ? 'Provider configurado como remoto: a geração local não contata outra máquina. O passo usa o adapter remoto autorizado.'
        : 'Provider remoto configurado, mas sem autorização gravada: nada é enviado e nenhum custo é gerado.';
      return {
        ...inner,
        getComfyUiEndpoint: () => comfy.endpoint ?? 'http://127.0.0.1:8188',
        getComfyUiStatus: async () => ({ connected: false, available: false, endpoint: comfy.endpoint ?? null, detail: reason, version: null, models: null }),
        runComfyUiConcept: async () => { throw adapterError('WORKFLOW_BLOCKED', reason, { adapterId: 'comfyui-concept' }); },
      };
    }
    const endpoint = comfy.endpoint ?? null;
    if (endpoint && !isLoopbackEndpoint(endpoint)) {
      throw adapterError('ADAPTER_SEND_UNAUTHORIZED', `O provider local recusa o endpoint ${endpoint} (não é da própria máquina). Use o modo remoto com autorização explícita.`, { adapterId: 'comfyui-concept' });
    }
    return {
      ...inner,
      getComfyUiEndpoint: (explicit = null) => inner.getComfyUiEndpoint(explicit ?? endpoint),
      getComfyUiStatus: (options2 = {}) => inner.getComfyUiStatus({ ...options2, endpoint: options2.endpoint ?? endpoint }),
      runComfyUiConcept: (options2 = {}) => inner.runComfyUiConcept({ ...options2, endpoint: options2.endpoint ?? endpoint }),
    };
  }

  /** Informações reais da máquina. GPU nunca é afirmada sem probe autorizado. */
  async function measureMachine() {
    const totalRamMb = Math.round(os.totalmem() / (1024 * 1024));
    const freeRamMb = Math.round(os.freemem() / (1024 * 1024));
    let diskMb = null;
    try {
      const stats = await fs.statfs(projectRoot);
      diskMb = Math.round((stats.bavail * stats.bsize) / (1024 * 1024));
    } catch {
      diskMb = null;
    }
    return Object.freeze({
      os: process.platform,
      release: os.release(),
      arch: process.arch,
      cpus: os.cpus().length,
      cpuModel: os.cpus()[0]?.model ?? null,
      ramMb: totalRamMb,
      freeRamMb,
      diskMb,
      // Probe de GPU/Vulkan exige decisão humana (T12 D11): não executado.
      gpu: null,
      gpuNote: 'Nenhum probe de GPU/Vulkan foi executado: a verificação depende de autorização humana.',
      vramMb: null,
      node: process.version,
      projectRoot,
    });
  }

  /**
   * Medições da máquina. O padrão mede de verdade neste processo; um hospedeiro
   * que já mede (ou um teste que simula outra máquina) pode injetar.
   */
  const machineInfo = typeof options.machineInfo === 'function' ? options.machineInfo : measureMachine;

  async function discover() {
    const machine = await machineInfo();
    const { hub, discoveries } = await discoverHub({ registry, adapters: (await currentAdapters()).all(), machine });
    return { hub, discoveries, machine };
  }

  async function emitFor(runDirectory, hashes = new Map()) {
    await fs.mkdir(runDirectory, { recursive: true });
    return async (relativePath, bytes) => {
      const target = path.join(runDirectory, relativePath);
      const gate = await assertSafeWriteTarget({
        root: runDirectory,
        target,
        resolve: async (value) => path.resolve(value),
        lstat: async (value) => fs.lstat(value).catch(() => null),
        realpath: async (value) => fs.realpath(value).catch(() => null),
      });
      if (!gate.ok) throw Object.assign(new Error(gate.reason), { code: 'UNSAFE_WRITE_TARGET' });
      await fs.mkdir(path.dirname(target), { recursive: true });
      const temporary = `${target}.${process.pid}.${randomUUID()}.tmp`;
      await fs.writeFile(temporary, bytes, { flag: 'wx' });
      try {
        await fs.rename(temporary, target);
      } catch (error) {
        await fs.rm(temporary, { force: true });
        throw error;
      }
      const projectRelative = path.relative(projectRoot, target).split(path.sep).join('/');
      const digest = hash(bytes);
      // o hash fica registrado pelos dois caminhos usados nos relatórios
      hashes.set(projectRelative, digest);
      hashes.set(path.relative(runDirectory, target).split(path.sep).join('/'), digest);
      return projectRelative;
    };
  }

  const storeFile = path.join(projectRoot, '.spriteforge', 'assets.json');

  async function readStore() {
    if (!await pathExists(storeFile)) return null;
    try {
      return JSON.parse(await fs.readFile(storeFile, 'utf8'));
    } catch {
      return null;
    }
  }

  async function writeStore(payload) {
    const serialized = `${JSON.stringify(payload, null, 2)}\n`;
    if (Buffer.byteLength(serialized) > 24 * 1024 * 1024) throw new Error('Asset store excede o limite de 24 MB');
    await fs.mkdir(path.dirname(storeFile), { recursive: true });
    const temporary = `${storeFile}.${process.pid}.${randomUUID()}.tmp`;
    await fs.writeFile(temporary, serialized, { encoding: 'utf8', flag: 'wx' });
    try {
      await fs.rename(temporary, storeFile);
    } catch (error) {
      await fs.rm(temporary, { force: true });
      throw error;
    }
  }

  async function assets() {
    return createAssetManager({ store: await readStore(), save: writeStore });
  }

  // ---------------------------------------------------- entradas do usuário
  const inputRoot = path.join(projectRoot, INPUT_DIRECTORY);

  /**
   * Resolve um caminho dentro de uma raiz do projeto sem seguir symlink para
   * fora. A interface envia caminhos relativos ao projeto (`input/sprite.png`);
   * os demais são relativos à pasta de confinamento. As duas formas apontam para
   * o mesmo arquivo e nenhuma delas pode sair de `root`.
   */
  async function resolveInside(root, candidate, projectRoot = path.dirname(root)) {
    const value = String(candidate ?? '').trim().replace(/^[\\/]+/, '');
    if (!value || path.isAbsolute(value)) return null;
    const prefixed = value === 'input' || value.startsWith('input/') || value.startsWith('input\\');
    const base = prefixed && path.resolve(root) !== path.resolve(projectRoot) ? projectRoot : root;
    const resolved = path.resolve(base, value);
    const gate = await assertSafeWriteTarget({
      root,
      target: resolved,
      resolve: async (item) => path.resolve(item),
      lstat: async (item) => fs.lstat(item).catch(() => null),
      realpath: async (item) => fs.realpath(item).catch(() => null),
    });
    return gate.ok ? resolved : null;
  }

  /**
   * Mede o que dá para medir aqui, sem ferramenta externa: PNG e GLB são
   * decodificados de verdade; JPEG/WebP são conferidos pela assinatura. O que
   * não pôde ser verificado fica marcado como tal — nunca como "ok".
   */
  function describeInputBytes(name, bytes) {
    const extension = extensionOf(name);
    const base = {
      name,
      format: extension || null,
      bytes: bytes.length,
      sha256: hash(bytes),
      kind: INPUT_IMAGE_EXTENSIONS.includes(extension) ? 'image'
        : INPUT_MODEL_EXTENSIONS.includes(extension) ? 'model'
          : INPUT_OTHER_EXTENSIONS.includes(extension) ? 'document' : 'other',
      contentChecked: false,
      width: null,
      height: null,
      problem: null,
    };
    if (extension === 'png') {
      try {
        validatePngStructure(bytes);
        const decoded = decodePng(bytes);
        const analysis = analyzePngContent(bytes);
        return Object.freeze({
          ...base, contentChecked: true, width: decoded.width, height: decoded.height,
          uniqueColors: analysis.uniqueColors, coverage: analysis.coverage, blank: analysis.blank,
          boundingBox: analysis.boundingBox ?? null,
        });
      } catch (error) {
        return Object.freeze({ ...base, problem: `PNG inválido: ${String(error.message ?? error).slice(0, 180)}` });
      }
    }
    if (extension === 'glb') {
      try {
        const info = inspectGlb(bytes);
        return Object.freeze({
          ...base, contentChecked: true,
          meshCount: info.meshCount, triangleCount: info.triangleCount,
          materials: info.materials?.length ?? 0, animationCount: info.animationCount ?? 0,
          animationNames: info.animationNames ?? [], skinned: info.skinned === true,
        });
      } catch (error) {
        return Object.freeze({ ...base, problem: `GLB inválido: ${String(error.message ?? error).slice(0, 180)}` });
      }
    }
    if (extension === 'jpg' || extension === 'jpeg') {
      const ok = bytes.length > 4 && bytes[0] === 0xff && bytes[1] === 0xd8 && bytes[2] === 0xff;
      return Object.freeze({ ...base, contentChecked: ok, problem: ok ? null : 'A assinatura do arquivo não é JPEG.' });
    }
    if (extension === 'webp') {
      const ok = bytes.length > 12
        && Buffer.from(bytes.slice(0, 4)).toString('latin1') === 'RIFF'
        && Buffer.from(bytes.slice(8, 12)).toString('latin1') === 'WEBP';
      return Object.freeze({ ...base, contentChecked: ok, problem: ok ? null : 'A assinatura do arquivo não é WebP.' });
    }
    return Object.freeze(base);
  }

  async function walkInputs() {
    const entries = [];
    const stack = [{ directory: inputRoot, depth: 0 }];
    while (stack.length && entries.length < MAX_INPUT_ENTRIES) {
      const { directory, depth } = stack.pop();
      let items = [];
      try {
        items = await fs.readdir(directory, { withFileTypes: true });
      } catch {
        continue; // pasta inexistente ainda não é erro: o projeto pode não ter entradas
      }
      for (const item of items) {
        if (entries.length >= MAX_INPUT_ENTRIES) break;
        const absolute = path.join(directory, item.name);
        if (item.isDirectory()) {
          if (depth + 1 < MAX_INPUT_DEPTH) stack.push({ directory: absolute, depth: depth + 1 });
          continue;
        }
        // Só arquivo regular: symlink, dispositivo ou FIFO não é entrada utilizável.
        if (!item.isFile()) continue;
        const extension = extensionOf(item.name);
        if (!INPUT_EXTENSIONS.includes(extension)) continue;
        const stats = await fs.stat(absolute).catch(() => null);
        if (!stats) continue;
        const relative = path.relative(projectRoot, absolute).split(path.sep).join('/');
        let measured = null;
        if (stats.size <= MAX_INPUT_BYTES) {
          try {
            measured = describeInputBytes(item.name, await fs.readFile(absolute));
          } catch {
            measured = null;
          }
        }
        entries.push(Object.freeze({
          path: relative,
          name: item.name,
          kind: measured?.kind ?? (INPUT_IMAGE_EXTENSIONS.includes(extension) ? 'image' : INPUT_MODEL_EXTENSIONS.includes(extension) ? 'model' : 'other'),
          bytes: stats.size,
          modifiedAt: stats.mtime.toISOString(),
          width: measured?.width ?? null,
          height: measured?.height ?? null,
          format: extension || null,
          contentChecked: measured?.contentChecked ?? false,
          problem: measured?.problem ?? (stats.size > MAX_INPUT_BYTES ? `Arquivo maior que ${MAX_INPUT_BYTES} bytes: não foi verificado aqui.` : null),
          sha256: measured?.sha256 ?? null,
          // Métricas já medidas na leitura: servem para escolher referência e
          // para o Comparison Lab sem decodificar o mesmo arquivo duas vezes.
          uniqueColors: measured?.uniqueColors ?? null,
          coverage: measured?.coverage ?? null,
          blank: measured?.blank ?? null,
          triangleCount: measured?.triangleCount ?? null,
          meshCount: measured?.meshCount ?? null,
          animationCount: measured?.animationCount ?? null,
          skinned: measured?.skinned ?? null,
        }));
      }
    }
    entries.sort((a, b) => a.path.localeCompare(b.path));
    return entries;
  }

  // ------------------------------------------------- contexto de cada passo
  /**
   * O engine é agnóstico de ferramenta: quem conhece o contrato do Blender e do
   * ComfyUI é o hospedeiro. Aqui cada passo recebe a pasta real onde pode
   * gravar, o script, as dimensões de frame, o "asset" e o caminho do modelo de
   * entrada — sem os quais os adapters externos devolvem WORKFLOW_BLOCKED.
   */
  const MODEL_EXTENSIONS = Object.freeze(['.blend', '.glb', '.gltf', '.fbx', '.obj', '.stl']);
  const DEFAULT_ANIMATIONS = Object.freeze(['idle', 'walk', 'attack']);

  function isModelPath(value) {
    return typeof value === 'string' && MODEL_EXTENSIONS.includes(path.extname(value).toLowerCase());
  }

  /**
   * Injeção de filesystem para os gates de contenção (mesmo padrão de
   * `assertSafeWriteTarget`: funções injetadas, módulo testável sem disco).
   */
  const containmentFs = {
    resolve: async (value) => path.resolve(value),
    lstat: async (value) => fs.lstat(value).catch(() => null),
    realpath: async (value) => fs.realpath(value).catch(() => null),
  };

  /**
   * Inspeção de um arquivo do projeto: confinamento + medição real + comparação
   * com o que o store registrou.
   *
   * Regras de honestidade: nada é medido duas vezes por chamada além do teto
   * (`measureBudget`), arquivo ausente volta `exists: false` (nunca uma medição
   * inventada), caminho que sai do projeto volta `refused` com o motivo, e formato
   * que o repositório não sabe decodificar volta com a limitação escrita.
   */
  async function inspectProjectFile(declaredPath, { recorded = null, measure = true, grid = null } = {}) {
    const relative = String(declaredPath ?? '').trim();
    if (!relative) {
      return Object.freeze({
        path: relative,
        exists: false,
        symlink: false,
        measurement: null,
        readError: null,
        refused: 'caminho vazio',
        comparison: compareWithRecord({ refusal: 'caminho vazio' }),
      });
    }
    const contained = await resolveContainedPath({
      root: projectRoot,
      target: path.isAbsolute(relative) ? relative : path.resolve(projectRoot, relative),
      ...containmentFs,
      label: 'artefato',
    });
    if (!contained.ok) {
      return Object.freeze({
        path: relative,
        exists: false,
        symlink: false,
        measurement: null,
        readError: null,
        refused: contained.reason,
        comparison: compareWithRecord({ refusal: contained.reason }),
      });
    }
    const projectRelative = path.relative(projectRoot, contained.target).split(path.sep).join('/');
    const exists = await pathExists(contained.target);
    let measurement = null;
    let readError = null;
    if (exists && measure) {
      try {
        const bytes = await fs.readFile(contained.target);
        measurement = measureArtifactBytes(bytes, { filename: path.basename(contained.target), hash, grid });
      } catch (error) {
        readError = String(error?.message ?? error).slice(0, 240);
      }
    }
    return Object.freeze({
      path: projectRelative,
      exists,
      symlink: contained.isSymlink,
      measurement,
      readError,
      refused: null,
      comparison: compareWithRecord({ recorded, measurement, exists, refusal: null }),
    });
  }

  // --------------------------------------- reconciliação assistida de artefatos
  /**
   * Planos de reconciliação emitidos e ainda não confirmados.
   *
   * Ficam em memória de propósito: um token só vale para o processo que mediu o
   * arquivo. Se o app reiniciar, todo plano some e qualquer confirmação é recusada
   * — a revisão que a pessoa viu não pode ser reaproveitada sobre um estado que
   * ninguém voltou a medir.
   */
  const reconciliationLedger = createPlanLedger({ now: () => Date.now() });

  /** Caminho relativo ao projeto, com `/` como separador (forma usada no store). */
  function projectRelativeFrom(value) {
    const raw = String(value ?? '').trim();
    if (!raw) return '';
    const resolved = path.isAbsolute(raw) ? path.resolve(raw) : path.resolve(projectRoot, raw);
    return path.relative(projectRoot, resolved).split(path.sep).join('/');
  }

  /**
   * UID efetivo do processo: o único fato de identidade que o app pode observar.
   *
   * O app não tem contas, perfis nem login, então a auditoria registra isto — e
   * `null` com uma nota quando o sistema não informa. Inventar um nome aqui seria
   * fabricar responsável por uma decisão.
   */
  function currentActorUid() {
    try {
      const info = os.userInfo();
      if (Number.isInteger(info?.uid)) return info.uid;
    } catch {
      // ambientes sem userInfo (host injetado, container restrito) caem no geteuid
    }
    const euid = typeof process.geteuid === 'function' ? process.geteuid() : null;
    return Number.isInteger(euid) ? euid : null;
  }

  /**
   * Lê o store para reconciliar, distinguindo "não existe" de "não é legível".
   *
   * `readStore` devolve `null` nos dois casos, o que aqui seria catastrófico:
   * reconciliar sobre um store ilegível gravaria um registro novo por cima de um
   * que não conseguimos ler. Por isso a leitura falha é recusa explícita.
   */
  async function readStoreForReconciliation() {
    const relativeStore = projectRelativeFrom(storeFile);
    if (!await pathExists(storeFile)) {
      fail('STORE_MISSING', `O projeto ainda não tem registro de assets (${relativeStore}): não há asset nem versão para reconciliar. Nada foi gravado.`);
    }
    let raw;
    try {
      raw = await fs.readFile(storeFile, 'utf8');
    } catch (error) {
      fail('STORE_UNREADABLE', `Não foi possível ler ${relativeStore}: ${String(error?.message ?? error).slice(0, 200)}. O registro não será reescrito a partir de uma leitura falha; nada foi aplicado.`);
    }
    try {
      const parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
        fail('STORE_UNREADABLE', `${relativeStore} não contém um objeto de registro de assets. Nada foi aplicado: reescrever isto destruiria o que está gravado.`);
      }
      return parsed;
    } catch (error) {
      fail('STORE_UNREADABLE', `${relativeStore} existe mas não é JSON válido (${String(error?.message ?? error).slice(0, 160)}). Reescrevê-lo destruiria o registro atual: nada foi aplicado. Restaure ou corrija o arquivo e inspecione de novo.`);
    }
  }

  // ------------------------------------------- leitura sem escrita (comparação)
  /**
   * Lê o registro para as superfícies que **não** escrevem.
   *
   * `readStore()` devolve `null` tanto para "não existe" quanto para "está
   * ilegível". Numa escrita essa ambiguidade é perigosa (daí
   * `readStoreForReconciliation`); numa leitura ela é desonesta de outro jeito:
   * responder "este asset não tem versões" para um store corrompido faria a
   * interface afirmar uma ausência que ninguém verificou. Aqui o estado volta
   * nomeado (`ok` | `missing` | `unreadable`) e a resposta o carrega.
   */
  async function readStoreForRead() {
    const relativeStore = projectRelativeFrom(storeFile);
    if (!await pathExists(storeFile)) {
      return {
        state: 'missing',
        store: null,
        message: `O projeto ainda não tem registro de assets (${relativeStore}): não há versão registrada para comparar.`,
      };
    }
    let raw;
    try {
      raw = await fs.readFile(storeFile, 'utf8');
    } catch (error) {
      return {
        state: 'unreadable',
        store: null,
        message: `Não foi possível ler ${relativeStore}: ${String(error?.message ?? error).slice(0, 200)}. Nada foi comparado e o registro não será reescrito a partir de uma leitura falha.`,
      };
    }
    try {
      const parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
        return {
          state: 'unreadable',
          store: null,
          message: `${relativeStore} não contém um objeto de registro de assets. Nada foi comparado.`,
        };
      }
      return { state: 'ok', store: parsed, message: null };
    } catch (error) {
      return {
        state: 'unreadable',
        store: null,
        message: `${relativeStore} existe mas não é JSON válido (${String(error?.message ?? error).slice(0, 160)}). Nada foi comparado e nada será reescrito aqui.`,
      };
    }
  }

  /**
   * Manager de leitura: o `save` lança.
   *
   * Comparação e busca de duplicatas são consultas. Passar um `save` que falha
   * torna "não escreve no store" uma propriedade estrutural destas superfícies,
   * não apenas uma ausência de chamada — se alguém encadear um `addVersion` aqui
   * no futuro, o teste estoura em vez de gravar escondido.
   */
  async function assetsForRead() {
    const read = await readStoreForRead();
    const manager = createAssetManager({
      store: read.store,
      save: () => {
        throw new Error('Superfície somente leitura: comparação e busca de duplicatas não gravam no registro de assets.');
      },
    });
    return { ...read, manager, assets: manager.list() ?? [] };
  }

  /**
   * Caminhos de artefato que o registro declara (versões atuais e apontamentos
   * anteriores preservados por reconciliação `repoint`).
   *
   * É a fronteira da prévia: o Studio serve bytes de arquivo que o catálogo já
   * expõe, e não de qualquer arquivo do projeto — senão a rota de prévia viraria
   * um servidor de arquivos da pasta do usuário.
   */
  function registeredArtifactPaths(assets) {
    const paths = new Set();
    for (const asset of assets ?? []) {
      for (const version of asset?.versions ?? []) {
        for (const artifact of version?.artifacts ?? []) {
          const declared = projectRelativeFrom(artifact?.path);
          if (declared) paths.add(declared);
          for (const item of artifact?.previous ?? []) {
            const previous = projectRelativeFrom(item?.path);
            if (previous) paths.add(previous);
          }
        }
      }
    }
    return paths;
  }

  /** Valida e normaliza o pedido de reconciliação (plano e confirmação). */
  function normalizeReconciliationRequest(input = {}) {
    const operation = String(input.operation ?? '').trim();
    if (!RECONCILIATION_OPERATIONS.includes(operation)) {
      fail('UNSUPPORTED_OPERATION', `Operação de reconciliação desconhecida: "${operation || '(não informada)'}". As três operações são register-new-version (registrar como nova versão), repoint (apontar o registro para outro arquivo) e mark-superseded (marcar a versão como substituída). Nada foi lido nem gravado.`);
    }
    const assetId = String(input.assetId ?? '').trim();
    if (!assetId) fail('MISSING_ASSET', 'Informe o asset a reconciliar (assetId). Nada foi gravado.');
    const version = String(input.version ?? '').trim();
    if (!version) fail('MISSING_VERSION', `Informe a versão do asset "${assetId}" (version). Nada foi gravado.`);
    const replacedByVersion = String(input.replacedByVersion ?? '').trim();
    return {
      operation,
      assetId,
      version,
      artifactPath: String(input.artifactPath ?? '').trim() || null,
      newPath: String(input.newPath ?? '').trim() || null,
      replacedByVersion: replacedByVersion || null,
      reason: normalizeJustification(input.reason ?? null),
      reviewer: normalizeReviewer(input.reviewer ?? null),
    };
  }

  /**
   * Localiza asset, versão e artefato no store **bruto** (não normalizado), com
   * recusa nomeada em cada nível. Nenhuma reconciliação é aplicada sem os três.
   */
  function locateReconciliationTarget({ store, assetId, version, artifactPath }) {
    const assets = Array.isArray(store?.assets) ? store.assets : [];
    const asset = assets.find((item) => item && item.id === assetId) ?? null;
    if (!asset) {
      fail('ASSET_NOT_FOUND', `O asset "${assetId}" não está no registro do projeto. Assets registrados: ${assets.map((item) => String(item?.id ?? '')).filter(Boolean).join(', ') || 'nenhum'}. Nada foi gravado.`);
    }
    const versions = Array.isArray(asset.versions) ? asset.versions : [];
    const versionRecord = versions.find((item) => String(item?.version ?? '') === version) ?? null;
    if (!versionRecord) {
      fail('VERSION_NOT_FOUND', `A versão "${version}" não existe no asset "${assetId}". Versões registradas: ${versions.map((item) => String(item?.version ?? '(sem rótulo)')).join(', ') || 'nenhuma'}. Nada foi gravado.`);
    }
    const artifacts = Array.isArray(versionRecord.artifacts) ? versionRecord.artifacts : [];
    if (!artifacts.length) {
      fail('ARTIFACT_NOT_FOUND', `A versão "${version}" do asset "${assetId}" não declara artefato nenhum: não há registro para reconciliar. Nada foi gravado.`);
    }
    const wanted = artifactPath ? projectRelativeFrom(artifactPath) : '';
    const artifact = wanted
      ? artifacts.find((item) => projectRelativeFrom(String(item?.path ?? '')) === wanted) ?? null
      : (artifacts.length === 1 ? artifacts[0] : null);
    if (!artifact) {
      fail('ARTIFACT_NOT_FOUND', wanted
        ? `O artefato "${artifactPath}" não está registrado na versão "${version}" do asset "${assetId}". Artefatos registrados: ${artifacts.map((item) => String(item?.path ?? '')).join(', ')}. Nada foi gravado.`
        : `A versão "${version}" do asset "${assetId}" declara ${artifacts.length} artefatos; informe qual reconciliar em artifactPath. Opções: ${artifacts.map((item) => String(item?.path ?? '')).join(', ')}. Nada foi gravado.`);
    }
    return { assets, asset, versions, versionRecord, artifacts, artifact };
  }

  /**
   * Estado medido agora, na forma que o token amarra e que a auditoria preserva.
   * Mede o arquivo registrado e, quando a operação é `repoint`, também o destino.
   */
  async function measureReconciliationState({ artifact, targetPath = null }) {
    const recordedPath = String(artifact?.path ?? '');
    const recorded = recordedSnapshot({
      path: recordedPath,
      sha256: artifact?.sha256 ?? null,
      bytes: artifact?.bytes ?? null,
      format: artifact?.format ?? null,
      validated: artifact?.validated === true,
      validation: artifact?.validation ?? null,
    });
    const inspection = await inspectProjectFile(recordedPath, { recorded, measure: true });
    if (inspection.refused) {
      fail('PATH_REFUSED', `O caminho registrado "${recordedPath}" não pôde ser inspecionado: ${inspection.refused}. Nada foi lido e nada foi gravado.`);
    }
    let targetInspection = null;
    if (targetPath) {
      targetInspection = await inspectProjectFile(targetPath, { recorded: null, measure: true });
    }
    return { recorded, inspection, targetInspection };
  }

  /**
   * Caminho declarado como entrada do usuário, confinado à raiz do projeto.
   *
   * Decisão por **caminho relativo** (`shared/fs/path-containment.mjs`), não por
   * `startsWith`: uma pasta irmã cujo nome começa com o nome da raiz passava no
   * teste de prefixo. A resolução de symlink acontece nos gates assíncronos
   * (`assertPathInsideProject`, `resolveInside`) que já usam o mesmo módulo.
   */
  function absoluteInsideProject(value) {
    if (typeof value !== 'string' || !value.trim()) return null;
    const resolved = path.isAbsolute(value) ? path.resolve(value) : path.resolve(projectRoot, value);
    return isPathContained(path.resolve(projectRoot), resolved) ? resolved : null;
  }

  /**
   * "Asset" no sentido do contrato Blender: nome, tipo (character|item),
   * animações e dimensão alvo. Tudo derivado do plano e das entradas do
   * usuário — nada é inventado sobre o modelo.
   */
  function assetForStep(step, context) {
    const params = { ...(context.params ?? {}), ...(step.params ?? {}) };
    const capability = String(step.capability ?? '');
    const workflow = String(context.studioWorkflowId ?? context.workflowId ?? '');
    const type = params.assetType === 'item' || params.assetType === 'character'
      ? params.assetType
      : capability === 'render3d.to2d' || workflow.includes('character')
        ? 'character'
        : 'item';
    const animations = Array.isArray(params.animations) && params.animations.length
      ? params.animations.filter((value) => typeof value === 'string' && value.trim()).slice(0, 8)
      : [...DEFAULT_ANIMATIONS];
    return {
      name: String(params.assetName ?? params.name ?? context.brief?.title ?? type).slice(0, 120),
      type,
      animations,
      target: String(params.frameSize ?? params.target ?? '48x48').slice(0, 12),
    };
  }

  async function resolveModelInput({ step, context, inputsById, runOutputs }) {
    const params = { ...(context.params ?? {}), ...(step.params ?? {}) };
    const declared = [params.model, params.modelPath, params.inputPath, params.source, context.modelPath]
      .map((value) => absoluteInsideProject(value))
      .filter(Boolean);
    if (declared.length) {
      for (const candidate of declared) {
        try { await fs.access(candidate); return candidate; } catch { /* tenta o próximo */ }
      }
      return null;
    }
    const produced = [...Object.values(inputsById ?? {}), ...Object.values(runOutputs ?? {})]
      .flatMap((entry) => (Array.isArray(entry?.outputs) ? entry.outputs : []))
      .filter(isModelPath)
      .map((value) => absoluteInsideProject(value))
      .filter(Boolean);
    if (!produced.length) return null;
    // A prioridade de formato/estágio já testada no adapter legado é reaproveitada.
    const best = host.findModelInput?.({ existingInputs: produced.map((value) => ({ path: value, stageIndex: 3 })) }) ?? produced[0];
    try { await fs.access(best); return best; } catch { return null; }
  }

  async function prepareStepContext({ step, context, inputsById, runOutputs, runDirectory }) {
    const providers = providerCache ?? (await providersNow()).providers;
    const blender = providers.blender;
    const enriched = { ...context };
    const outputDirectory = path.join(runDirectory, 'steps', String(step.id));
    await fs.mkdir(outputDirectory, { recursive: true });
    enriched.outputDirectory = outputDirectory;
    enriched.asset = assetForStep(step, context);
    if (step.adapter === 'comfyui-concept' || step.adapter === 'comfyui-remote') {
      // Difusão: o texto vem do usuário (brief ou campo prompt) e o checkpoint
      // vem do provider escolhido — nada é baixado aqui.
      const params = { ...(context.params ?? {}), ...(step.params ?? {}) };
      const briefText = typeof context.brief === 'string' ? context.brief.trim() : '';
      enriched.prompt = params.prompt ?? (briefText.length >= 12 ? briefText.slice(0, 8000) : null);
      enriched.checkpoint = params.checkpoint ?? providers.comfyui.checkpoint ?? null;
      enriched.workflowId = params.workflowId ?? providers.comfyui.workflowId ?? null;
      enriched.asset = enriched.asset ?? assetForStep(step, context);
      if (step.adapter === 'comfyui-remote') {
        enriched.endpoint = providers.comfyui.endpoint ?? null;
        enriched.credentialRef = providers.comfyui.credentialRef ?? null;
        enriched.maxCostUnits = providers.comfyui.maxCostUnits ?? null;
        enriched.authorization = providers.comfyui.authorization ?? { granted: false };
      }
    }
    if (step.adapter === 'blender-spritesheet') {
      // O contrato do Blender é específico: script, dimensões como objeto e o
      // caminho do modelo. Nada disso é imposto aos outros adapters — o rig2d,
      // por exemplo, espera `frameSize` como texto "48x48".
      enriched.scriptPath = blender.scriptPath ?? host.blenderScriptPath;
      enriched.frameSize = host.parseFrameSize?.(blender.frameSize) ?? { width: 48, height: 48 };
      enriched.projectRoot = projectRoot;
    }
    // Id do workflow do Studio (não confundir com o template do ComfyUI, que
    // vive em `workflowId` e vem do provider escolhido).
    enriched.studioWorkflowId = context.workflowId ?? null;
    const model = await resolveModelInput({ step, context, inputsById, runOutputs });
    if (model) {
      enriched.inputPath = model;
      const relative = path.relative(projectRoot, model).split(path.sep).join('/');
      enriched.inputsById = { ...(inputsById ?? {}), 'animated-model': { outputs: [relative], path: relative, sha256: null } };
    }
    return enriched;
  }

  const managerCache = new Map();

  /**
   * Execuções em andamento **neste processo**. É o que permite cancelar um run
   * de verdade: sem este registro, o sinal de cancelamento não tem para quem
   * ir e o produto só poderia mentir ("cancelado") sem parar nada.
   */
  const activeRuns = new Map();
  /** Pedidos de cancelamento: quem cancelou e por quê fica gravado no run. */
  const cancellationRequests = new Map();

  function managerFor(runId) {
    if (!managerCache.has(runId)) {
      const runDirectory = path.join(projectRoot, RUNS_DIRECTORY, runId);
      managerCache.set(runId, new ExecutionManager({
        resolveAdapter: async (adapterId) => (await currentAdapters()).adapter(adapterId),
        prepareContext: (args) => prepareStepContext({ ...args, runDirectory }),
        persist: async (snapshot) => {
          await fs.mkdir(runDirectory, { recursive: true });
          await fs.writeFile(path.join(runDirectory, 'run.json'), `${JSON.stringify(snapshot, null, 2)}\n`, 'utf8');
        },
        limits,
        validateStep: validateStepOutputs,
      }));
    }
    return managerCache.get(runId);
  }

  return Object.freeze({
    schemaVersion: STUDIO_SERVICE_SCHEMA_VERSION,
    projectRoot,
    workflowIds: WORKFLOW_IDS,

    async overview() {
      const { hub, machine } = await discover();
      const [preflight, assetManager] = [await runPreflight({ registry, adapters: (await currentAdapters()).all(), machine }), await assets()];
      return Object.freeze({
        schemaVersion: STUDIO_SERVICE_SCHEMA_VERSION,
        machine,
        capabilities: registry.list().map((capability) => ({
          id: capability.id,
          family: capability.family,
          title: capability.title,
          status: capability.status,
          description: capability.description,
          requirements: capability.requirements,
          evidence: capability.evidence,
          limitations: capability.limitations,
        })),
        capabilityStates: hub.capabilityStates(),
        adapters: (await currentAdapters()).describe(),
        providers: await providerStates(),
        preflight: Object.freeze({ summary: preflight.summary, userActions: preflight.userActions, tools: preflight.tools }),
        workflows: listWorkflows({ hub, registry }),
        destinations: listDestinations(),
        // `versions` é a contagem (formato publicado e consumido pela interface);
        // `versionRunIds` diz de quais runs cada versão veio — sem isso o roteiro
        // não tem como saber se o resultado em foco foi guardado no projeto.
        assets: assetManager.list().map((asset) => ({
          id: asset.id,
          name: asset.name,
          type: asset.type,
          versions: asset.versions.length,
          versionRunIds: (asset.versions ?? []).map((version) => version.runId ?? null).filter(Boolean),
          rights: asset.rights.state,
        })),
        rights: assetManager.rightsReport(),
        note: 'Nenhuma ferramenta foi instalada, baixada ou contatada; nenhum probe de GPU foi executado.',
      });
    },

    async capabilities() {
      return registry.list();
    },

    /** Providers configurados + estado real de cada um. */
    async providers() {
      return providerStates();
    },

    /** Altera um provider (modo, endpoint, checkpoint, caminho do Blender…). */
    async configureProvider(input) {
      const result = await providerStore.configure(input);
      adaptersInstance = null;
      adaptersKey = null;
      providerCache = null;
      return { ...result, providers: await providerStates() };
    },

    async adapterManifests() {
      return (await currentAdapters()).manifests();
    },

    async preflight({ capabilityIds = null } = {}) {
      const machine = await machineInfo();
      return runPreflight({ registry, adapters: (await currentAdapters()).all(), machine, capabilityIds });
    },

    async workflows() {
      const { hub } = await discover();
      return listWorkflows({ hub, registry });
    },

    async plan({ workflowId, destination = null, options: planOptions = {}, brief = null, allowRemote = false }) {
      const { hub, machine } = await discover();
      const plan = planWorkflow({ workflowId, hub, registry, destination, options: planOptions, brief, allowRemote });
      return Object.freeze({ plan, machine, hubStates: hub.capabilityStates() });
    },

    /**
     * Executa um plano. Só adapters internos rodam sem ferramenta externa;
     * passos bloqueados permanecem bloqueados e o run registra o motivo.
     */
    async run({ workflowId, destination = null, options: runOptions = {}, brief = null, params = {}, authorization = null, costCeiling = null, onEvent = null, signal = null, resume = null }) {
      const runId = resume?.runId ?? `run-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
      // Cancelamento cooperativo: o engine recebe este signal e para no próximo
      // ponto de verificação. Um signal externo (do hospedeiro) é encadeado.
      const controller = new AbortController();
      const forwardAbort = () => controller.abort(signal?.reason ?? new Error('Execução cancelada pelo chamador.'));
      if (signal) {
        if (signal.aborted) forwardAbort();
        else signal.addEventListener('abort', forwardAbort, { once: true });
      }
      activeRuns.set(runId, Object.freeze({
        controller,
        runId,
        workflowId,
        startedAt: new Date().toISOString(),
        resumed: Boolean(resume),
      }));
      const runDirectory = path.join(projectRoot, RUNS_DIRECTORY, runId);
      // Run anterior reaproveitado como entrada (rig/partes já revisados).
      const fromRun = params.fromRun ?? runOptions.fromRun ?? null;
      if (fromRun !== null) {
        // Id de run é nome de pasta: recusar separadores e ".." aqui impede que
        // uma entrada digitada na UI vire leitura fora de .lia-forge/runs/.
        const value = String(fromRun);
        if (!/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(value) || value.includes('..')) {
          throw new Error('run: fromRun inválido — use o id de um run existente em .lia-forge/runs/ (sem caminhos).');
        }
      }
      const priorRunDirectory = fromRun ? path.join(projectRoot, RUNS_DIRECTORY, String(fromRun)) : null;
      let plan = null;
      try {
      const { hub, machine } = await discover();
      // Entradas fornecidas pelo usuário (`params.model`, `params.fromRun`…) são
      // promovidas a opções do plano: é por elas que o Orquestrador decide se um
      // passo tem o que precisa, e é por elas que o valor chega ao adapter — o
      // engine substitui `context.params` pelos params do passo planejado.
      const RESERVED_PARAMS = new Set(['reviews', 'sourceImage']);
      const userInputOptions = Object.fromEntries(Object.entries(params)
        .filter(([key, value]) => !RESERVED_PARAMS.has(key) && ['string', 'number', 'boolean'].includes(typeof value)));
      const planOptions = { ...userInputOptions, ...runOptions, ...(fromRun ? { fromRun } : {}) };
      plan = planWorkflow({ workflowId, hub, registry, destination, options: planOptions, brief });
      const hashes = new Map();
      const emit = await emitFor(runDirectory, hashes);
      const manager = managerFor(runId);
      await fs.mkdir(runDirectory, { recursive: true });
      // O que originou este run fica gravado: a retomada precisa das mesmas
      // entradas (run de origem, imagem de entrada) para não perder o contexto
      // que só existia na primeira execução. Segredos são redigidos.
      const origin = {
        workflowId,
        destination,
        brief,
        options: fromRun ? { ...runOptions, fromRun } : { ...runOptions },
        params: Object.fromEntries(Object.entries(params)
          .filter(([key]) => key !== 'reviews')
          .map(([key, value]) => [key, typeof value === 'string' ? redactSecrets(value) : value])),
      };
      await fs.writeFile(path.join(runDirectory, 'plan.json'), `${JSON.stringify({ ...origin, plan }, null, 2)}\n`, 'utf8');

      const readArtifact = async (relativePath) => {
        const candidates = [path.join(runDirectory, relativePath)];
        // artefatos do run de origem, quando este run reaproveita um resultado
        if (priorRunDirectory) candidates.push(path.join(priorRunDirectory, relativePath));
        candidates.push(path.join(projectRoot, relativePath));
        for (const absolute of candidates) {
          // Confinamento (auditoria P0, item 2): nada é lido fora da raiz do
          // projeto, e a conferência é por caminho relativo + caminho real
          // (symlink dentro do projeto apontando para fora não é lido).
          const contained = await resolveContainedPath({
            root: projectRoot,
            target: absolute,
            ...containmentFs,
            label: 'artefato de origem',
          });
          if (!contained.ok) continue;
          try {
            return await fs.readFile(contained.target);
          } catch {
            /* tenta o próximo candidato */
          }
        }
        return null;
      };

      const context = {
        projectRoot,
        workflowId,
        outputDirectory: runDirectory,
        emit,
        machine,
        destination,
        brief,
        params,
        reviews: params.reviews ?? {},
        // Adapters externos (Blender, ComfyUI) gravam no disco por conta própria,
        // sem passar pelo `emit`. O hash ainda precisa existir: é o que ancora o
        // gate de revisão (SHA-256) e a detecção de entrada alterada.
        hashArtifact: async (relativePath) => {
          const direct = hashes.get(relativePath)
            ?? hashes.get(path.relative(runDirectory, path.join(projectRoot, relativePath)));
          if (direct) return direct;
          const bytes = await context.readArtifact(relativePath);
          return bytes ? hash(bytes) : null;
        },
        // bolsa de dados entre passos do mesmo run (partes → rig → animação)
        state: {},
        // leitura confinada ao projeto: aceita caminho relativo ao run ou ao
        // projeto, e devolve null quando o arquivo não existe
        readArtifact,
      };

      if (fromRun) {
        const previous = await this.readRun(fromRun);
        if (!previous) throw new Error(`run: o run anterior "${fromRun}" não foi encontrado em .lia-forge/runs/`);
        context.priorOutputs = Object.fromEntries((previous.steps ?? [])
          .filter((step) => step.outputs?.length)
          .map((step) => [step.id, { outputs: step.outputs, sha256: step.sha256 ?? null }]));
      }

      // Imagem de entrada declarada pelo usuário (caminho relativo ao projeto).
      const sourceImage = params.sourceImage ?? runOptions.sourceImage ?? null;
      if (sourceImage) {
        const bytes = await context.readArtifact(sourceImage);
        if (!bytes) throw new Error(`run: imagem de entrada "${sourceImage}" não encontrada dentro do projeto`);
        const decoded = decodePng(bytes);
        context.image = decoded;
        context.state.image = decoded;
        context.state.partImages = null;
      }

      // Autorização por run (P0-2): o escopo é derivado do plano REAL deste run e
      // a autorização da pessoa é vinculada a ele por fingerprint. Sem `scope` o
      // gate do engine nem rodava — era o que fazia `authorization` ser decorativo.
      // Na retomada, o escopo autorizado é o gravado no run: se o plano mudou, o
      // fingerprint muda e o run bloqueia pedindo autorização de novo.
      const scope = resume?.scope ?? buildRunScope(plan, {
        destination,
        inputs: context.inputs ?? {},
        costCeiling,
      });
      const requiresAuthorization = scopeRequiresAuthorization(scope);
      // Retomada: a autorização que vale é a gravada no run.json deste run, não
      // uma nova decisão inventada aqui. Ela é vinculada por fingerprint ao escopo
      // RECALCULADO a partir do plano atual — se o plano mudou (adapter novo,
      // destino diferente, entrada trocada, ação protegida a mais), o fingerprint
      // não bate e o engine bloqueia pedindo autorização de novo.
      let requestedAuthorization = resume?.authorization ?? authorization;
      if (!requestedAuthorization && resume) {
        requestedAuthorization = await fs.readFile(path.join(runDirectory, 'run.json'), 'utf8')
          .then((text) => JSON.parse(text)?.authorization ?? null)
          .catch(() => null);
      }
      const boundAuthorization = authorizationForScope(scope, requestedAuthorization);
      const uncoveredActions = requiresAuthorization
        ? missingProtectedActions(scope, boundAuthorization)
        : [];
      if (requiresAuthorization && (!boundAuthorization || uncoveredActions.length > 0)) {
        // Fail-closed antes de executar qualquer passo: o run fica gravado como
        // bloqueado com o motivo e o fingerprint que a pessoa precisa autorizar.
        const gate = checkAuthorization({
          scope: { ...scope, plan: plan.steps.map((step) => step.id) },
          authorization: uncoveredActions.length > 0 ? boundAuthorization : null,
        });
        const blockedSnapshot = await manager.execute(plan, {
          context,
          scope,
          authorization: { granted: false },
          signal: controller.signal,
          onEvent,
          runId,
          resume: false,
          checkpoints: null,
        });
        return Object.freeze({
          runId,
          plan,
          snapshot: blockedSnapshot,
          runDirectory: path.relative(projectRoot, runDirectory),
          authorizationRequired: true,
          authorizationScope: scope,
          authorizationFingerprint: gate.fingerprint,
          authorizationReason: uncoveredActions.length > 0
            ? `Autorização incompleta: as ações protegidas ${uncoveredActions.join(', ')} deste run não foram concedidas. Nada foi executado.`
            : gate.reason,
          missingProtectedActions: Object.freeze(uncoveredActions),
        });
      }
      const snapshot = await manager.execute(plan, {
        context,
        scope,
        authorization: boundAuthorization,
        // O signal interno é o que `cancelRun` aborta; o signal do chamador
        // (quando existe) foi encadeado nele acima.
        signal: controller.signal,
        onEvent,
        // o id do run é decidido aqui: é o nome da pasta em .lia-forge/runs/
        runId,
        resume: Boolean(resume),
        checkpoints: resume?.checkpoints ?? null,
      });
      // O motivo e a autoria do cancelamento não existem dentro do engine: são
      // gravados aqui, sobre o snapshot final, para o histórico do run dizer quem
      // parou a execução e por quê (com segredos redigidos).
      const cancellation = cancellationRequests.get(runId) ?? null;
      if (cancellation && snapshot.status === 'cancelled') {
        const entry = {
          at: cancellation.at,
          level: 'warn',
          message: `Execução cancelada por ${cancellation.cancelledBy}: ${cancellation.reason}`,
          details: { code: 'WORKFLOW_CANCELLED', cancelledBy: cancellation.cancelledBy },
        };
        const recorded = { ...snapshot, cancellation, logs: [...(snapshot.logs ?? []), entry] };
        await fs.writeFile(path.join(runDirectory, 'run.json'), `${JSON.stringify(recorded, null, 2)}\n`, 'utf8').catch(() => {});
        return Object.freeze({
          runId,
          plan,
          snapshot: Object.freeze(recorded),
          runDirectory: path.relative(projectRoot, runDirectory),
          authorizationRequired: requiresAuthorization,
          authorizationScope: scope,
          authorizationFingerprint: recorded.planFingerprint ?? null,
        });
      }
      return Object.freeze({
        runId,
        plan,
        snapshot,
        runDirectory: path.relative(projectRoot, runDirectory),
        authorizationRequired: requiresAuthorization,
        authorizationScope: scope,
        authorizationFingerprint: snapshot.planFingerprint ?? null,
      });
      } catch (error) {
        // Falha antes de qualquer passo executar (entrada inexistente, plano
        // inválido…): o run ainda assim existe, fica gravado e explica o motivo
        // — com segredos redigidos, como em qualquer outro log.
        const message = redactSecrets(error?.message ?? String(error));
        const at = new Date().toISOString();
        const failed = {
          schemaVersion: STUDIO_SERVICE_SCHEMA_VERSION,
          runId,
          planId: plan?.id ?? workflowId,
          planTitle: plan?.title ?? workflowId,
          status: 'failed',
          startedAt: at,
          finishedAt: at,
          steps: (plan?.steps ?? []).map((step) => ({ id: step.id, adapter: step.adapter, state: 'pending', outputs: [], error: null })),
          gates: [],
          logs: [{ at, level: 'error', message, details: { code: error?.code ?? null } }],
          provenance: [],
          cost: { status: 'unknown', entries: [], total: null, currency: null },
          summary: { total: plan?.steps?.length ?? 0, progress: 0, finished: true, failed: [], blocked: [] },
          error: { code: error?.code ?? 'WORKFLOW_FAILED', message },
        };
        await fs.mkdir(runDirectory, { recursive: true }).catch(() => {});
        await fs.writeFile(path.join(runDirectory, 'run.json'), `${JSON.stringify(failed, null, 2)}\n`, 'utf8').catch(() => {});
        return Object.freeze({ runId, plan, snapshot: failed, runDirectory: path.relative(projectRoot, runDirectory) });
      } finally {
        activeRuns.delete(runId);
        cancellationRequests.delete(runId);
        if (signal) signal.removeEventListener('abort', forwardAbort);
      }
    },

    /** Execuções em andamento neste processo (para a interface offrir cancelar). */
    activeRuns() {
      return activeRuns.size
        ? [...activeRuns.values()].map((item) => Object.freeze({ runId: item.runId, workflowId: item.workflowId, startedAt: item.startedAt, resumed: item.resumed }))
        : [];
    },

    /**
     * Cancela um run em andamento. Três casos, todos ditos com clareza:
     *
     * 1. está em execução neste processo → envia o sinal e o engine grava `cancelled`;
     * 2. terminou → nada é alterado e o estado real é devolvido;
     * 3. aparece como `running` mas não está neste processo (o aplicativo foi
     *    fechado, por exemplo) → o estado é gravado como cancelado **com a marca
     *    de execução ausente**: o produto não finge que parou algo que não parou.
     */
    async cancelRun({ runId, reason = 'cancelado pelo usuário', cancelledBy = 'usuario' } = {}) {
      const id = String(runId ?? '').trim();
      if (!/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(id) || id.includes('..')) {
        throw new Error('cancelRun: runId inválido — use o id de um run em .lia-forge/runs/ (sem caminhos).');
      }
      const text = redactSecrets(String(reason));
      const at = new Date().toISOString();
      const active = activeRuns.get(id);
      if (active) {
        cancellationRequests.set(id, { reason: text, cancelledBy: String(cancelledBy), at });
        active.controller.abort(new Error(text));
        return Object.freeze({
          ok: true,
          runId: id,
          status: 'cancelling',
          cancelledBy: String(cancelledBy),
          reason: text,
          note: 'Sinal de cancelamento enviado: o passo em andamento para no próximo ponto de verificação e o run é gravado como cancelado.',
        });
      }
      const file = path.join(projectRoot, RUNS_DIRECTORY, id, 'run.json');
      if (!await pathExists(file)) throw new Error(`cancelRun: run "${id}" não encontrado em .lia-forge/runs/`);
      const stored = JSON.parse(await fs.readFile(file, 'utf8'));
      if (!['running', 'planned', 'paused'].includes(stored.status)) {
        return Object.freeze({
          ok: false,
          runId: id,
          status: stored.status,
          reason: `O run já estava encerrado como "${stored.status}"; nada foi alterado.`,
        });
      }
      const cancelled = {
        ...stored,
        status: 'cancelled',
        finishedAt: at,
        cancelled: { reason: text, cancelledBy: String(cancelledBy), at, executionPresent: false },
        steps: (stored.steps ?? []).map((step) => (['pending', 'running', 'queued'].includes(step.state)
          ? { ...step, state: 'cancelled', error: { code: 'WORKFLOW_CANCELLED', message: text } }
          : step)),
        logs: [...(stored.logs ?? []), {
          at,
          level: 'warn',
          message: `Run marcado como cancelado sem execução neste processo: ${text}`,
          details: { executionPresent: false },
        }],
        summary: { ...(stored.summary ?? {}), finished: true },
      };
      const temporary = `${file}.${process.pid}.${randomUUID()}.tmp`;
      await fs.writeFile(temporary, `${JSON.stringify(cancelled, null, 2)}\n`, { encoding: 'utf8', flag: 'wx' });
      await fs.rename(temporary, file);
      return Object.freeze({
        ok: true,
        runId: id,
        status: 'cancelled',
        stale: true,
        cancelledBy: String(cancelledBy),
        reason: text,
        note: 'Não havia execução neste processo (o aplicativo pode ter sido fechado). O estado gravado foi corrigido para cancelado; checkpoints de passos concluídos continuam válidos para retomada.',
      });
    },

    /**
     * Retoma um run interrompido (cancelado, pausado, bloqueado ou falho) a
     * partir dos checkpoints válidos, com as **mesmas entradas originais** e as
     * revisões já gravadas — sem elas o gate de revisão seria perdido.
     */
    async resumeRun({ runId, reason = null } = {}) {
      const id = String(runId ?? '').trim();
      if (!/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(id) || id.includes('..')) {
        throw new Error('resumeRun: runId inválido — use o id de um run em .lia-forge/runs/ (sem caminhos).');
      }
      if (activeRuns.has(id)) throw new Error(`resumeRun: o run "${id}" ainda está em execução neste processo; cancele antes de retomar.`);
      const snapshot = await this.readRun(id);
      if (!snapshot) throw new Error(`resumeRun: run "${id}" não encontrado em .lia-forge/runs/`);
      // Run gravado como em andamento sem execução neste processo (o aplicativo
      // foi fechado, a máquina reiniciou): os checkpoints estão no disco e a
      // retomada é exatamente o que o usuário espera do botão "Retomar".
      const interrupted = ['running', 'planned'].includes(snapshot.status) && !activeRuns.has(id);
      if (!interrupted && !isResumableRunState(snapshot.status)) {
        return Object.freeze({ ok: false, runId: id, status: snapshot.status, reason: `Run "${snapshot.status}" não precisa de retomada.` });
      }
      const runDirectory = path.join(projectRoot, RUNS_DIRECTORY, id);
      const planFile = path.join(runDirectory, 'plan.json');
      if (!await pathExists(planFile)) {
        throw new Error(`resumeRun: o plano original do run "${id}" não foi encontrado; sem ele não há como retomar com as mesmas entradas.`);
      }
      const stored = JSON.parse(await fs.readFile(planFile, 'utf8'));
      const reviews = await fs.readFile(path.join(runDirectory, 'reviews.json'), 'utf8')
        .then((text) => JSON.parse(text))
        .catch(() => ({}));
      const checkpoints = Object.fromEntries((snapshot.steps ?? [])
        .filter((step) => step.state === 'succeeded')
        .map((step) => [step.id, { stepId: step.id, adapter: step.adapter, outputs: step.outputs, sha256: step.sha256, finishedAt: step.finishedAt }]));
      const resumed = await this.run({
        workflowId: stored.workflowId,
        destination: stored.destination,
        brief: stored.brief,
        options: stored.options ?? {},
        params: { ...(stored.params ?? {}), reviews },
        // `authorization` não é passada de propósito: o run usa a que está gravada
        // no run.json dele, revalidada contra o escopo recalculado.
        resume: { runId: id, checkpoints },
      });
      return Object.freeze({
        ok: true,
        runId: id,
        resumedFrom: snapshot.status,
        interrupted,
        checkpointsReused: Object.keys(checkpoints).length,
        reason: reason ? redactSecrets(String(reason)) : null,
        result: resumed.snapshot,
      });
    },

    /**
     * Revisão humana de um passo (12 passos do produto: aprovar/rejeitar).
     *
     * Aprovar grava a decisão sobre o SHA-256 do artefato real e retoma o run a
     * partir dos checkpoints válidos — o passo revisado não é reexecutado.
     * Rejeitar marca o passo como reprovado e o run permanece bloqueado.
     */
    async reviewStep({ runId, stepId, approved, reviewer = 'usuario', note = null }) {
      const snapshot = await this.readRun(runId);
      if (!snapshot) throw new Error(`reviewStep: run "${runId}" não encontrado`);
      const step = snapshot.steps.find((item) => item.id === stepId);
      if (!step) throw new Error(`reviewStep: passo "${stepId}" não existe no run "${runId}"`);
      const planFile = path.join(projectRoot, RUNS_DIRECTORY, runId, 'plan.json');
      const stored = JSON.parse(await fs.readFile(planFile, 'utf8'));
      const decision = {
        approved: approved === true,
        sha256: step.sha256 ?? null,
        reviewer,
        reviewedAt: new Date().toISOString(),
        note: note ? redactSecrets(note) : null,
      };
      const reviewsFile = path.join(projectRoot, RUNS_DIRECTORY, runId, 'reviews.json');
      const reviews = await fs.readFile(reviewsFile, 'utf8').then((text) => JSON.parse(text)).catch(() => ({}));
      // Decisão humana é proveniência: rejeitar e depois aprovar não pode apagar a
      // rejeição (foi ela que disse o que estava errado). O mapa continua com a
      // decisão atual — é o que o gate lê — e o histórico vai ao lado.
      const previous = reviews[stepId] ?? null;
      const history = previous
        ? [...(previous.history ?? []), {
          approved: previous.approved === true,
          sha256: previous.sha256 ?? null,
          reviewer: previous.reviewer ?? null,
          reviewedAt: previous.reviewedAt ?? null,
          note: previous.note ?? null,
        }]
        : [];
      reviews[stepId] = history.length ? { ...decision, history } : decision;
      await fs.writeFile(reviewsFile, `${JSON.stringify(reviews, null, 2)}\n`, 'utf8');
      if (!approved) {
        return Object.freeze({ runId, stepId, decision, resumed: false, reason: 'Passo rejeitado pelo revisor; o run permanece bloqueado.' });
      }
      if (!decision.sha256) {
        return Object.freeze({ runId, stepId, decision, resumed: false, reason: 'O passo não produziu artefato com hash; nada a retomar.' });
      }
      const checkpoints = Object.fromEntries(snapshot.steps
        .filter((item) => item.state === 'succeeded' || item.id === stepId)
        .map((item) => [item.id, { stepId: item.id, adapter: item.adapter, outputs: item.outputs, sha256: item.sha256, finishedAt: item.finishedAt }]));
      const resumed = await this.run({
        workflowId: stored.workflowId,
        destination: stored.destination,
        brief: stored.brief,
        options: stored.options ?? {},
        // entradas originais + revisões: sem isso a retomada perde o run de
        // origem (rig já revisado) e a imagem de entrada declarada pelo usuário
        params: { ...(stored.params ?? {}), reviews },
        resume: { runId, checkpoints },
      });
      return Object.freeze({ runId, stepId, decision, resumed: true, result: resumed.snapshot });
    },

    /**
     * Lista os runs gravados. Dois campos a mais dizem a verdade sobre a
     * execução: `active` (está rodando neste processo agora) e `stale` (o
     * arquivo diz que está em andamento, mas não há execução aqui — o aplicativo
     * foi fechado, por exemplo). Sem isso, um run interrompido ficaria para
     * sempre "em andamento" na interface.
     *
     * `stale` cobre só `running`/`planned`, que são os estados que **contradizem**
     * a realidade quando não há execução neste processo — os mesmos que
     * `resumeRun` reporta como `interrupted: true`. `paused` fica de fora: é o
     * estado que o engine grava quando a execução terminou com passos pendentes
     * (sem falha, bloqueio ou cancelamento), ou seja, um registro verdadeiro de
     * uma parada, não uma mentira a corrigir. Tratá-lo como interrompido fazia a
     * lista oferecer "Corrigir estado" — que grava `cancelled` com o motivo "não
     * havia execução neste processo" — para um run cujo estado já estava certo, e
     * ainda contradizia `resumeRun`, que responde `interrupted: false` para ele.
     */
    async listRuns() {
      const root = path.join(projectRoot, RUNS_DIRECTORY);
      if (!await pathExists(root)) return [];
      const entries = await fs.readdir(root, { withFileTypes: true });
      const running = new Set(activeRuns.keys());
      const unfinished = new Set(['running', 'planned']);
      const runs = [];
      for (const entry of entries) {
        if (!entry.isDirectory()) continue;
        const file = path.join(root, entry.name, 'run.json');
        if (!await pathExists(file)) continue;
        try {
          const snapshot = JSON.parse(await fs.readFile(file, 'utf8'));
          const runId = snapshot.runId ?? entry.name;
          const active = running.has(runId);
          runs.push({
            runId,
            planId: snapshot.planId,
            planTitle: snapshot.planTitle,
            status: snapshot.status,
            startedAt: snapshot.startedAt,
            finishedAt: snapshot.finishedAt,
            summary: snapshot.summary,
            active,
            stale: !active && unfinished.has(snapshot.status),
            // Retomar precisa do plano original gravado: sem ele o serviço recusa
            // (e a interface não pode oferecer um botão que devolve erro).
            planStored: await pathExists(path.join(root, entry.name, 'plan.json')),
          });
        } catch {
          runs.push({ runId: entry.name, status: 'unreadable', active: false, stale: false });
        }
      }
      return runs.sort((a, b) => String(b.startedAt ?? '').localeCompare(String(a.startedAt ?? '')));
    },

    /**
     * Lê o run gravado e traz junto as decisões humanas de `reviews.json`.
     *
     * Sem isso a interface não tem como mostrar quem aprovou o quê: quando a
     * retomada reaproveita o passo do checkpoint, o snapshot novo vem sem o campo
     * `review` e a aprovação que destravou o run fica invisível — assim como uma
     * rejeição anterior, que é justamente o registro do que estava errado.
     *
     * Regra de honestidade: um gate pendente **agora** vale mais do que a decisão
     * gravada antes. Se o passo está de novo esperando revisão (o artefato mudou,
     * por exemplo), ele não aparece como aprovado; a decisão antiga vai em
     * `review.recorded`, com `matchesArtifact` dizendo se ela vale para o conteúdo
     * atual do passo.
     */
    async readRun(runId) {
      const directory = path.join(projectRoot, RUNS_DIRECTORY, String(runId));
      const file = path.join(directory, 'run.json');
      if (!await pathExists(file)) return null;
      const snapshot = JSON.parse(await fs.readFile(file, 'utf8'));
      const reviews = await fs.readFile(path.join(directory, 'reviews.json'), 'utf8')
        .then((text) => JSON.parse(text))
        .catch(() => null);
      if (!reviews || typeof reviews !== 'object' || !Array.isArray(snapshot?.steps)) return snapshot;
      const steps = snapshot.steps.map((step) => {
        const decision = reviews[step.id];
        if (!decision || typeof decision !== 'object') return step;
        const matchesArtifact = decision.sha256 && step.sha256 ? decision.sha256 === step.sha256 : null;
        const recorded = { ...decision, matchesArtifact };
        const current = step.review ?? null;
        if (current && current.status !== 'approved') return { ...step, review: { ...current, recorded } };
        return {
          ...step,
          review: {
            status: decision.approved === true ? 'approved' : 'rejected',
            reviewedBy: decision.reviewer ?? null,
            reviewedAt: decision.reviewedAt ?? null,
            sha256: decision.sha256 ?? null,
            note: decision.note ?? null,
            history: decision.history ?? [],
            matchesArtifact,
            reason: decision.approved === true ? null : 'Rejeitado pelo revisor; o run permanece bloqueado.',
          },
        };
      });
      return { ...snapshot, steps, reviews };
    },

    /** Preview de VFX para a interface (PNG em base64, limitado a 6 MB). */
    async vfxPreview({ preset = 'explosion', size = 96, frameCount = 8, seed = 'lia-forge', palette = null, columns = null } = {}) {
      const generated = generateVfxAtlas({ preset, size, frameCount, seed, palette, columns });
      const png = encodePngRgba(generated.atlas.image.rgba, generated.atlas.image.width, generated.atlas.image.height);
      if (png.length > MAX_PREVIEW_BYTES) throw new Error('Preview excede o limite de 6 MB; reduza size ou frameCount.');
      return Object.freeze({
        preset,
        seed: generated.seed,
        frameCount: generated.frameCount,
        grid: { columns: generated.atlas.columns, rows: generated.atlas.rows },
        sheetWidth: generated.atlas.sheetWidth,
        sheetHeight: generated.atlas.sheetHeight,
        deterministic: generated.deterministic,
        content: analyzePngContent(png),
        pngBase64: png.toString('base64'),
        sha256: hash(png),
      });
    },

    /** Exporta artefatos de um run para um destino (perfil + SHA-256 + notas). */
    /**
     * Exporta o pacote de um run para um destino.
     *
     * Gates (P0-3 da revisão integrada). Antes desta correção `exportRun` não
     * consultava direitos, estado do run nem revisão pendente: um asset com
     * licença declarada como desconhecida (`NOASSERTION` ⇒ estado
     * `license-pending`) era exportado normalmente — medido antes de corrigir.
     * Direitos existem no modelo (`classifyRights` já calcula `redistributable`),
     * só não eram gate.
     *
     *   1. run concluído: `failed`/`cancelled`/`blocked`/`running` não exportam.
     *      Exportar artefato de run que não terminou é entregar conteúdo que o
     *      produto não garante;
     *   2. nenhuma revisão pendente nem revisão sobre hash diferente: a revisão
     *      humana vale para os bytes que a pessoa viu;
     *   3. direitos: se algum asset vinculado a este run (o `asset` informado ou
     *      os que têm proveniência deste runId) não é redistribuível
     *      (`restricted`, `blocked`, `license-pending`, `unknown`), a exportação
     *      é recusada com o estado e os bloqueios nomeados.
     *
     * Quando nenhum asset está vinculado não há declaração nenhuma para conferir:
     * a exportação segue, mas o manifesto grava `rights: null` e a resposta diz
     * `rightsState: 'not-declared'`. Não é "liberado" — é "nada foi declarado",
     * e quem recebe o pacote vê isso.
     */
    async exportRun({ runId, destination, asset = null }) {
      const snapshot = await this.readRun(runId);
      if (!snapshot) throw new Error(`exportRun: run "${runId}" não encontrado`);
      // Ordem dos gates: o motivo mais acionável primeiro. "Revisão pendente no
      // passo X" diz o que a pessoa tem de fazer; "o run está blocked" só
      // descreve o sintoma (e é o estado em que um run com revisão pendente fica).
      const pendingReview = (snapshot.steps ?? []).filter((step) => step.review?.status === 'review-missing');
      if (pendingReview.length > 0) {
        throw new Error(`exportRun: revisão humana pendente no(s) passo(s) ${pendingReview.map((step) => `"${step.id}"`).join(', ')}. Nada foi gravado.`);
      }
      const reviewDiverged = (snapshot.steps ?? []).filter((step) => step.review?.approved === true && step.review?.sha256 && step.sha256 && step.review.sha256 !== step.sha256);
      if (reviewDiverged.length > 0) {
        throw new Error(`exportRun: o artefato do(s) passo(s) ${reviewDiverged.map((step) => `"${step.id}"`).join(', ')} mudou depois da revisão (SHA-256 diferente). Aprove novamente o conteúdo atual.`);
      }
      if (snapshot.status !== 'succeeded') {
        throw new Error(`exportRun: o run "${runId}" está "${snapshot.status}"; exportar exige run concluído. Nada foi gravado.`);
      }
      const rightsGate = await this.exportRightsGate({ runId, asset });
      if (!rightsGate.allowed) {
        throw new Error(`exportRun: direitos ${rightsGate.state} bloqueiam a exportação de "${runId}": ${rightsGate.blockers.join('; ')}. Nada foi gravado.`);
      }
      const runDirectory = path.join(projectRoot, RUNS_DIRECTORY, runId);
      const artifacts = [];
      const escaping = [];
      for (const step of snapshot.steps) {
        const emitted = step.outputs ?? [];
        for (const [index, relative] of emitted.entries()) {
          const absolute = path.isAbsolute(relative) ? relative : path.join(projectRoot, relative);
          // Confinamento da exportação (auditoria P0, item 2 / R-11): só os
          // artefatos **deste run** são autorizados. Antes a checagem era
          // `absolute.startsWith(runDirectory) || absolute.startsWith(projectRoot)`
          // — dois escapes medidos: (a) pasta irmã cujo nome começa com o id do
          // run (`run-abc-evil/…`) satisfazia o prefixo; (b) symlink criado dentro
          // do run apontando para fora do projeto tem caminho textual dentro da
          // raiz e conteúdo fora dela. E aceitar qualquer caminho do projeto
          // inteiro entregava ao manifesto arquivos que ninguém autorizou.
          // Aqui: caminho relativo + caminho real (symlinks resolvidos).
          const contained = await resolveContainedPath({
            root: runDirectory,
            target: absolute,
            ...containmentFs,
            label: `saída "${relative}" do passo "${step.id}"`,
          });
          if (!contained.ok) {
            escaping.push(`${step.id}: "${relative}" — ${contained.reason}`);
            continue;
          }
          if (!await pathExists(contained.target)) continue;
          const bytes = await fs.readFile(contained.target);
          // Integridade do byte exportado. O engine grava o SHA-256 da primeira
          // saída do passo (é o hash que a revisão humana aprovou); se o arquivo
          // em disco não bate com ele, o conteúdo mudou depois do run — exportar
          // seria entregar algo diferente do que foi revisado. Fail-closed.
          if (index === 0 && step.sha256 && hash(bytes) !== step.sha256) {
            throw new Error(`exportRun: o artefato "${path.basename(absolute)}" do passo "${step.id}" mudou depois do run (SHA-256 ${String(step.sha256).slice(0, 12)}… gravado, ${hash(bytes).slice(0, 12)}… em disco). Nada foi gravado.`);
          }
          artifacts.push({
            id: `${step.id}:${path.basename(contained.target)}`,
            format: path.extname(contained.target).slice(1).toLowerCase(),
            role: step.id,
            relativePath: path.relative(runDirectory, contained.target).split(path.sep).join('/'),
            bytes,
          });
        }
      }
      // Sair da pasta do run não é "artefato ignorado", é sinal de adulteração do
      // registro do run: falha fechado e nomeia o que foi recusado.
      if (escaping.length) {
        throw new Error(`exportRun: o run "${runId}" declara saída(s) fora da pasta do run — ${escaping.join('; ')}. Exportar só aceita os artefatos autorizados deste run. Nada foi gravado.`);
      }
      if (!artifacts.length) throw new Error('exportRun: o run não produziu artefatos gravados');
      const compatibility = checkDestinationCompatibility({ destinationId: destination, artifacts });
      const bundle = buildExportBundle({ destinationId: destination, artifacts, hash, asset: rightsGate.asset, rights: rightsGate.rights, workflowRunId: runId });
      const target = path.join(runDirectory, 'export', destination, 'manifest.json');
      await fs.mkdir(path.dirname(target), { recursive: true });
      await fs.writeFile(target, `${JSON.stringify(bundle, null, 2)}\n`, 'utf8');
      return Object.freeze({
        bundle,
        compatibility,
        path: path.relative(projectRoot, target).split(path.sep).join('/'),
        rightsState: rightsGate.state,
        rightsNote: rightsGate.note,
      });
    },

    /**
     * Direitos que governam a exportação de um run.
     *
     * Considera o asset informado e **todos** os assets que têm proveniência deste
     * run: vincular o run a um asset depois não pode servir para exportar sem o
     * gate, e declarar direitos só no asset "errado" também não.
     *
     * @returns {Promise<{allowed:boolean, state:string, blockers:string[], rights:object|null, asset:object|null, note:string}>}
     */
    async exportRightsGate({ runId, asset = null }) {
      const manager = await assets();
      const wantedId = typeof asset === 'string' ? asset : (asset?.id ?? null);
      const linked = (manager.list() ?? []).filter((entry) => (wantedId ? entry.id === wantedId : (entry.provenance ?? []).some((item) => item.runId === runId)));
      if (!linked.length) {
        return Object.freeze({
          allowed: true,
          state: 'not-declared',
          blockers: Object.freeze([]),
          rights: null,
          asset: null,
          note: 'Nenhum asset vinculado a este run: nenhuma licença foi declarada, então nada aqui afirma que o conteúdo está liberado.',
        });
      }
      const blocking = linked.filter((entry) => entry.rights?.redistributable !== true);
      if (blocking.length) {
        return Object.freeze({
          allowed: false,
          state: blocking.length === 1 ? String(blocking[0].rights?.state ?? 'unknown') : 'mixed',
          blockers: Object.freeze(blocking.flatMap((entry) => (entry.rights?.blockers ?? []).map((blocker) => `${entry.id}: ${blocker}`))),
          rights: null,
          asset: null,
          note: 'Direitos não redistribuíveis bloqueiam a exportação até uma pessoa declarar a licença.',
        });
      }
      const primary = linked.find((entry) => entry.id === wantedId) ?? linked[0];
      return Object.freeze({
        allowed: true,
        state: String(primary.rights?.state ?? 'unknown'),
        blockers: Object.freeze([]),
        rights: primary.rights ?? null,
        asset: primary,
        note: 'Direitos declarados por uma pessoa; a declaração vai no manifesto.',
      });
    },

    // ------------------------------------------------------------- assets
    async listAssets() {
      return (await assets()).list();
    },

    async upsertAsset(record) {
      return (await assets()).upsert(record);
    },

    async addAssetVersion(id, version) {
      return (await assets()).addVersion(id, version);
    },

    async declareAssetRights(id, declaration) {
      return (await assets()).declareRights(id, declaration);
    },

    async rightsReport() {
      return (await assets()).rightsReport();
    },

    /**
     * Registra a proveniência de um run inteiro no asset.
     *
     * Gates (P0-4 da revisão integrada). Antes: qualquer run virava versão de
     * asset e **todo** artefato recebia `validated: true` como literal, sem ler
     * `step.validations`, o estado do run ou a revisão — o oposto de "sem outputs
     * ou progresso simulados".
     *
     *   1. só run concluído vira versão (nada de `failed`/`blocked`/`cancelled`);
     *   2. nenhum passo reprovado, sem revisão pendente, nem revisão registrada
     *      sobre outro hash: a versão herda a integridade do run, não a substitui;
     *   3. `validated` é derivado da validação realmente executada, e só é `true`
     *      quando há validador aprovado **sobre estes bytes** (o SHA-256 que o
     *      passo gravou). Sem evidência, `validated: false` com o motivo escrito.
     */
    async attachRunToAsset({ assetId, runId }) {
      const snapshot = await this.readRun(runId);
      if (!snapshot) throw new Error(`attachRunToAsset: run "${runId}" não encontrado`);
      const manager = await assets();
      if (!manager.get(assetId)) throw new Error(`attachRunToAsset: asset "${assetId}" não encontrado`);
      // Mesma ordem de exportRun: motivo acionável primeiro.
      const pendingReview = (snapshot.steps ?? []).filter((step) => step.review?.status === 'review-missing');
      if (pendingReview.length > 0) {
        throw new Error(`attachRunToAsset: revisão humana pendente no(s) passo(s) ${pendingReview.map((step) => `"${step.id}"`).join(', ')}. Nada foi gravado.`);
      }
      const reviewDiverged = (snapshot.steps ?? []).filter((step) => step.review?.approved === true && step.review?.sha256 && step.sha256 && step.review.sha256 !== step.sha256);
      if (reviewDiverged.length > 0) {
        throw new Error(`attachRunToAsset: o artefato do(s) passo(s) ${reviewDiverged.map((step) => `"${step.id}"`).join(', ')} mudou depois da revisão (SHA-256 diferente). Nada foi gravado.`);
      }
      const failedSteps = (snapshot.steps ?? []).filter((step) => step.state === 'failed');
      if (failedSteps.length > 0) {
        throw new Error(`attachRunToAsset: o passo ${failedSteps.map((step) => `"${step.id}"`).join(', ')} falhou; o run não é íntegro o bastante para virar versão de asset. Nada foi gravado.`);
      }
      if (snapshot.status !== 'succeeded') {
        throw new Error(`attachRunToAsset: o run "${runId}" está "${snapshot.status}"; versão de asset exige run concluído. Nada foi gravado.`);
      }
      const artifacts = [];
      for (const provenance of snapshot.provenance ?? []) {
        const emitted = provenance.outputs ?? [];
        const step = (snapshot.steps ?? []).find((item) => item.id === provenance.stepId) ?? null;
        for (const relative of emitted) {
          const absolute = path.join(projectRoot, relative);
          if (!await pathExists(absolute)) continue;
          const bytes = await fs.readFile(absolute);
          /**
           * O hash registrado é o dos bytes que acabaram de ser lidos.
           *
           * Antes, quando o passo tinha uma saída só, o registro reaproveitava
           * `provenance.sha256` — o hash do arquivo **quando o passo terminou**. Se
           * o arquivo foi reescrito depois (exportar de novo para o mesmo destino
           * reescreve o `manifest.json` com outro `generatedAt`, por exemplo), a
           * versão de asset passava a afirmar um hash que não era o do arquivo que
           * ela mesma tinha acabado de ler, com o mesmo tamanho em bytes: o catálogo
           * media o disco e reportava "hash divergente" para um arquivo que ninguém
           * tinha alterado depois do registro. Medido por tests/studio-ui-render-smoke.
           *
           * O vínculo com o que o passo validou não se perde: `deriveArtifactValidation`
           * compara com `step.sha256` e devolve `hash-diverged` nomeando os dois
           * hashes, que é onde essa informação sempre deveria ter estado.
           */
          const sha256 = hash(bytes);
          artifacts.push({
            path: relative,
            role: provenance.stepId,
            format: path.extname(relative).slice(1).toLowerCase() || null,
            bytes: bytes.length,
            sha256,
            ...deriveArtifactValidation({ step, sha256, emittedCount: emitted.length }),
          });
        }
        await manager.addProvenance(assetId, {
          adapter: provenance.adapter,
          adapterVersion: provenance.adapterVersion,
          tool: provenance.adapter,
          license: provenance.license,
          outputRights: provenance.outputRights,
          runId,
          at: provenance.at,
        });
      }
      if (artifacts.length) {
        await manager.addVersion(assetId, { runId, artifacts, note: `Artefatos do run ${runId}` });
      }
      return manager.get(assetId);
    },

    // ------------------------------------------------- entradas (referências)
    /**
     * Lista o que o usuário já tem em `<projeto>/input/`: é o que a interface
     * oferece para escolher, em vez de pedir que alguém digite um caminho.
     */
    /**
     * Passo 1 da jornada: onde está o projeto e o que há nele. Só leitura —
     * nada é criado aqui (criar/abrir pasta é ação do hospedeiro, que usa
     * `ensureProjectStructure` do mesmo módulo).
     */
    async projectInfo() {
      const structure = await inspectProjectStructure(projectRoot);
      const assets = await this.listAssets().catch(() => []);
      const runs = await this.listRuns().catch(() => []);
      return Object.freeze({
        ...structure,
        counts: Object.freeze({
          ...structure.counts,
          assets: Array.isArray(assets) ? assets.length : 0,
          runs: Array.isArray(runs) ? runs.length : structure.counts.runs,
        }),
        activeRuns: this.activeRuns().length,
        legacy: Object.freeze({
          spriteforge: structure.directories.legacyState.exists,
          liaManifest: structure.files.liaManifest.exists,
          note: structure.directories.legacyState.exists || structure.files.liaManifest.exists
            ? 'Conteúdo de versões anteriores (.spriteforge/, .lia.json) foi encontrado e é preservado: o produto não move, não converte e não apaga.'
            : 'Nenhum conteúdo legado (.spriteforge/, .lia.json) foi encontrado nesta pasta.',
        }),
      });
    },

    async listInputs() {
      return Object.freeze({ directory: INPUT_DIRECTORY, entries: Object.freeze(await walkInputs()) });
    },

    /**
     * Grava uma entrada fornecida pelo usuário (imagem de referência, modelo).
     * Regras: nome sanitizado, extensão permitida, conteúdo verificado quando o
     * formato é conhecido deste código, tamanho limitado, escrita atômica dentro
     * de `<projeto>/input/` e colisão nunca sobrescreve o arquivo existente.
     *
     * @param {{filename:string, bytes:Uint8Array|Buffer, note?:string}} input
     */
    async saveInput({ filename, bytes, note = null } = {}) {
      const name = sanitizeInputName(filename);
      if (!name) throw new Error('saveInput: nome de arquivo inválido (use apenas letras, números, ponto, hífen e sublinhado).');
      const extension = extensionOf(name);
      if (!INPUT_EXTENSIONS.includes(extension)) {
        throw new Error(`saveInput: formato ".${extension || '?'}" não é aceito como entrada. Aceitos: ${INPUT_EXTENSIONS.join(', ')}.`);
      }
      const payload = Buffer.isBuffer(bytes) ? bytes : Buffer.from(bytes ?? []);
      if (!payload.length) throw new Error('saveInput: nenhum byte recebido.');
      if (payload.length > MAX_INPUT_BYTES) throw new Error(`saveInput: arquivo maior que ${Math.round(MAX_INPUT_BYTES / (1024 * 1024))} MB.`);

      const described = describeInputBytes(name, payload);
      if (described.problem) throw new Error(`saveInput: ${described.problem}`);
      if (!described.contentChecked && INPUT_IMAGE_EXTENSIONS.includes(extension)) {
        throw new Error('saveInput: o conteúdo da imagem não pôde ser verificado neste formato.');
      }

      await fs.mkdir(inputRoot, { recursive: true });
      // Colisão ganha sufixo: o que o usuário já tinha nunca é sobrescrito. A
      // comparação ignora caixa porque o projeto pode viver em um sistema de
      // arquivos que também ignora (Windows/macOS) — lá seria o mesmo arquivo.
      const taken = new Set((await fs.readdir(inputRoot).catch(() => [])).map((item) => item.toLowerCase()));
      const stem = name.slice(0, name.length - extension.length - 1);
      // A extensão gravada é a que o usuário enviou (só a comparação ignora caixa).
      const rawExtension = name.slice(stem.length + 1);
      let finalName = name;
      for (let suffix = 2; taken.has(finalName.toLowerCase()); suffix += 1) {
        finalName = `${stem}-${suffix}.${rawExtension}`;
        if (suffix > 500) throw new Error('saveInput: não foi possível encontrar um nome livre para a entrada.');
      }
      const target = await resolveInside(inputRoot, finalName);
      if (!target) throw new Error('saveInput: caminho recusado pelo gate de escrita segura.');

      const temporary = `${target}.${process.pid}.${randomUUID()}.tmp`;
      await fs.writeFile(temporary, payload, { flag: 'wx' });
      try {
        await fs.rename(temporary, target);
      } catch (error) {
        await fs.rm(temporary, { force: true });
        throw error;
      }
      return Object.freeze({
        ...described,
        // o nome gravado pode ter sufixo anti-colisão: vale o que está no disco
        name: finalName,
        path: path.relative(projectRoot, target).split(path.sep).join('/'),
        note: note === null ? null : redactSecrets(String(note).slice(0, 400)),
      });
    },

    /** Bytes de uma entrada, confinados a `<projeto>/input/`. */
    async readInput(relativePath) {
      const absolute = await resolveInside(inputRoot, relativePath, projectRoot);
      if (!absolute) throw new Error('readInput: caminho fora de input/ foi recusado.');
      const stats = await fs.lstat(absolute).catch(() => null);
      if (!stats?.isFile()) throw new Error('readInput: entrada não encontrada.');
      if (stats.size > MAX_PREVIEW_BYTES) throw new Error(`readInput: arquivo maior que o limite de prévia (${MAX_PREVIEW_BYTES} bytes).`);
      return fs.readFile(absolute);
    },

    /**
     * Comparison Lab: mede lado a lado os artefatos escolhidos (de runs ou de
     * entradas) sem julgar qual é melhor — a decisão é humana e fica registrada.
     */
    async compareArtifacts({ paths: candidates = [] } = {}) {
      if (!Array.isArray(candidates) || !candidates.length) throw new Error('compareArtifacts: informe ao menos um caminho.');
      if (candidates.length > 8) throw new Error('compareArtifacts: compare até 8 artefatos por vez.');
      const entries = [];
      for (const candidate of candidates) {
        const relative = String(candidate ?? '');
        const absolute = path.isAbsolute(relative) ? null : await resolveInside(projectRoot, relative, projectRoot);
        if (!absolute) {
          entries.push(Object.freeze({ path: relative, ok: false, problem: 'Caminho fora do projeto foi recusado.' }));
          continue;
        }
        try {
          const bytes = await fs.readFile(absolute);
          const described = describeInputBytes(path.basename(absolute), bytes);
          entries.push(Object.freeze({ path: path.relative(projectRoot, absolute).split(path.sep).join('/'), ok: true, ...described }));
        } catch (error) {
          entries.push(Object.freeze({ path: relative, ok: false, problem: String(error.message ?? error).slice(0, 180) }));
        }
      }
      return Object.freeze({ comparedAt: new Date().toISOString(), entries: Object.freeze(entries) });
    },

    /**
     * Catálogo de assets do projeto.
     *
     * Só leitura: não cria asset, não escreve no store e não toca em arquivo do
     * usuário. Para cada artefato declarado nas versões, o arquivo é **medido de
     * novo** (SHA-256, estrutura e conteúdo) e comparado com o registro — o
     * catálogo mostra o estado do disco, não o que foi declarado no dia.
     *
     * @param {object} [params]
     * @param {string|null} [params.query] texto livre: id, nome, nota de versão ou caminho de artefato
     * @param {string|null} [params.type] `character` | `item`
     * @param {string|null} [params.rightsState] estado de direitos declarado
     * @param {'recent'|'name'|'versions'|'rights'} [params.sort]
     * @param {number|null} [params.limit] máximo de assets devolvidos (1..200)
     * @param {boolean} [params.measure] medir os artefatos (padrão true)
     */
    async assetCatalog({ query = null, type = null, rightsState = null, sort = 'recent', limit = null, measure = true } = {}) {
      const manager = await assets();
      const listed = manager.list() ?? [];
      const wanted = String(query ?? '').trim().toLowerCase();
      const wantedType = type === null || type === undefined || type === '' ? null : String(type);
      const wantedRights = rightsState === null || rightsState === undefined || rightsState === '' ? null : String(rightsState);
      const sortMode = ['recent', 'name', 'versions', 'rights'].includes(String(sort)) ? String(sort) : 'recent';
      const maxEntries = Number.isInteger(limit) && limit > 0 ? Math.min(limit, 200) : null;
      const shouldMeasure = measure !== false;
      let budget = shouldMeasure ? CATALOG_MEASURE_BUDGET : 0;

      /**
       * Primeira passada: montar o esqueleto de cada asset sem tocar em arquivo
       * nenhum. Filtrar e ordenar antes de medir é o que faz o orçamento de
       * leitura valer para o que vai ser devolvido — medir primeiro gastaria o
       * teto em assets que a busca descarta, e a resposta chegaria dizendo "não
       * medido" justamente para o que a pessoa pediu.
       */
      const candidates = listed.map((asset) => {
        const stamps = [];
        const versions = (asset.versions ?? []).map((version) => {
          if (version.createdAt) stamps.push(String(version.createdAt));
          return {
            version: version.version ?? null,
            createdAt: version.createdAt ?? null,
            runId: version.runId ?? null,
            note: version.note ?? null,
            /**
             * Versão marcada como substituída por uma reconciliação. A marca é
             * descritiva: a versão continua aqui, com seus artefatos.
             */
            superseded: version.superseded ? {
              at: version.superseded.at ?? null,
              reason: version.superseded.reason ?? null,
              divergenceReason: version.superseded.divergenceReason ?? null,
              replacedByVersion: version.superseded.replacedByVersion ?? null,
              artifactPath: version.superseded.artifactPath ?? null,
              /**
               * A divergência que motivou a marcação, preservada como evidência
               * histórica: os dois lados (o que o registro afirmava e o que o
               * disco mostrou) e o estado da comparação naquele momento.
               */
              observed: version.superseded.observed ? {
                recordedSha256: version.superseded.observed.recordedSha256 ?? null,
                recordedBytes: typeof version.superseded.observed.recordedBytes === 'number' ? version.superseded.observed.recordedBytes : null,
                measuredSha256: version.superseded.observed.measuredSha256 ?? null,
                measuredBytes: typeof version.superseded.observed.measuredBytes === 'number' ? version.superseded.observed.measuredBytes : null,
                format: version.superseded.observed.format ?? null,
                comparisonState: version.superseded.observed.comparisonState ?? null,
                comparisonReason: version.superseded.observed.comparisonReason ?? null,
                exists: version.superseded.observed.exists === true,
              } : null,
              by: version.superseded.by ? {
                kind: version.superseded.by.kind ?? 'local-user',
                uid: typeof version.superseded.by.uid === 'number' ? version.superseded.by.uid : null,
                reviewer: version.superseded.by.reviewer ?? null,
              } : null,
            } : null,
            reconciliation: version.reconciliation ? {
              fromVersion: version.reconciliation.fromVersion ?? null,
              operation: version.reconciliation.operation ?? null,
              at: version.reconciliation.at ?? null,
              entryId: version.reconciliation.entryId ?? null,
            } : null,
            artifacts: (version.artifacts ?? []).map((artifact) => ({
              path: String(artifact?.path ?? ''),
              role: artifact?.role ?? 'artifact',
              recordedFormat: artifact?.format ?? null,
              recordedBytes: typeof artifact?.bytes === 'number' ? artifact.bytes : null,
              recordedSha256: artifact?.sha256 ?? null,
              validated: artifact?.validated === true,
              validation: artifact?.validation
                ? { status: artifact.validation.status ?? null, reason: artifact.validation.reason ?? null }
                : null,
              /**
               * Apontamentos anteriores preservados por reconciliações `repoint`:
               * é o histórico que impede "o registro mudou e ninguém sabe o que era".
               */
              previous: (artifact?.previous ?? []).map((item) => ({
                path: String(item?.path ?? ''),
                sha256: item?.sha256 ?? null,
                bytes: typeof item?.bytes === 'number' ? item.bytes : null,
                format: item?.format ?? null,
                validated: item?.validated === true,
                replacedAt: item?.replacedAt ?? null,
              })),
            })),
          };
        });
        for (const entry of asset.provenance ?? []) if (entry.at) stamps.push(String(entry.at));
        if (asset.updatedAt) stamps.push(String(asset.updatedAt));
        if (asset.createdAt) stamps.push(String(asset.createdAt));
        const rights = asset.rights ?? null;
        const lastAt = stamps.length ? stamps.slice().sort().pop() : null;
        return {
          lastAt,
          versionCount: versions.length,
          rightsState: rights?.state ?? 'unknown',
          name: asset.name ?? asset.id,
          skeleton: {
            id: asset.id,
            name: asset.name ?? asset.id,
            type: asset.type ?? null,
            kind: asset.kind ?? asset.type ?? null,
            stage: asset.stage ?? null,
            destination: asset.destination ?? null,
            createdAt: asset.createdAt ?? null,
            updatedAt: asset.updatedAt ?? null,
            lastActivityAt: lastAt,
            rights: rights ? {
              state: rights.state ?? 'unknown',
              redistributable: rights.redistributable === true,
              licenses: [...(rights.licenses ?? [])],
              blockers: [...(rights.blockers ?? [])],
              declaredBy: rights.declaredBy ?? null,
              declaredAt: rights.declaredAt ?? null,
              note: rights.note ?? null,
            } : null,
            versionCount: versions.length,
            versionRunIds: versions.map((version) => version.runId).filter(Boolean),
            supersededVersionCount: versions.filter((version) => version.superseded).length,
            /**
             * Auditoria de reconciliação do asset: append-only no store e limitada
             * aqui às últimas decisões — o total real acompanha, para a interface
             * nunca apresentar histórico truncado como se fosse completo.
             */
            reconciliationTotal: Array.isArray(asset.reconciliations) ? asset.reconciliations.length : 0,
            reconciliations: reconciliationHistory(asset, RECONCILIATION_HISTORY_LIMIT).entries,
            reconciliationHistoryLimit: RECONCILIATION_HISTORY_LIMIT,
            provenance: (asset.provenance ?? []).map((item) => ({
              source: item.source ?? null,
              tool: item.tool ?? null,
              adapter: item.adapter ?? null,
              model: item.model ?? null,
              license: item.license ?? null,
              weightsLicense: item.weightsLicense ?? null,
              runId: item.runId ?? null,
              at: item.at ?? null,
            })),
            versions,
          },
        };
      });

      const filtered = candidates.filter((candidate) => {
        if (wantedType && String(candidate.skeleton.type ?? '') !== wantedType) return false;
        if (wantedRights && String(candidate.rightsState) !== wantedRights) return false;
        if (!wanted) return true;
        const haystack = [
          candidate.skeleton.id,
          candidate.skeleton.name,
          ...candidate.skeleton.versions.map((version) => version.note ?? ''),
          ...candidate.skeleton.versions.flatMap((version) => version.artifacts.map((artifact) => artifact.path)),
        ].join('\n').toLowerCase();
        return haystack.includes(wanted);
      });

      const RIGHTS_ORDER = ['blocked', 'restricted', 'license-pending', 'unknown', 'owned', 'licensed'];
      const byName = (left, right) => String(left.skeleton.name).localeCompare(String(right.skeleton.name), 'pt-BR');
      const sorted = filtered.slice().sort((left, right) => {
        if (sortMode === 'name') return byName(left, right);
        if (sortMode === 'versions') return right.versionCount - left.versionCount || byName(left, right);
        if (sortMode === 'rights') {
          const a = RIGHTS_ORDER.indexOf(String(left.rightsState));
          const b = RIGHTS_ORDER.indexOf(String(right.rightsState));
          return (a < 0 ? 99 : a) - (b < 0 ? 99 : b) || byName(left, right);
        }
        const leftAt = left.lastAt ? Date.parse(left.lastAt) : 0;
        const rightAt = right.lastAt ? Date.parse(right.lastAt) : 0;
        return rightAt - leftAt || byName(left, right);
      });
      const selected = maxEntries ? sorted.slice(0, maxEntries) : sorted;

      /**
       * Segunda passada: medir só o que vai ser devolvido, dentro do orçamento.
       * Cada artefato é lido de novo e comparado com o que o store registrou.
       */
      const totals = { artifacts: 0, measured: 0, missing: 0, diverged: 0, refused: 0 };
      const entries = [];
      for (const candidate of selected) {
        const counters = { artifacts: 0, measured: 0, missing: 0, diverged: 0, refused: 0 };
        const versions = [];
        for (const version of candidate.skeleton.versions) {
          const artifacts = [];
          for (const recorded of version.artifacts) {
            const useBudget = budget > 0;
            if (useBudget) budget -= 1;
            const inspected = await inspectProjectFile(recorded.path, {
              // `compareWithRecord` compara contra os nomes do store
              // (`bytes`/`sha256`/`format`), não contra os do esqueleto do catálogo.
              recorded: {
                bytes: recorded.recordedBytes,
                sha256: recorded.recordedSha256,
                format: recorded.recordedFormat,
              },
              measure: shouldMeasure && useBudget,
            });
            counters.artifacts += 1;
            if (inspected.measurement) counters.measured += 1;
            if (inspected.refused) counters.refused += 1;
            else if (!inspected.exists) counters.missing += 1;
            else if (String(inspected.comparison.state).endsWith('-diverged')) counters.diverged += 1;
            artifacts.push(Object.freeze({
              path: inspected.path,
              role: recorded.role,
              recordedFormat: recorded.recordedFormat,
              recordedBytes: recorded.recordedBytes,
              recordedSha256: recorded.recordedSha256,
              validated: recorded.validated,
              validation: recorded.validation ? Object.freeze({ ...recorded.validation }) : null,
              exists: inspected.exists,
              refused: inspected.refused,
              comparisonState: inspected.comparison.state,
              comparisonReason: inspected.comparison.reason,
              diverged: Object.freeze([...inspected.comparison.diverged]),
              /**
               * Apontamentos anteriores preservados por reconciliações `repoint`.
               * O catálogo é leitura: mostra o histórico, nunca o reescreve.
               */
              previous: Object.freeze((recorded.previous ?? []).map((item) => Object.freeze({ ...item }))),
              measured: inspected.measurement ? Object.freeze({
                format: inspected.measurement.format,
                bytes: inspected.measurement.bytes,
                sha256: inspected.measurement.sha256,
                width: inspected.measurement.image?.width ?? inspected.measurement.structure?.width ?? null,
                height: inspected.measurement.image?.height ?? inspected.measurement.structure?.height ?? null,
                uniqueColors: inspected.measurement.image?.uniqueColors ?? null,
                coverage: inspected.measurement.image?.coverage ?? null,
                meshCount: inspected.measurement.model?.meshCount ?? null,
                triangleCount: inspected.measurement.model?.triangleCount ?? null,
                summary: inspected.measurement.model?.summary ?? null,
                limitations: Object.freeze([...inspected.measurement.limitations]),
                error: inspected.measurement.error,
              }) : null,
            }));
          }
          versions.push(Object.freeze({
            version: version.version,
            createdAt: version.createdAt,
            runId: version.runId,
            note: version.note,
            /**
             * Marca de substituição e vínculo de reconciliação: a segunda passada
             * reconstrói a versão campo a campo, então o que não for listado aqui
             * sumiria da resposta mesmo estando gravado no store.
             */
            superseded: version.superseded ? Object.freeze({
              ...version.superseded,
              observed: version.superseded.observed ? Object.freeze({ ...version.superseded.observed }) : null,
              by: version.superseded.by ? Object.freeze({ ...version.superseded.by }) : null,
            }) : null,
            reconciliation: version.reconciliation ? Object.freeze({ ...version.reconciliation }) : null,
            artifactCount: artifacts.length,
            artifacts: Object.freeze(artifacts),
          }));
        }
        totals.artifacts += counters.artifacts;
        totals.measured += counters.measured;
        totals.missing += counters.missing;
        totals.diverged += counters.diverged;
        totals.refused += counters.refused;
        entries.push(Object.freeze({
          ...candidate.skeleton,
          rights: candidate.skeleton.rights ? Object.freeze({
            ...candidate.skeleton.rights,
            licenses: Object.freeze(candidate.skeleton.rights.licenses),
            blockers: Object.freeze(candidate.skeleton.rights.blockers),
          }) : null,
          versionRunIds: Object.freeze(candidate.skeleton.versionRunIds),
          provenance: Object.freeze(candidate.skeleton.provenance.map((item) => Object.freeze({ ...item }))),
          reconciliations: Object.freeze(candidate.skeleton.reconciliations.map((item) => Object.freeze({ ...item }))),
          artifacts: Object.freeze({ ...counters }),
          versions: Object.freeze(versions),
        }));
      }

      return Object.freeze({
        schemaVersion: STUDIO_SERVICE_SCHEMA_VERSION,
        generatedAt: new Date().toISOString(),
        total: listed.length,
        returned: entries.length,
        filters: Object.freeze({ query: wanted || null, type: wantedType, rightsState: wantedRights }),
        sort: sortMode,
        limit: maxEntries,
        totals: Object.freeze(totals),
        measureBudget: Object.freeze({
          perCall: CATALOG_MEASURE_BUDGET,
          used: shouldMeasure ? Math.max(0, CATALOG_MEASURE_BUDGET - budget) : 0,
          exhausted: shouldMeasure && budget <= 0,
          maxBytesPerFile: MEASURE_LIMITS.maxBytes,
        }),
        entries: Object.freeze(entries),
        note: totals.diverged || totals.missing || totals.refused
          ? `${totals.diverged} artefato(s) divergem do registro, ${totals.missing} não estão no disco e ${totals.refused} tiveram o caminho recusado. O catálogo mostra o que o disco diz agora; o registro do asset não foi alterado.`
          : 'Catálogo medido no disco nesta chamada. Validação estrutural não é aprovação visual: qualidade, identidade e adequação ao jogo continuam sendo decisão humana.',
      });
    },

    /**
     * Inspeção de um arquivo do projeto: medição real + de onde ele veio.
     *
     * O caminho é confinado à raiz do projeto pelo mesmo módulo que a exportação
     * usa (`shared/fs/path-containment.mjs`): `..`, absoluto externo e symlink
     * apontando para fora são recusados com motivo, e nada é lido.
     *
     * @param {object} params
     * @param {string} params.path caminho relativo ao projeto (ou absoluto dentro dele)
     * @param {{columns:number,rows:number}|null} [params.grid] grade esperada, para atlas
     */
    async inspectArtifact({ path: declaredPath, grid = null } = {}) {
      if (typeof declaredPath !== 'string' || !declaredPath.trim()) {
        throw new Error('inspectArtifact: informe o caminho do artefato (relativo à raiz do projeto).');
      }
      const inspected = await inspectProjectFile(declaredPath, { recorded: null, measure: true, grid });
      if (inspected.refused) {
        throw new Error(`inspectArtifact: ${inspected.refused} Nada foi lido.`);
      }
      const provenance = { runs: [], assets: [], exports: [], input: null };

      // De que run/passo este arquivo veio, e o que a revisão humana decidiu.
      //
      // A busca é limitada aos runs mais recentes: cada run exige ler o
      // `run.json` inteiro, e o serviço roda no processo principal do Electron —
      // varrer centenas de runs por clique travaria a janela. O que ficou de fora
      // é dito na resposta (`runsTruncated`), não omitido em silêncio.
      const allRuns = (await this.listRuns()) ?? [];
      const runs = allRuns
        .slice()
        .sort((left, right) => String(right.startedAt ?? '').localeCompare(String(left.startedAt ?? '')))
        .slice(0, RUN_PROVENANCE_SCAN_LIMIT);
      const runsTruncated = allRuns.length > runs.length;
      for (const summary of runs) {
        const snapshot = await this.readRun(summary.runId);
        if (!snapshot || !Array.isArray(snapshot.steps)) continue;
        const runDirectory = path.join(projectRoot, RUNS_DIRECTORY, String(snapshot.runId ?? summary.runId));
        for (const step of snapshot.steps) {
          const outputs = Array.isArray(step.outputs) ? step.outputs : [];
          const matched = outputs.map((output) => path.relative(projectRoot, path.isAbsolute(output) ? output : path.resolve(projectRoot, output)).split(path.sep).join('/'))
            .find((normalized) => normalized === inspected.path);
          if (!matched) continue;
          const review = step.review ?? null;
          provenance.runs.push(Object.freeze({
            runId: String(snapshot.runId ?? summary.runId),
            runStatus: snapshot.status ?? null,
            stepId: String(step.id ?? ''),
            stepTitle: step.title ?? null,
            adapter: step.adapter ?? null,
            stepState: step.state ?? null,
            stepSha256: step.sha256 ?? null,
            hashMatchesStep: step.sha256 && inspected.measurement?.sha256 ? step.sha256 === inspected.measurement.sha256 : null,
            // `readRun` devolve a decisão humana em duas formas: solta no objeto
            // (`reviewedBy`/`reviewedAt`) quando o passo não tinha revisão anterior,
            // e em `review.recorded` quando tinha. As duas são lidas aqui — senão a
            // inspeção mostraria "sem decisão" para um passo já revisado.
            review: review ? Object.freeze((() => {
              const human = review.recorded ?? review;
              // Na forma sem `recorded` não existe campo `approved`: a decisão está
              // em `review.status` ('approved' | 'rejected'). Sem ler as duas, um
              // passo já revisado apareceria como "sem decisão".
              const approved = human?.approved === true || review.status === 'approved'
                ? true
                : human?.approved === false || review.status === 'rejected'
                  ? false
                  : null;
              return {
                status: review.status ?? null,
                approved,
                reviewer: human?.reviewedBy ?? human?.reviewer ?? null,
                at: human?.reviewedAt ?? null,
                note: human?.note ?? null,
                sha256: human?.sha256 ?? null,
                matchesArtifact: human?.matchesArtifact ?? null,
                historyCount: Array.isArray(human?.history) ? human.history.length : 0,
              };
            })()) : null,
          }));
          // Manifestos de exportação deste run que declaram este arquivo.
          const insideRun = path.relative(runDirectory, path.resolve(projectRoot, inspected.path)).split(path.sep).join('/');
          const exportRoot = path.join(runDirectory, 'export');
          if (await pathExists(exportRoot)) {
            for (const destination of await fs.readdir(exportRoot, { withFileTypes: true })) {
              if (!destination.isDirectory()) continue;
              const manifestPath = path.join(exportRoot, destination.name, 'manifest.json');
              let manifest = null;
              try { manifest = JSON.parse(await fs.readFile(manifestPath, 'utf8')); } catch { manifest = null; }
              if (!manifest || !Array.isArray(manifest.files)) continue;
              const declared = manifest.files.find((file) => String(file?.path ?? '') === insideRun || String(file?.path ?? '') === inspected.path);
              if (!declared) continue;
              provenance.exports.push(Object.freeze({
                runId: String(snapshot.runId ?? summary.runId),
                destination: manifest.destination ?? destination.name,
                manifestPath: path.relative(projectRoot, manifestPath).split(path.sep).join('/'),
                recordedSha256: declared.sha256 ?? null,
                hashMatchesNow: declared.sha256 && inspected.measurement?.sha256 ? declared.sha256 === inspected.measurement.sha256 : null,
                rightsState: manifest.rights?.state ?? null,
                generatedAt: manifest.generatedAt ?? null,
              }));
            }
          }
        }
      }

      // Em quais versões de asset este arquivo está registrado.
      for (const asset of (await assets()).list() ?? []) {
        for (const version of asset.versions ?? []) {
          for (const artifact of version.artifacts ?? []) {
            const normalized = path.relative(projectRoot, path.isAbsolute(artifact.path) ? artifact.path : path.resolve(projectRoot, String(artifact.path ?? ''))).split(path.sep).join('/');
            if (normalized !== inspected.path) continue;
            provenance.assets.push(Object.freeze({
              assetId: asset.id,
              assetName: asset.name ?? asset.id,
              version: version.version ?? null,
              createdAt: version.createdAt ?? null,
              runId: version.runId ?? null,
              role: artifact.role ?? null,
              validated: artifact.validated === true,
              validationStatus: artifact.validation?.status ?? null,
              rightsState: asset.rights?.state ?? 'unknown',
            }));
          }
        }
      }

      // Se é uma entrada do usuário, diz o que foi registrado sobre ela.
      if (inspected.path.startsWith(`${INPUT_DIRECTORY}/`)) {
        const inputs = await this.listInputs();
        const entry = (inputs?.entries ?? []).find((item) => item.path === inspected.path || item.relativePath === inspected.path);
        provenance.input = entry ? Object.freeze({
          path: entry.path,
          name: entry.name ?? null,
          kind: entry.kind ?? null,
          bytes: typeof entry.bytes === 'number' ? entry.bytes : null,
          modifiedAt: entry.modifiedAt ?? null,
          contentChecked: entry.contentChecked === true,
          problem: entry.problem ?? null,
          sha256: entry.sha256 ?? null,
        }) : Object.freeze({ path: inspected.path, name: null, kind: null, bytes: null, modifiedAt: null, contentChecked: false, problem: 'o arquivo está em input/ mas a listagem de entradas não o retornou (formato fora da lista aceita ou teto de tamanho)', sha256: null });
      }

      const truncationNote = runsTruncated
        ? ` A busca de origem percorreu os ${runs.length} runs mais recentes de ${allRuns.length}: um vínculo com um run mais antigo pode não aparecer aqui.`
        : '';
      return Object.freeze({
        schemaVersion: STUDIO_SERVICE_SCHEMA_VERSION,
        generatedAt: new Date().toISOString(),
        path: inspected.path,
        exists: inspected.exists,
        symlink: inspected.symlink,
        readError: inspected.readError,
        measurement: inspected.measurement,
        provenance: Object.freeze({
          runs: Object.freeze(provenance.runs),
          assets: Object.freeze(provenance.assets),
          exports: Object.freeze(provenance.exports),
          input: provenance.input,
          runsScanned: runs.length,
          runsTruncated,
          runsScanLimit: RUN_PROVENANCE_SCAN_LIMIT,
        }),
        note: !inspected.exists
          ? 'O arquivo não está no disco: nada foi medido e nada aqui afirma conteúdo.'
          : (!provenance.runs.length && !provenance.assets.length && !provenance.exports.length && !provenance.input)
            ? `Medição estrutural executada agora sobre os bytes em disco. Nenhum run, versão de asset, manifesto de exportação ou entrada registra este arquivo: ele existe no projeto, mas não é artefato de nenhuma execução rastreada. Medição não é aprovação visual.${truncationNote}`
            : `Medição estrutural executada agora, sobre os bytes em disco. Não é aprovação visual nem julgamento de qualidade: identidade, arte e adequação ao jogo continuam sendo decisão humana.${truncationNote}`
      });
    },

    // ------------------------------------- comparação de versões e duplicatas
    /**
     * Compara duas versões registradas do **mesmo** asset.
     *
     * Só leitura: mede os arquivos de novo (dentro do orçamento) e devolve o que o
     * registro diz, o que o disco diz agora e onde os dois discordam. Não corrige,
     * não reconcilia e não grava nada — reconciliar é
     * `planArtifactReconciliation` + `confirmArtifactReconciliation`, com revisão e
     * auditoria.
     *
     * @param {object} params
     * @param {string} params.assetId asset dono das duas versões
     * @param {string} params.left rótulo da primeira versão (ex.: `v1`)
     * @param {string} params.right rótulo da segunda versão (ex.: `v2`)
     * @param {boolean} [params.measure] medir os arquivos agora (padrão true)
     */
    async compareAssetVersions({ assetId = null, left = null, right = null, measure = true } = {}) {
      const wantedAsset = String(assetId ?? '').trim();
      if (!wantedAsset) {
        throw Object.assign(new Error('compareAssetVersions: informe o asset (assetId). Nada foi lido.'), { code: 'MISSING_ASSET' });
      }
      const leftLabel = String(left ?? '').trim();
      const rightLabel = String(right ?? '').trim();
      if (!leftLabel || !rightLabel) {
        throw Object.assign(new Error('compareAssetVersions: informe as duas versões (left e right). Nada foi lido.'), { code: 'MISSING_VERSION' });
      }
      if (leftLabel === rightLabel) {
        throw Object.assign(new Error(`compareAssetVersions: as duas versões são a mesma ("${leftLabel}"). Escolha duas versões diferentes: comparar uma versão consigo mesma não informa nada e gastaria o orçamento de leitura.`), { code: 'SAME_VERSION' });
      }

      const read = await assetsForRead();
      const budgetSummary = (used) => Object.freeze({
        perCall: VERSION_MEASURE_BUDGET,
        used,
        exhausted: used >= VERSION_MEASURE_BUDGET,
        maxBytesPerFile: MEASURE_LIMITS.maxBytes,
      });
      if (read.state !== 'ok') {
        return Object.freeze({
          schemaVersion: COMPARISON_SCHEMA_VERSION,
          generatedAt: new Date().toISOString(),
          readOnly: true,
          store: Object.freeze({ state: read.state, message: read.message }),
          asset: null,
          left: null,
          right: null,
          pairs: Object.freeze([]),
          versionFields: Object.freeze([]),
          verdict: contentVerdict(null, null),
          differences: Object.freeze([]),
          divergences: Object.freeze([]),
          limitations: Object.freeze([read.message]),
          measureBudget: budgetSummary(0),
          note: 'Sem registro legível não há versões para comparar. Nada foi gravado, reescrito nem lido de arquivo de artefato.',
        });
      }

      const asset = read.assets.find((item) => String(item?.id ?? '') === wantedAsset) ?? null;
      if (!asset) {
        const known = read.assets.map((item) => String(item?.id ?? '')).filter(Boolean);
        throw Object.assign(new Error(`compareAssetVersions: o asset "${wantedAsset}" não existe no registro deste projeto. Assets registrados: ${known.join(', ') || '(nenhum)'}.`), { code: 'ASSET_NOT_FOUND' });
      }
      const versions = asset.versions ?? [];
      const leftVersion = versions.find((version) => String(version?.version ?? '') === leftLabel) ?? null;
      const rightVersion = versions.find((version) => String(version?.version ?? '') === rightLabel) ?? null;
      const missing = [leftVersion ? null : leftLabel, rightVersion ? null : rightLabel].filter(Boolean);
      if (missing.length) {
        throw Object.assign(new Error(`compareAssetVersions: a versão ${missing.map((label) => `"${label}"`).join(' e ')} não existe no asset "${wantedAsset}". Versões registradas: ${versions.map((version) => version?.version).filter(Boolean).join(', ') || '(nenhuma)'}.`), { code: 'VERSION_NOT_FOUND' });
      }

      const shouldMeasure = measure !== false;
      let budget = shouldMeasure ? VERSION_MEASURE_BUDGET : 0;

      /**
       * Mede os artefatos de uma versão pelo mesmo caminho do catálogo: o registro
       * vai para `recorded` (com os nomes que o store usa) e a resposta da inspeção
       * vira o lado da comparação. Sem orçamento restante o arquivo continua sendo
       * verificado quanto a existência e confinamento (barato) e a resposta diz que
       * não foi medido — nunca um valor inventado.
       */
      const readSides = async (version) => {
        const sides = [];
        for (const artifact of version?.artifacts ?? []) {
          const useBudget = budget > 0;
          if (useBudget) budget -= 1;
          const inspected = await inspectProjectFile(String(artifact?.path ?? ''), {
            recorded: {
              bytes: typeof artifact?.bytes === 'number' ? artifact.bytes : null,
              sha256: artifact?.sha256 ?? null,
              format: artifact?.format ?? null,
            },
            measure: shouldMeasure && useBudget,
          });
          sides.push(describeArtifactSide({
            path: artifact?.path ?? null,
            role: artifact?.role ?? null,
            recordedFormat: artifact?.format ?? null,
            recordedBytes: artifact?.bytes ?? null,
            recordedSha256: artifact?.sha256 ?? null,
            validated: artifact?.validated === true,
            validation: artifact?.validation ?? null,
            previous: artifact?.previous ?? [],
          }, inspected));
        }
        return sides;
      };

      const leftSides = await readSides(leftVersion);
      const rightSides = await readSides(rightVersion);
      const usedBudget = shouldMeasure ? Math.max(0, VERSION_MEASURE_BUDGET - budget) : 0;

      const leftPrimary = primaryArtifact(leftSides);
      const rightPrimary = primaryArtifact(rightSides);
      const describeVersion = (version, sides, label, primary) => Object.freeze({
          label,
          version: version?.version ?? null,
          createdAt: version?.createdAt ?? null,
          runId: version?.runId ?? null,
          note: typeof version?.note === 'string' ? version.note : null,
          artifactCount: sides.length,
          superseded: version?.superseded ? Object.freeze({
            at: version.superseded.at ?? null,
            reason: version.superseded.reason ?? null,
            divergenceReason: version.superseded.divergenceReason ?? null,
            replacedByVersion: version.superseded.replacedByVersion ?? null,
            artifactPath: version.superseded.artifactPath ?? null,
            by: version.superseded.by ? Object.freeze({
              kind: version.superseded.by.kind ?? null,
              uid: typeof version.superseded.by.uid === 'number' ? version.superseded.by.uid : null,
              reviewer: version.superseded.by.reviewer ?? null,
            }) : null,
          }) : null,
          reconciliation: version?.reconciliation ? Object.freeze({
            fromVersion: version.reconciliation.fromVersion ?? null,
            operation: version.reconciliation.operation ?? null,
            at: version.reconciliation.at ?? null,
            entryId: version.reconciliation.entryId ?? null,
          }) : null,
          artifacts: Object.freeze(sides),
          /**
           * Artefato que representa este lado na comparação visual, escolhido por
           * regra declarada (primeiro formato exibível em ordem alfabética de
           * caminho) — e a prévia só é prometida quando dá para mostrar.
           */
          primary: Object.freeze({
            path: primary?.path ?? null,
            exists: primary?.exists ?? null,
            preview: previewFor(primary ?? {}),
          }),
      });

      const leftPayload = describeVersion(leftVersion, leftSides, leftLabel, leftPrimary);
      const rightPayload = describeVersion(rightVersion, rightSides, rightLabel, rightPrimary);
      const pairs = pairArtifacts(leftSides, rightSides);
      const pairPayload = Object.freeze(pairs.map((pair) => Object.freeze({
        key: pair.key,
        basis: pair.basis,
        leftPath: pair.left?.path ?? null,
        rightPath: pair.right?.path ?? null,
        fields: artifactFields(pair.left ?? {}, pair.right ?? {}),
        verdict: contentVerdict(pair.left, pair.right),
        leftPreview: previewFor(pair.left ?? {}),
        rightPreview: previewFor(pair.right ?? {}),
      })));
      const fields = versionFields(leftPayload, rightPayload);
      const verdict = contentVerdict(leftPrimary, rightPrimary);

      const differences = Object.freeze([
        ...fields.filter((field) => field.differs).map((field) => Object.freeze({
          scope: 'version', key: field.key, label: field.label, group: field.group, left: field.left, right: field.right,
        })),
        ...pairPayload.flatMap((pair) => pair.fields
          .filter((field) => field.differs)
          .map((field) => Object.freeze({
            scope: pair.key,
            leftPath: pair.leftPath,
            rightPath: pair.rightPath,
            key: field.key,
            label: field.label,
            group: field.group,
            left: field.left,
            right: field.right,
          }))),
      ]);
      /**
       * Campos sem valor. Cada entrada diz de onde veio (`version` ou o par de
       * artefatos): "Largura ausente" sem escopo não diz se é a versão que não tem
       * data ou o GLB que não tem pixels.
       */
      const unavailable = Object.freeze([
        ...fields.filter((field) => field.missing).map((field) => Object.freeze({
          scope: 'version', key: field.key, label: field.label, group: field.group, missing: field.missing,
        })),
        ...pairPayload.flatMap((pair) => pair.fields
          .filter((field) => field.missing)
          .map((field) => Object.freeze({
            scope: pair.key,
            leftPath: pair.leftPath,
            rightPath: pair.rightPath,
            key: field.key,
            label: field.label,
            group: field.group,
            missing: field.missing,
          }))),
      ]);
      const divergences = divergenceNotes([
        ...leftSides.map((side) => ({ label: `${leftLabel} · ${side.path}`, side })),
        ...rightSides.map((side) => ({ label: `${rightLabel} · ${side.path}`, side })),
      ]);
      const limitations = Object.freeze([...new Set([
        ...leftSides.flatMap((side) => side.limitations),
        ...rightSides.flatMap((side) => side.limitations),
        ...(shouldMeasure ? [] : ['medição desligada nesta chamada (measure=false): só o registro foi comparado']),
        ...(budget <= 0 && shouldMeasure ? [`o orçamento de ${VERSION_MEASURE_BUDGET} leituras por chamada acabou: alguns artefatos não foram medidos`] : []),
      ])]);

      return Object.freeze({
        schemaVersion: COMPARISON_SCHEMA_VERSION,
        generatedAt: new Date().toISOString(),
        readOnly: true,
        store: Object.freeze({ state: read.state, message: null }),
        asset: Object.freeze({
          id: asset.id,
          name: asset.name ?? asset.id,
          type: asset.type ?? null,
          stage: asset.stage ?? null,
          destination: asset.destination ?? null,
          rightsState: asset.rights?.state ?? 'unknown',
          versionCount: versions.length,
          reconciliationTotal: Array.isArray(asset.reconciliations) ? asset.reconciliations.length : 0,
        }),
        left: leftPayload,
        right: rightPayload,
        pairs: pairPayload,
        versionFields: Object.freeze(fields),
        verdict,
        identicalContent: verdict.identical,
        differences,
        unavailable,
        divergences,
        limitations,
        measureBudget: budgetSummary(usedBudget),
        note: verdict.identical === true
          ? 'Conteúdo idêntico medido agora: mesmo SHA-256 nos dois arquivos. Isto não diz que as versões são equivalentes para o jogo — só que os bytes são os mesmos. Nada foi alterado.'
          : verdict.identical === false
            ? 'Conteúdo diferente medido agora. A comparação não escolhe qual versão é melhor e não corrige divergência: reconciliar é outra ação, com revisão e auditoria.'
            : `Sem veredito de conteúdo: ${verdict.reason}. Nada foi alterado.`,
      });
    },

    /**
     * Conteúdo duplicado entre artefatos registrados.
     *
     * Só leitura. Agrupa por SHA-256 e diz de onde veio a evidência: hash **medido
     * agora** vale mais que hash gravado, e quando a medição desmente o registro
     * (o store dizia o mesmo hash e os arquivos atuais diferem) isso aparece em
     * `resolvedByMeasurement` em vez de virar grupo.
     *
     * Duplicata de conteúdo não é equivalência semântica: a resposta não sugere
     * fusão, limpeza nem substituição, e não toca em `rights` nem em `provenance`.
     *
     * @param {object} [params]
     * @param {number|null} [params.limit] máximo de grupos devolvidos (1..200)
     * @param {boolean} [params.measure] medir os arquivos agora (padrão true)
     */
    async findDuplicateArtifacts({ limit = null, measure = true } = {}) {
      const groupLimit = Number.isInteger(limit) && limit > 0 ? Math.min(limit, 200) : DUPLICATE_GROUP_LIMIT;
      const read = await assetsForRead();
      if (read.state !== 'ok') {
        return Object.freeze({
          schemaVersion: COMPARISON_SCHEMA_VERSION,
          generatedAt: new Date().toISOString(),
          readOnly: true,
          store: Object.freeze({ state: read.state, message: read.message }),
          assetCount: 0,
          candidateCount: 0,
          hashedCount: 0,
          unhashedCount: 0,
          measuredCount: 0,
          unmeasuredCount: 0,
          groupCount: 0,
          returnedGroupCount: 0,
          truncated: false,
          groupLimit,
          crossAssetGroupCount: 0,
          distinctFileGroupCount: 0,
          groups: Object.freeze([]),
          resolvedByMeasurement: Object.freeze([]),
          measureBudget: Object.freeze({
            perCall: DUPLICATE_MEASURE_BUDGET,
            used: 0,
            exhausted: false,
            maxBytesPerFile: MEASURE_LIMITS.maxBytes,
          }),
          limitations: Object.freeze([read.message]),
          note: 'Sem registro legível não há hashes para agrupar. Nada foi gravado nem reescrito.',
        });
      }

      const candidates = collectHashCandidates(read.assets);
      const shouldMeasure = measure !== false;
      let budget = shouldMeasure ? DUPLICATE_MEASURE_BUDGET : 0;
      const measurements = new Map();

      /**
       * Uma leitura por **caminho**, não por candidato: duas versões que apontam
       * para o mesmo arquivo não podem gastar o orçamento duas vezes — e o orçamento
       * é o que garante que a consulta não vira uma varredura ilimitada do projeto.
       */
      if (shouldMeasure) {
        for (const candidate of duplicateMeasureOrder(candidates)) {
          if (budget <= 0) break;
          if (measurements.has(candidate.path)) continue;
          budget -= 1;
          /**
           * `recorded: null` de propósito. O que se mede aqui é o **arquivo**
           * (hash, bytes, formato, existência); a conferência contra o registro é
           * do par registro × arquivo e é refeita por candidato dentro de
           * `buildDuplicateReport`. Duas versões podem apontar para o mesmo caminho
           * com hashes gravados diferentes — comparar uma vez contra o registro do
           * primeiro candidato e reaproveitar o resultado marcaria como divergente
           * um registro que confere.
           */
          const inspected = await inspectProjectFile(candidate.path, { recorded: null, measure: true });
          measurements.set(candidate.path, {
            sha256: inspected.measurement?.sha256 ?? null,
            bytes: inspected.measurement?.bytes ?? null,
            format: inspected.measurement?.format ?? null,
            exists: inspected.exists,
            refused: inspected.refused,
            readError: inspected.readError,
          });
        }
      }

      const report = buildDuplicateReport({ candidates, measurements, groupLimit });
      const usedBudget = shouldMeasure ? Math.max(0, DUPLICATE_MEASURE_BUDGET - budget) : 0;
      return Object.freeze({
        ...report,
        generatedAt: new Date().toISOString(),
        readOnly: true,
        store: Object.freeze({ state: read.state, message: null }),
        assetCount: read.assets.length,
        measureBudget: Object.freeze({
          perCall: DUPLICATE_MEASURE_BUDGET,
          used: usedBudget,
          exhausted: shouldMeasure && budget <= 0,
          maxBytesPerFile: MEASURE_LIMITS.maxBytes,
        }),
        limitations: Object.freeze([
          ...(shouldMeasure ? [] : ['medição desligada nesta chamada (measure=false): o agrupamento usa apenas o hash gravado no registro']),
          ...(report.unmeasuredCount ? [`${report.unmeasuredCount} artefato(s) não foram medidos nesta chamada: a igualdade deles vem do hash gravado, não do conteúdo atual`] : []),
          ...(report.missingCount ? [`${report.missingCount} artefato(s) apontam para arquivo que não está no disco: o estado atual deles não pôde ser verificado`] : []),
          ...(report.refusedCount ? [`${report.refusedCount} artefato(s) tiveram o caminho recusado pelo confinamento: nada foi lido`] : []),
          ...(report.unreadableCount ? [`${report.unreadableCount} artefato(s) não puderam ser lidos (erro de leitura reportado por arquivo)`] : []),
          ...(report.unhashedCount ? [`${report.unhashedCount} artefato(s) não têm SHA-256 no registro e não puderam ser agrupados sem medição`] : []),
          ...(report.truncated ? [`mais grupos existem além dos ${report.returnedGroupCount} devolvidos (teto de ${groupLimit} por chamada)`] : []),
          ...(budget <= 0 && shouldMeasure ? [`o orçamento de ${DUPLICATE_MEASURE_BUDGET} leituras por chamada acabou: parte do projeto não foi verificada`] : []),
          'Apontamentos anteriores (previous[]) de reconciliação repoint ficam de fora: são histórico, não artefato em uso.',
          'Snapshots de run (.lia-forge/runs/) não entram: a busca cobre o registro de assets. Um output só participa depois de virar versão de asset.',
        ]),
      });
    },

    /**
     * Bytes de um artefato **registrado** para a prévia visual.
     *
     * Existe porque as duas rotas de imagem do Studio são confinadas a `input/`
     * (`readInput`) e a `.lia-forge/runs/` (`/artifact`): artefato de asset fica em
     * qualquer pasta do projeto e, sem isto, a comparação lado a lado mostraria um
     * retângulo vazio para todo asset — que é exatamente o que a interface fazia.
     *
     * Fronteiras: confinamento à raiz do projeto pelo mesmo módulo da inspeção
     * (symlink que escapa é recusado sem ler), caminho precisa estar declarado no
     * registro de assets (versão atual ou apontamento anterior), extensão na lista
     * de imagem e teto de 6 MB. Fora disso nada é lido.
     */
    async readAssetArtifact(relativePath) {
      const declared = String(relativePath ?? '').trim();
      if (!declared) {
        throw Object.assign(new Error('readAssetArtifact: informe o caminho do artefato registrado (relativo à raiz do projeto). Nada foi lido.'), { code: 'MISSING_PATH' });
      }
      const contained = await resolveContainedPath({
        root: projectRoot,
        target: path.isAbsolute(declared) ? declared : path.resolve(projectRoot, declared),
        ...containmentFs,
        label: 'artefato de asset',
      });
      if (!contained.ok) {
        throw Object.assign(new Error(`readAssetArtifact: ${contained.reason} Nada foi lido.`), { code: 'PATH_REFUSED' });
      }
      const projectRelative = path.relative(projectRoot, contained.target).split(path.sep).join('/');
      const extension = path.extname(projectRelative).toLowerCase();
      const contentType = PREVIEW_CONTENT_TYPES[extension] ?? null;
      if (!contentType) {
        throw Object.assign(new Error(`readAssetArtifact: "${projectRelative}" não tem prévia nesta interface (extensão "${extension || '(sem extensão)'}"). Só ${Object.keys(PREVIEW_CONTENT_TYPES).join(', ')} são servidos; nada foi lido.`), { code: 'PREVIEW_UNSUPPORTED' });
      }
      const read = await assetsForRead();
      if (read.state !== 'ok') {
        // Fail-closed: sem registro legível não dá para afirmar que o caminho é um
        // artefato de asset, e servir bytes de qualquer arquivo do projeto não é
        // o que esta rota é.
        throw Object.assign(new Error(`readAssetArtifact: ${read.message} Sem confirmar que o caminho é artefato registrado, nada foi servido.`), { code: read.state === 'missing' ? 'STORE_MISSING' : 'STORE_UNREADABLE' });
      }
      if (!registeredArtifactPaths(read.assets).has(projectRelative)) {
        throw Object.assign(new Error(`readAssetArtifact: "${projectRelative}" não é artefato declarado em nenhuma versão de asset deste projeto. Esta rota só serve arquivos que o catálogo já expõe — o Studio não é um servidor de arquivos da pasta do projeto. Nada foi lido.`), { code: 'ARTIFACT_NOT_REGISTERED' });
      }
      const stats = await fs.lstat(contained.target).catch(() => null);
      if (!stats || !stats.isFile()) {
        throw Object.assign(new Error(`readAssetArtifact: "${projectRelative}" não está no disco ou não é um arquivo regular. Nada foi servido.`), { code: 'ARTIFACT_MISSING' });
      }
      if (stats.size > PREVIEW_MAX_BYTES) {
        throw Object.assign(new Error(`readAssetArtifact: "${projectRelative}" tem ${stats.size} bytes e excede o teto de prévia de ${PREVIEW_MAX_BYTES} bytes. Abra o arquivo no explorador; nada foi servido aqui.`), { code: 'PREVIEW_TOO_LARGE' });
      }
      const bytes = await fs.readFile(contained.target);
      return Object.freeze({
        path: projectRelative,
        contentType,
        extension,
        bytes: bytes.length,
        sha256: hash(bytes),
        base64: bytes.toString('base64'),
      });
    },

    /**
     * Plano de reconciliação de um artefato divergente.
     *
     * Mede de novo, agora, o arquivo registrado (e o destino, quando a operação é
     * `repoint`), compara com o registro e devolve o que a pessoa precisa revisar
     * **antes** de decidir — junto com um token que amarra a decisão a este estado.
     * Não grava nada: é leitura + medição.
     */
    async planArtifactReconciliation(input = {}) {
      const requested = normalizeReconciliationRequest(input);
      const { operation, assetId, version, artifactPath, newPath, replacedByVersion, reason, reviewer } = requested;
      const store = await readStoreForReconciliation();
      const located = locateReconciliationTarget({ store, assetId, version, artifactPath });
      const { asset, versions, versionRecord, artifact } = located;

      // `repoint` exige destino; os outros dois trabalham sobre o arquivo registrado.
      let targetDeclared = null;
      if (operation === 'repoint') {
        if (!newPath) {
          fail('MISSING_TARGET_PATH', 'A operação repoint exige o caminho do arquivo que o registro deve passar a apontar (newPath), dentro da pasta do projeto. Nada foi gravado.');
        }
        if (projectRelativeFrom(newPath) === projectRelativeFrom(String(artifact.path ?? ''))) {
          fail('TARGET_SAME_PATH', `O caminho "${newPath}" é o mesmo que o registro já aponta: não há o que repontar. Nada foi gravado.`);
        }
        targetDeclared = newPath;
      }

      const { recorded, inspection, targetInspection } = await measureReconciliationState({ artifact, targetPath: targetDeclared });
      const comparison = inspection.comparison ?? null;
      const measured = inspection.measurement ?? null;
      const limitations = [...(measured?.limitations ?? [])].map((item) => String(item));
      const warnings = [];

      if (!inspection.exists) {
        limitations.push('o arquivo registrado não está no disco: tamanho, hash e conteúdo não puderam ser medidos');
        if (operation === 'register-new-version') {
          fail('SOURCE_MISSING', `O arquivo registrado "${recorded.path}" não está no disco: não há bytes para medir e registrar como nova versão. Se o arquivo mudou de lugar, use repoint e escolha o caminho novo; se a versão deixou de valer, use mark-superseded. Nada foi gravado.`);
        }
      }

      if (operation === 'repoint') {
        // Confinamento e existência do destino são conferidos **antes** de qualquer
        // revisão: a pessoa nunca revisa um apontamento para um arquivo que não
        // pôde ser inspecionado.
        if (targetInspection.refused) {
          fail('TARGET_REFUSED', `O caminho escolhido "${targetDeclared}" foi recusado pelo confinamento do projeto: ${targetInspection.refused} Nada foi gravado.`);
        }
        if (!targetInspection.exists) {
          fail('TARGET_MISSING', `O arquivo escolhido "${targetInspection.path}" não está no disco: não há o que inspecionar antes de confirmar o apontamento. Nada foi gravado.`);
        }
        if (targetInspection.readError) {
          fail('TARGET_UNREADABLE', `O arquivo escolhido "${targetInspection.path}" não pôde ser lido: ${targetInspection.readError}. Nada foi gravado.`);
        }
        if (!targetInspection.measurement?.sha256) {
          fail('TARGET_NOT_MEASURED', `O arquivo escolhido "${targetInspection.path}" existe mas não produziu SHA-256: o registro não pode passar a apontar para um arquivo sem hash medido. Nada foi gravado.`);
        }
        for (const item of targetInspection.measurement?.limitations ?? []) limitations.push(`destino: ${item}`);
        if (targetInspection.measurement.sha256 === recorded.sha256) {
          warnings.push('o arquivo escolhido tem exatamente o mesmo SHA-256 do registro atual: este apontamento não corrige divergência nenhuma.');
        }
        if (recorded.format && targetInspection.measurement.format && recorded.format !== targetInspection.measurement.format) {
          warnings.push(`o formato registrado muda de "${recorded.format}" para "${targetInspection.measurement.format}": confirme que o destino do asset continua aceitando este arquivo.`);
        }
      }

      if (operation === 'mark-superseded') {
        if (replacedByVersion === version) {
          fail('SELF_REPLACEMENT', `A versão "${version}" não pode ser marcada como substituída por ela mesma. Nada foi gravado.`);
        }
        if (replacedByVersion && !versions.some((item) => String(item?.version ?? '') === replacedByVersion)) {
          fail('REPLACEMENT_VERSION_NOT_FOUND', `A versão substituta "${replacedByVersion}" não existe no asset "${assetId}". Versões registradas: ${versions.map((item) => String(item?.version ?? '(sem rótulo)')).join(', ') || 'nenhuma'}. Nenhuma versão é inventada; nada foi gravado.`);
        }
        if (versionRecord.superseded) {
          warnings.push(`esta versão já estava marcada como substituída (${versionRecord.superseded.at ?? 'data não registrada'}); a nova decisão substitui a marca e as duas permanecem na auditoria.`);
        }
      }

      if (operation === 'register-new-version') {
        if (comparison?.state === 'ok') {
          warnings.push('o arquivo em disco confere com o registro (hash, tamanho e formato): a versão nova teria o mesmo conteúdo. A decisão continua sendo sua; nada é aprovado automaticamente.');
        }
        if (measured && measured.bytes === 0) {
          warnings.push('o arquivo tem 0 bytes: a versão nova apontaria para um arquivo vazio.');
        }
        if (measured && measured.measured !== true) {
          warnings.push('o conteúdo do arquivo não pôde ser decodificado (só tamanho, formato e SHA-256 foram medidos): a versão nova será registrada sem métricas de conteúdo.');
        }
      }

      const newVersionLabel = operation === 'register-new-version' ? nextVersionLabel(versions) : null;
      const measuredAt = new Date().toISOString();
      const before = {
        path: recorded.path,
        recorded,
        onDisk: fileFingerprint(inspection),
        comparisonState: comparison?.state ?? 'not-measured',
        comparisonReason: comparison?.reason ?? null,
        diverged: [...(comparison?.diverged ?? [])].map((item) => String(item)),
        exists: inspection.exists === true,
        versionExists: true,
        superseded: versionRecord.superseded ? { ...versionRecord.superseded } : null,
      };
      const origin = {
        measuredBy: 'reconciliation',
        measuredAt,
        fromVersion: version,
        operation,
        planId: null,
      };
      const after = operation === 'repoint'
        ? {
          path: targetInspection.path,
          sha256: targetInspection.measurement.sha256,
          bytes: Number.isInteger(targetInspection.measurement.bytes) ? targetInspection.measurement.bytes : null,
          format: targetInspection.measurement.format ?? null,
          version,
          replacedByVersion: null,
          filesTouched: false,
          origin,
        }
        : operation === 'register-new-version'
          ? {
            path: recorded.path,
            sha256: measured?.sha256 ?? null,
            bytes: Number.isInteger(measured?.bytes) ? measured.bytes : null,
            format: measured?.format ?? null,
            version: newVersionLabel,
            replacedByVersion: null,
            filesTouched: false,
            origin,
          }
          : {
            path: recorded.path,
            sha256: measured?.sha256 ?? null,
            bytes: Number.isInteger(measured?.bytes) ? measured.bytes : null,
            format: measured?.format ?? null,
            version,
            replacedByVersion,
            filesTouched: false,
            origin,
          };

      const planId = randomUUID();
      const createdAt = Date.now();
      origin.planId = planId;
      const state = planState({
        planId,
        operation,
        assetId,
        version,
        artifactPath: before.path,
        targetPath: operation === 'repoint' ? after.path : null,
        file: fileFingerprint(inspection),
        targetFile: targetInspection ? fileFingerprint(targetInspection) : null,
        store: storeFingerprint(store),
        asset: assetFingerprint(asset),
        replacementVersion: replacedByVersion,
        createdAt,
      });
      const token = reconciliationLedger.register(state);
      const history = reconciliationHistory(asset);

      return Object.freeze({
        schemaVersion: STUDIO_SERVICE_SCHEMA_VERSION,
        reconciliationSchemaVersion: RECONCILIATION_SCHEMA_VERSION,
        generatedAt: measuredAt,
        planId,
        token,
        expiresAt: new Date(createdAt + RECONCILIATION_TOKEN_TTL_MS).toISOString(),
        ttlMs: RECONCILIATION_TOKEN_TTL_MS,
        requiresConfirmation: true,
        confirmed: false,
        operation,
        operationLabel: RECONCILIATION_OPERATION_LABELS[operation] ?? operation,
        assetId,
        assetName: asset.name ?? asset.id,
        assetType: asset.type ?? null,
        rightsState: asset.rights?.state ?? 'unknown',
        version,
        artifactRole: artifact.role ?? 'artifact',
        actorPreview: describeActor({ uid: currentActorUid(), reviewer }),
        before: Object.freeze({ ...before }),
        after: Object.freeze({ ...after }),
        divergence: Object.freeze({
          state: before.comparisonState,
          reason: before.comparisonReason,
          diverged: Object.freeze([...before.diverged]),
        }),
        measuredNow: Object.freeze({
          path: before.path,
          exists: inspection.exists === true,
          symlink: inspection.symlink === true,
          readError: inspection.readError ?? null,
          format: measured?.format ?? null,
          formatSource: measured?.formatSource ?? null,
          bytes: Number.isInteger(measured?.bytes) ? measured.bytes : null,
          sha256: measured?.sha256 ?? null,
          contentDecoded: measured?.measured === true,
          summary: summarizeMeasurement(measured),
        }),
        target: targetInspection ? Object.freeze({
          path: targetInspection.path,
          exists: targetInspection.exists === true,
          symlink: targetInspection.symlink === true,
          readError: targetInspection.readError ?? null,
          format: targetInspection.measurement?.format ?? null,
          bytes: Number.isInteger(targetInspection.measurement?.bytes) ? targetInspection.measurement.bytes : null,
          sha256: targetInspection.measurement?.sha256 ?? null,
          contentDecoded: targetInspection.measurement?.measured === true,
          summary: summarizeMeasurement(targetInspection.measurement ?? null),
        }) : null,
        availableVersions: Object.freeze(versions.map((item) => Object.freeze({
          version: String(item?.version ?? ''),
          createdAt: item?.createdAt ?? null,
          runId: item?.runId ?? null,
          superseded: item?.superseded ? true : false,
          artifactCount: Array.isArray(item?.artifacts) ? item.artifacts.length : 0,
        }))),
        newVersionLabel,
        limitations: Object.freeze(limitations),
        warnings: Object.freeze(warnings),
        reason,
        history: Object.freeze({ ...history, entries: Object.freeze(history.entries) }),
        filesTouched: false,
        note: RECONCILIATION_PLAN_NOTES[operation] ?? 'Revise antes de confirmar: nada é aplicado por esta chamada.',
      });
    },

    /**
     * Confirma e aplica uma decisão de reconciliação já revisada.
     *
     * Exige `confirmed: true` e o token do plano. Antes de gravar, mede de novo e
     * compara com o estado que gerou o plano: se o arquivo ou o registro mudou, a
     * operação é interrompida e exige nova inspeção. A gravação é **uma só** —
     * versão/registro e auditoria entram no store juntos, ou nada entra.
     */
    async confirmArtifactReconciliation(input = {}) {
      if (input?.confirmed !== true) {
        fail('NOT_CONFIRMED', 'A reconciliação exige confirmação explícita depois da revisão do plano: nada foi aplicado. A interface só envia confirmed: true quando a pessoa revisou o que vai mudar e pediu para aplicar.');
      }
      const requested = normalizeReconciliationRequest(input);
      const { operation, assetId, version, reviewer, reason } = requested;
      const token = String(input.token ?? '').trim();
      const plan = reconciliationLedger.take(token);
      const planned = plan.state;

      // O token amarra operação, asset e versão: confirmar outra coisa com um plano
      // existente é recusa, não conveniência.
      if (operation !== planned.operation) {
        fail('OPERATION_MISMATCH', `O plano ${planned.planId} foi emitido para a operação "${planned.operation}" e a confirmação pediu "${operation}": nada foi aplicado. Faça um plano novo para a operação que você quer.`);
      }
      if (assetId !== planned.assetId || version !== planned.version) {
        fail('PLAN_TARGET_MISMATCH', `O plano ${planned.planId} foi emitido para o asset "${planned.assetId}", versão "${planned.version}": nada foi aplicado sobre "${assetId}" / "${version}". Faça um plano novo.`);
      }
      if (requested.replacedByVersion !== planned.replacementVersion) {
        fail('REPLACEMENT_MISMATCH', `O plano foi revisado com a versão substituta "${planned.replacementVersion ?? '(nenhuma)'}" e a confirmação pediu "${requested.replacedByVersion ?? '(nenhuma)'}": nada foi aplicado. Faça um plano novo para revisar a mudança.`);
      }
      if (operation === 'repoint' && requested.newPath && projectRelativeFrom(requested.newPath) !== planned.targetPath) {
        fail('TARGET_MISMATCH', `O plano foi revisado com o destino "${planned.targetPath}" e a confirmação pediu "${requested.newPath}": nada foi aplicado. Faça um plano novo para revisar o destino.`);
      }

      // Estado atual: store bruto + medição nova do arquivo registrado e do destino.
      const store = await readStoreForReconciliation();
      const located = locateReconciliationTarget({ store, assetId, version, artifactPath: planned.artifactPath });
      const { asset, versions, versionRecord, artifact } = located;
      const { recorded, inspection, targetInspection } = await measureReconciliationState({
        artifact,
        targetPath: planned.targetPath,
      });
      const current = {
        file: fileFingerprint(inspection),
        targetFile: targetInspection ? fileFingerprint(targetInspection) : null,
        store: storeFingerprint(store),
        asset: assetFingerprint(asset),
      };
      const drift = comparePlanState({ planned, current });
      if (!drift.ok) {
        fail('STATE_CHANGED', `O estado mudou depois da inspeção que gerou este plano: ${drift.changed.join('; ')}. Nada foi aplicado. Faça uma nova inspeção (planArtifactReconciliation) e revise de novo antes de confirmar.`);
      }

      const now = Date.now();
      const decidedAt = new Date(now).toISOString();
      const measured = inspection.measurement ?? null;
      const actor = describeActor({ uid: currentActorUid(), reviewer });
      const comparison = inspection.comparison ?? null;
      const before = {
        path: recorded.path,
        recorded,
        onDisk: fileFingerprint(inspection),
        comparisonState: comparison?.state ?? 'not-measured',
        comparisonReason: comparison?.reason ?? null,
        diverged: [...(comparison?.diverged ?? [])].map((item) => String(item)),
        exists: inspection.exists === true,
        versionExists: true,
        superseded: versionRecord.superseded ? { ...versionRecord.superseded } : null,
      };
      const after = { ...(operation === 'repoint'
        ? {
          path: targetInspection.path,
          sha256: targetInspection.measurement?.sha256 ?? null,
          bytes: Number.isInteger(targetInspection.measurement?.bytes) ? targetInspection.measurement.bytes : null,
          format: targetInspection.measurement?.format ?? null,
          version,
          replacedByVersion: null,
        }
        : {
          path: before.path,
          sha256: measured?.sha256 ?? null,
          bytes: Number.isInteger(measured?.bytes) ? measured.bytes : null,
          format: measured?.format ?? null,
          version: operation === 'register-new-version' ? nextVersionLabel(versions) : version,
          replacedByVersion: operation === 'mark-superseded' ? requested.replacedByVersion : null,
        }) };
      after.filesTouched = false;
      after.origin = {
        measuredBy: 'reconciliation',
        measuredAt: decidedAt,
        fromVersion: version,
        operation,
        planId: planned.planId,
      };

      const evidence = reconciliationEvidence({ sha256: after.sha256 ?? null, at: decidedAt, operation });
      const contentMetrics = operation === 'repoint'
        ? summarizeMeasurement(targetInspection?.measurement ?? null)
        : summarizeMeasurement(measured);
      const decision = {
        id: `reconciliacao-${randomUUID()}`,
        before,
        after,
        reason,
        divergenceReason: before.comparisonReason ?? null,
        contentMetrics,
        evidence,
        replacementVersion: operation === 'mark-superseded' ? requested.replacedByVersion : null,
      };
      if (operation === 'register-new-version') {
        if (!inspection.exists || !measured?.sha256) {
          fail('SOURCE_MISSING', `O arquivo registrado "${before.path}" não está mais no disco ou não produziu SHA-256: não há bytes para registrar como nova versão. Nada foi gravado.`);
        }
        decision.newVersion = after.version;
        decision.note = `Reconciliação: arquivo medido de novo em ${decidedAt}; versão ${version} preservada sem alteração.`;
        decision.artifacts = [{
          path: before.path,
          role: artifact.role ?? 'artifact',
          format: after.format ?? null,
          bytes: after.bytes ?? null,
          sha256: after.sha256 ?? null,
          validator: null,
          validated: false,
          validation: evidence.validation,
          contentMetrics,
        }];
      }

      let applied;
      try {
        applied = applyDecision({ store, assetId, version, operation, decision, actor, token, now });
      } catch (error) {
        if (error instanceof ReconciliationError) throw error;
        fail('DECISION_REFUSED', `A decisão não pôde ser aplicada ao registro: ${String(error?.message ?? error).slice(0, 240)} Nada foi gravado.`);
      }

      try {
        await writeStore(applied.store);
      } catch (error) {
        fail('WRITE_FAILED', `A decisão foi preparada mas a gravação de ${projectRelativeFrom(storeFile)} falhou: ${String(error?.message ?? error).slice(0, 240)} O registro anterior continua intacto (a escrita é atômica: arquivo temporário exclusivo e rename) e nenhuma auditoria parcial foi gravada. Nada foi aplicado.`);
      }

      const history = reconciliationHistory(applied.asset);
      return Object.freeze({
        schemaVersion: STUDIO_SERVICE_SCHEMA_VERSION,
        reconciliationSchemaVersion: RECONCILIATION_SCHEMA_VERSION,
        generatedAt: new Date().toISOString(),
        applied: true,
        operation,
        operationLabel: RECONCILIATION_OPERATION_LABELS[operation] ?? operation,
        assetId,
        assetName: applied.asset.name ?? applied.asset.id,
        version,
        entry: Object.freeze({ ...applied.entry }),
        versionAfter: applied.version ? Object.freeze({
          version: String(applied.version.version ?? ''),
          superseded: applied.version.superseded ? Object.freeze({ ...applied.version.superseded }) : null,
          artifacts: Object.freeze((applied.version.artifacts ?? []).map((item) => Object.freeze({
            path: String(item?.path ?? ''),
            role: item?.role ?? 'artifact',
            sha256: item?.sha256 ?? null,
            bytes: Number.isInteger(item?.bytes) ? item.bytes : null,
            format: item?.format ?? null,
            validated: item?.validated === true,
            previousCount: Array.isArray(item?.previous) ? item.previous.length : 0,
          }))),
        }) : null,
        newVersion: applied.newVersion ? Object.freeze({
          version: String(applied.newVersion.version ?? ''),
          createdAt: applied.newVersion.createdAt ?? null,
          note: applied.newVersion.note ?? null,
          artifacts: Object.freeze((applied.newVersion.artifacts ?? []).map((item) => Object.freeze({
            path: String(item?.path ?? ''),
            sha256: item?.sha256 ?? null,
            bytes: Number.isInteger(item?.bytes) ? item.bytes : null,
            format: item?.format ?? null,
            validated: item?.validated === true,
            validationStatus: item?.validation?.status ?? null,
          }))),
        }) : null,
        preservedVersions: versions.length,
        store: Object.freeze({
          path: projectRelativeFrom(storeFile),
          assetCount: Array.isArray(applied.store?.assets) ? applied.store.assets.length : 0,
          versionCount: Array.isArray(applied.asset?.versions) ? applied.asset.versions.length : 0,
          reconciliationTotal: Array.isArray(applied.asset?.reconciliations) ? applied.asset.reconciliations.length : 0,
          updatedAt: applied.store?.updatedAt ?? null,
        }),
        history: Object.freeze({ ...history, entries: Object.freeze(history.entries) }),
        filesTouched: false,
        rightsChanged: false,
        note: RECONCILIATION_CONFIRM_NOTES[operation] ?? 'Decisão gravada no registro e na auditoria do asset.',
      });
    },

    classifyRights,
    redactSecrets,
    sha256: hash,
  });
}

/** Versões de uma entrada do catálogo (helper local do filtro de busca). */
function versionsOf(entry) {
  return entry.versions ?? [];
}

/**
 * Teto de arquivos medidos por chamada de catálogo: medir é ler e decodificar, e
 * um projeto com muitas versões não pode virar uma varredura sem fim. O que ficou
 * de fora é reportado em `measureBudget.exhausted`, nunca medido pela metade em
 * silêncio.
 */
const CATALOG_MEASURE_BUDGET = 60;

/** Quantos runs (dos mais recentes) a inspeção de um arquivo percorre. */
const RUN_PROVENANCE_SCAN_LIMIT = 40;

/**
 * O que a revisão de cada operação precisa deixar claro antes da confirmação.
 * As três frases afirmam o mesmo limite: reconciliação não toca em arquivo.
 */
const RECONCILIATION_PLAN_NOTES = Object.freeze({
  'register-new-version': 'Revise antes de confirmar: o arquivo será medido de novo na hora de gravar e uma versão nova será criada com esse hash, tamanho, formato e métricas. A versão anterior continua intacta, com o caminho, o hash e as evidências que tinha — nada é reescrito retroativamente. Nenhum arquivo é criado, movido ou apagado, e os direitos declarados não mudam. Medição estrutural não é aprovação de qualidade visual.',
  repoint: 'Revise antes de confirmar: o registro desta versão passará a apontar para o arquivo de destino inspecionado agora. O caminho, o hash, o tamanho, o formato e a evidência de validação anteriores ficam preservados em previous[] e na auditoria. O arquivo antigo não é movido, renomeado nem apagado, e o caminho precisa estar dentro da pasta do projeto (symlink para fora é recusado sem leitura). Medição estrutural não é aprovação de qualidade visual.',
  'mark-superseded': 'Revise antes de confirmar: a versão será marcada como substituída. Nenhum arquivo e nenhum registro são apagados — a marcação é descritiva, e a divergência observada (hash, tamanho, formato e estado da comparação) fica preservada como evidência histórica junto com a decisão. Os direitos declarados não mudam. Medição estrutural não é aprovação de qualidade visual.',
});

/** O que a resposta de uma decisão aplicada afirma — e o que ela não afirma. */
const RECONCILIATION_CONFIRM_NOTES = Object.freeze({
  'register-new-version': 'Decisão gravada no registro do projeto e na auditoria do asset: uma versão nova foi criada com o que o arquivo é agora, e a versão anterior permanece sem alteração. Nenhum arquivo foi criado, movido, reescrito ou apagado. A versão nova entra sem validação: medição estrutural não é aprovação de qualidade visual.',
  repoint: 'Decisão gravada no registro do projeto e na auditoria do asset: o registro agora aponta para o arquivo escolhido, e o apontamento anterior (caminho, hash, tamanho, formato e evidência de validação) permanece em previous[]. Nenhum arquivo foi movido ou apagado. O artefato volta sem validação: a evidência anterior pertencia ao arquivo anterior, e medição estrutural não é aprovação de qualidade visual.',
  'mark-superseded': 'Decisão gravada no registro do projeto e na auditoria do asset: a versão está marcada como substituída, com a divergência observada preservada. Nenhum arquivo e nenhuma versão foram apagados. Nada aqui aprova ou reprova qualidade visual.',
});

export default createStudioService;
