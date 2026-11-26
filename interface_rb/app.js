/* Fila de atendimento: a árvore rubro-negra (rbtree.js) mantém a ordem de chegada por trás da tela. */
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const SITUACAO = { Aguardando: 'Aguardando', EmAtendimento: 'Em atendimento', Concluido: 'Concluído', Cancelado: 'Cancelado' };
const NOMES = ['Ana Souza', 'Bruno Lima', 'Carla Mendes', 'Diego Rocha', 'Elisa Prado', 'Fábio Nunes', 'Gabriela Dias',
  'Helena Costa', 'Igor Martins', 'Júlia Alves', 'Kleber Torres', 'Larissa Pinto', 'Murilo Ramos', 'Nádia Freitas'];

const estado = { pacientes: [], proximoId: 1, espera: new RBTree(), historico: new RBTree(), aba: 'espera' };

const dois = (n) => String(n).padStart(2, '0');
const formatar = (d) => `${d.getFullYear()}-${dois(d.getMonth() + 1)}-${dois(d.getDate())} ${dois(d.getHours())}:${dois(d.getMinutes())}:${dois(d.getSeconds())}`;
function lerHorario(texto) {
  const m = /^(\d{4})-(\d{2})-(\d{2}) ([01]\d|2[0-3]):([0-5]\d):([0-5]\d)$/.exec(texto.trim());
  if (!m) return null;
  const [a, me, di, h, mi, s] = m.slice(1).map(Number);
  const d = new Date(a, me - 1, di, h, mi, s);
  return d.getFullYear() === a && d.getMonth() === me - 1 && d.getDate() === di ? d : null;
}
const semAcento = (t) => t.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
const chave = (p) => [p.horario, p.id];

function avisar(msg, tipo = '') {
  const el = document.createElement('div');
  el.className = `aviso ${tipo}`;
  el.textContent = msg;
  $('avisos').appendChild(el);
  setTimeout(() => el.remove(), 3800);
}

/* ---------- ações ---------- */
function cadastrar(nome, risco, horarioTexto, silencioso = false) {
  const h = lerHorario(horarioTexto);
  if (!nome.trim()) return avisar('Informe o nome do paciente.', 'erro');
  if (!(risco >= 1 && risco <= 5)) return avisar('Classificação de risco inválida.', 'erro');
  if (!h) return avisar('Horário inválido. Use AAAA-MM-DD HH:MM:SS.', 'erro');
  const p = { id: estado.proximoId, nome: nome.trim(), risco, horario: formatar(h), situacao: 'Aguardando' };
  estado.espera.inserir(chave(p), p);
  estado.historico.inserir(chave(p), p);
  estado.pacientes.push(p);
  estado.proximoId += 1;
  if (!silencioso) avisar(`${p.nome} cadastrado (ID ${p.id}).`, 'ok');
  return p;
}

function porId(id) { return estado.pacientes[id - 1]; }

function sair(id, novaSituacao, mensagem) {
  const p = porId(id);
  if (!p || p.situacao !== 'Aguardando') return avisar('Só quem está aguardando pode sair da fila.', 'erro');
  estado.espera.remover(chave(p));
  p.situacao = novaSituacao;
  avisar(mensagem(p), 'ok');
}

function devolver(id) {
  const p = porId(id);
  if (!p || p.situacao !== 'EmAtendimento') return;
  estado.espera.inserir(chave(p), p);
  p.situacao = 'Aguardando';
  avisar(`${p.nome} voltou à fila na posição original.`, 'ok');
}

function concluir(id) {
  const p = porId(id);
  if (!p || p.situacao !== 'EmAtendimento') return;
  p.situacao = 'Concluido';
  avisar(`Atendimento de ${p.nome} concluído.`, 'ok');
}

/* ---------- telas ---------- */
function posicaoNaFila(p) {
  if (p.situacao !== 'Aguardando') return null;
  let i = 0;
  for (const no of estado.espera.emOrdem()) { i += 1; if (no.valor.id === p.id) return i; }
  return null;
}

function celulaRisco(p, editavel) {
  if (!editavel) return `<span class="risco r${p.risco}">${p.risco}</span>`;
  return `<select data-acao="risco" data-id="${p.id}" aria-label="Risco de ${esc(p.nome)}">` +
    [1, 2, 3, 4, 5].map((r) => `<option value="${r}"${r === p.risco ? ' selected' : ''}>${r}</option>`).join('') + '</select>';
}

function renderTabela() {
  const arv = estado[estado.aba];
  const linhas = [];
  let i = 0;
  for (const no of arv.emOrdem()) {
    i += 1;
    const p = no.valor;
    let acoes = '';
    if (p.situacao === 'Aguardando') {
      acoes = `<button class="btn sec mini" data-acao="chamar" data-id="${p.id}">Chamar</button>` +
        `<button class="btn sec mini" data-acao="cancelar" data-id="${p.id}">Cancelar</button>`;
    } else if (p.situacao === 'EmAtendimento') {
      acoes = `<button class="btn sec mini" data-acao="concluir" data-id="${p.id}">Concluir</button>` +
        `<button class="btn sec mini" data-acao="devolver" data-id="${p.id}">Devolver à fila</button>`;
    }
    linhas.push(`<tr><td class="num">${i}</td><td class="num">${p.id}</td><td>${esc(p.nome)}</td>` +
      `<td class="num">${esc(p.horario.slice(11))}<br><span class="suave">${esc(p.horario.slice(0, 10))}</span></td>` +
      `<td>${celulaRisco(p, p.situacao === 'Aguardando')}</td><td><span class="sit ${p.situacao}">${SITUACAO[p.situacao]}</span></td>` +
      `<td><div class="acoes">${acoes}</div></td></tr>`);
  }
  $('corpoTabela').innerHTML = linhas.join('') || '<tr><td colspan="7" class="suave">Nenhum paciente por aqui ainda.</td></tr>';
  $('infoTabela').textContent = estado.aba === 'espera'
    ? 'Quem chegou primeiro aparece primeiro.'
    : 'Todos os pacientes que já chegaram, em ordem de chegada.';
}

function renderChips() {
  const emAtendimento = estado.pacientes.filter((p) => p.situacao === 'EmAtendimento').length;
  $('chips').innerHTML =
    `<span class="chip">Aguardando <b>${estado.espera.tamanho}</b></span>` +
    `<span class="chip">Em atendimento <b>${emAtendimento}</b></span>` +
    `<span class="chip">Total de chegadas <b>${estado.historico.tamanho}</b></span>`;
}

function renderTudo() { renderTabela(); renderChips(); if (!$('cartaoBusca').hidden) buscar($('busca').value, true); }

/* ---------- busca por ID ou nome ---------- */
function buscar(texto, silencioso = false) {
  const termo = texto.trim();
  const cartao = $('cartaoBusca');
  if (!termo) { cartao.hidden = true; return; }
  let achados;
  if (/^\d+$/.test(termo)) {
    const p = porId(Number(termo));
    achados = p ? [p] : [];
  } else {
    const t = semAcento(termo);
    achados = estado.pacientes.filter((p) => semAcento(p.nome).includes(t));
  }
  cartao.hidden = false;
  $('corpoBusca').innerHTML = achados.map((p) => {
    const pos = posicaoNaFila(p);
    return `<tr><td class="num">${p.id}</td><td>${esc(p.nome)}</td><td class="num">${esc(p.horario.slice(11))}</td>` +
      `<td><span class="risco r${p.risco}">${p.risco}</span></td><td><span class="sit ${p.situacao}">${SITUACAO[p.situacao]}</span></td>` +
      `<td>${pos ? pos + 'º' : '-'}</td></tr>`;
  }).join('') || '<tr><td colspan="6" class="suave">Nenhum paciente encontrado.</td></tr>';
  if (!silencioso && !achados.length) avisar('Nenhum paciente encontrado.', 'erro');
}

/* ---------- relógio ---------- */
function aplicarRelogio() {
  const auto = $('relogioAuto').checked;
  $('horario').readOnly = auto;
  if (auto) $('horario').value = formatar(new Date());
}
setInterval(() => { if ($('relogioAuto').checked) $('horario').value = formatar(new Date()); }, 1000);

/* ---------- exemplo ---------- */
function gerarExemplo() {
  const base = new Date();
  base.setHours(8, 0, 0, 0);
  NOMES.slice(0, 12).forEach((nome, i) => {
    cadastrar(nome, 1 + ((i * 2) % 5), formatar(new Date(base.getTime() + i * 3 * 60000)), true);
  });
}

function limparTudo() {
  estado.pacientes = [];
  estado.proximoId = 1;
  estado.espera = new RBTree();
  estado.historico = new RBTree();
  $('cartaoBusca').hidden = true;
  $('busca').value = '';
}

/* ---------- eventos ---------- */
$('formCadastro').addEventListener('submit', (ev) => {
  ev.preventDefault();
  const p = cadastrar($('nome').value, Number($('risco').value), $('horario').value);
  if (p) {
    $('nome').value = '';
    if (!$('relogioAuto').checked) $('horario').value = formatar(new Date(lerHorario(p.horario).getTime() + 60000));
    renderTudo();
    $('nome').focus();
  }
});
$('relogioAuto').addEventListener('change', aplicarRelogio);
$('formBusca').addEventListener('submit', (ev) => { ev.preventDefault(); buscar($('busca').value); });
$('btnLimparBusca').addEventListener('click', () => { $('busca').value = ''; $('cartaoBusca').hidden = true; });
$('btnExemplo').addEventListener('click', () => { limparTudo(); gerarExemplo(); renderTudo(); });
$('btnLimpar').addEventListener('click', () => { limparTudo(); renderTudo(); avisar('Tudo limpo.'); });
for (const b of document.querySelectorAll('.aba')) b.addEventListener('click', () => {
  estado.aba = b.dataset.aba;
  for (const o of document.querySelectorAll('.aba')) o.setAttribute('aria-selected', String(o === b));
  renderTabela();
});
$('corpoTabela').addEventListener('click', (ev) => {
  const b = ev.target.closest('button[data-acao]');
  if (!b) return;
  const id = Number(b.dataset.id);
  const acao = b.dataset.acao;
  if (acao === 'chamar') sair(id, 'EmAtendimento', (p) => `${p.nome} chamado para atendimento.`);
  else if (acao === 'cancelar') sair(id, 'Cancelado', (p) => `Cadastro de ${p.nome} cancelado.`);
  else if (acao === 'devolver') devolver(id);
  else if (acao === 'concluir') concluir(id);
  renderTudo();
});
$('corpoTabela').addEventListener('change', (ev) => {
  const s = ev.target.closest('select[data-acao="risco"]');
  if (!s) return;
  const p = porId(Number(s.dataset.id));
  p.risco = Number(s.value);
  avisar(`Risco de ${p.nome} alterado para ${p.risco}.`, 'ok');
});

aplicarRelogio();
renderTudo();
