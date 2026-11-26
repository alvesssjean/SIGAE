
const VERMELHO = 'V', NEGRO = 'N';
let uidSeq = 0;

class RBInvalidaError extends Error {}

class No {
  constructor(chave, valor, cor = VERMELHO, pai = null) {
    this.uid = ++uidSeq;
    this.chave = chave;
    this.valor = valor;
    this.cor = cor;
    this.esq = null;
    this.dir = null;
    this.pai = pai;
  }
}

function compararChaves(a, b) {
  if (a[0] < b[0]) return -1;
  if (a[0] > b[0]) return 1;
  return a[1] - b[1];
}
const rotulo = (c) => `${c[0]}#${c[1]}`;
const nomeCor = (c) => (c === VERMELHO ? 'vermelho' : 'negro');
const corDe = (n) => (n === null ? NEGRO : n.cor);
function exigir(n) {
  if (n === null) throw new RBInvalidaError('estrutura inconsistente durante a operação');
  return n;
}

class RBTree {
  constructor(rastrear = false) {
    this.raiz = null;
    this.tamanho = 0;
    this.rastrear = rastrear;
    this.eventos = [];
  }

  foto() {
    const nos = [];
    if (this.raiz !== null) {
      const pilha = [this.raiz];
      while (pilha.length) {
        const n = pilha.pop();
        nos.push({
          uid: n.uid, chave: n.chave, cor: n.cor,
          esq: n.esq ? n.esq.uid : null,
          dir: n.dir ? n.dir.uid : null,
          pai: n.pai ? n.pai.uid : null,
        });
        if (n.dir) pilha.push(n.dir);
        if (n.esq) pilha.push(n.esq);
      }
    }
    return { raiz: this.raiz ? this.raiz.uid : null, nos };
  }

  _reg(texto, tipo, nos = [], extra = false) {
    if (this.rastrear) this.eventos.push({ texto, tipo, nos, extra, snap: this.foto() });
  }

  _pintar(no, cor) {
    if (no.cor !== cor) {
      const antiga = no.cor;
      no.cor = cor;
      this._reg(`recolorir ${rotulo(no.chave)}: ${nomeCor(antiga)} -> ${nomeCor(cor)}`, 'recolorir', [no.uid]);
    }
  }

  achar(chave) {
    let n = this.raiz;
    while (n !== null) {
      const c = compararChaves(chave, n.chave);
      if (c === 0) return n;
      n = c < 0 ? n.esq : n.dir;
    }
    return null;
  }
  contem(chave) { return this.achar(chave) !== null; }
  buscar(chave) { const n = this.achar(chave); return n === null ? null : n.valor; }

  caminho(chave) {
    const passos = [];
    let n = this.raiz;
    while (n !== null) {
      const c = compararChaves(chave, n.chave);
      passos.push({ uid: n.uid, chave: n.chave, c });
      if (c === 0) break;
      n = c < 0 ? n.esq : n.dir;
    }
    return passos;
  }

  altura() {
    const h = (n) => (n === null ? 0 : 1 + Math.max(h(n.esq), h(n.dir)));
    return h(this.raiz);
  }

  _minimo(no) { while (no.esq !== null) no = no.esq; return no; }
  _sucessor(no) {
    if (no.dir !== null) return this._minimo(no.dir);
    let pai = no.pai;
    while (pai !== null && no === pai.dir) { no = pai; pai = pai.pai; }
    return pai;
  }
  *emOrdem() {
    let no = this.raiz === null ? null : this._minimo(this.raiz);
    while (no !== null) { yield no; no = this._sucessor(no); }
  }

  inserir(chave, valor = null) {
    this.eventos = [];
    let pai = null;
    let atual = this.raiz;
    while (atual !== null) {
      const c = compararChaves(chave, atual.chave);
      if (c === 0) throw new Error(`chave duplicada: ${rotulo(chave)}`);
      pai = atual;
      atual = c < 0 ? atual.esq : atual.dir;
    }
    const novo = new No(chave, valor, VERMELHO, pai);
    if (pai === null) this.raiz = novo;
    else if (compararChaves(chave, pai.chave) < 0) pai.esq = novo;
    else pai.dir = novo;
    this.tamanho += 1;
    this._reg(`inserir ${rotulo(chave)} (nasce vermelho)`, 'inserir', [novo.uid]);
    this._corrigirInsercao(novo);
  }

  _corrigirInsercao(no) {
    while (no.pai !== null && no.pai.cor === VERMELHO) {
      let pai = no.pai;
      const avo = pai.pai;
      if (avo === null) break;
      if (pai === avo.esq) {
        const tio = avo.dir;
        if (tio !== null && tio.cor === VERMELHO) {
          this._reg('caso 1: tio vermelho, recolore pai, tio e avô', 'caso', [pai.uid, tio.uid, avo.uid]);
          this._pintar(pai, NEGRO); this._pintar(tio, NEGRO); this._pintar(avo, VERMELHO);
          no = avo;
        } else {
          if (no === pai.dir) {
            this._reg('caso 2: tio negro, nó em zigue-zague', 'caso', [no.uid, pai.uid, avo.uid]);
            no = pai;
            this._rotacionarEsquerda(no);
            pai = exigir(no.pai);
          }
          this._reg('caso 3: tio negro, nó em linha', 'caso', [no.uid, pai.uid, avo.uid]);
          this._pintar(pai, NEGRO); this._pintar(avo, VERMELHO);
          this._rotacionarDireita(avo);
        }
      } else {
        const tio = avo.esq;
        if (tio !== null && tio.cor === VERMELHO) {
          this._reg('caso 1: tio vermelho, recolore pai, tio e avô', 'caso', [pai.uid, tio.uid, avo.uid]);
          this._pintar(pai, NEGRO); this._pintar(tio, NEGRO); this._pintar(avo, VERMELHO);
          no = avo;
        } else {
          if (no === pai.esq) {
            this._reg('caso 2: tio negro, nó em zigue-zague', 'caso', [no.uid, pai.uid, avo.uid]);
            no = pai;
            this._rotacionarDireita(no);
            pai = exigir(no.pai);
          }
          this._reg('caso 3: tio negro, nó em linha', 'caso', [no.uid, pai.uid, avo.uid]);
          this._pintar(pai, NEGRO); this._pintar(avo, VERMELHO);
          this._rotacionarEsquerda(avo);
        }
      }
    }
    if (this.raiz !== null) this._pintar(this.raiz, NEGRO);
  }

  remover(chave) {
    this.eventos = [];
    const z = this.achar(chave);
    if (z === null) return false;
    this._reg(`remover ${rotulo(chave)}`, 'remover', [z.uid]);
    let y = z;
    let corOriginal = y.cor;
    let x, xPai;
    if (z.esq === null) {
      x = z.dir; xPai = z.pai;
      this._transplantar(z, z.dir);
    } else if (z.dir === null) {
      x = z.esq; xPai = z.pai;
      this._transplantar(z, z.esq);
    } else {
      y = this._minimo(z.dir);
      this._reg(`nó com dois filhos: sucessor ${rotulo(y.chave)} assume o lugar`, 'remover', [y.uid]);
      corOriginal = y.cor;
      x = y.dir;
      if (y.pai === z) {
        xPai = y;
      } else {
        xPai = y.pai;
        this._transplantar(y, y.dir);
        y.dir = z.dir;
        exigir(y.dir).pai = y;
      }
      this._transplantar(z, y);
      y.esq = z.esq;
      exigir(y.esq).pai = y;
      this._pintar(y, z.cor);
    }
    this.tamanho -= 1;
    if (corOriginal === NEGRO) {
      this._reg('o nó removido era negro: corrigir o duplo negro', 'remover', xPai ? [xPai.uid] : []);
      this._corrigirRemocao(x, xPai);
    } else {
      this._reg('o nó removido era vermelho: nenhuma correção necessária', 'remover', [], true);
      if (x !== null) this._pintar(x, NEGRO);
    }
    return true;
  }

  _transplantar(u, v) {
    if (u.pai === null) this.raiz = v;
    else if (u === u.pai.esq) u.pai.esq = v;
    else u.pai.dir = v;
    if (v !== null) v.pai = u.pai;
  }

  _corrigirRemocao(x, xPai) {
    while (x !== this.raiz && corDe(x) === NEGRO) {
      if (xPai === null) break;
      if (x === xPai.esq) {
        let w = exigir(xPai.dir);
        if (w.cor === VERMELHO) {
          this._reg('caso 1: irmão vermelho, troca cores e rotaciona', 'caso', [w.uid, xPai.uid]);
          this._pintar(w, NEGRO); this._pintar(xPai, VERMELHO);
          this._rotacionarEsquerda(xPai);
          w = exigir(xPai.dir);
        }
        if (corDe(w.esq) === NEGRO && corDe(w.dir) === NEGRO) {
          this._reg('caso 2: irmão negro e sobrinhos negros, sobe', 'caso', [w.uid, xPai.uid]);
          this._pintar(w, VERMELHO);
          x = xPai; xPai = x.pai;
        } else {
          if (corDe(w.dir) === NEGRO) {
            this._reg('caso 3: sobrinho distante negro, rotaciona', 'caso', [w.uid, w.esq.uid]);
            this._pintar(exigir(w.esq), NEGRO); this._pintar(w, VERMELHO);
            this._rotacionarDireita(w);
            w = exigir(xPai.dir);
          }
          this._reg('caso 4: sobrinho distante vermelho, finaliza', 'caso', [w.uid, xPai.uid, w.dir.uid]);
          this._pintar(w, xPai.cor); this._pintar(xPai, NEGRO); this._pintar(exigir(w.dir), NEGRO);
          this._rotacionarEsquerda(xPai);
          x = this.raiz; xPai = null;
        }
      } else {
        let w = exigir(xPai.esq);
        if (w.cor === VERMELHO) {
          this._reg('caso 1: irmão vermelho, troca cores e rotaciona', 'caso', [w.uid, xPai.uid]);
          this._pintar(w, NEGRO); this._pintar(xPai, VERMELHO);
          this._rotacionarDireita(xPai);
          w = exigir(xPai.esq);
        }
        if (corDe(w.esq) === NEGRO && corDe(w.dir) === NEGRO) {
          this._reg('caso 2: irmão negro e sobrinhos negros, sobe', 'caso', [w.uid, xPai.uid]);
          this._pintar(w, VERMELHO);
          x = xPai; xPai = x.pai;
        } else {
          if (corDe(w.esq) === NEGRO) {
            this._reg('caso 3: sobrinho distante negro, rotaciona', 'caso', [w.uid, w.dir.uid]);
            this._pintar(exigir(w.dir), NEGRO); this._pintar(w, VERMELHO);
            this._rotacionarEsquerda(w);
            w = exigir(xPai.esq);
          }
          this._reg('caso 4: sobrinho distante vermelho, finaliza', 'caso', [w.uid, xPai.uid, w.esq.uid]);
          this._pintar(w, xPai.cor); this._pintar(xPai, NEGRO); this._pintar(exigir(w.esq), NEGRO);
          this._rotacionarDireita(xPai);
          x = this.raiz; xPai = null;
        }
      }
    }
    if (x !== null) this._pintar(x, NEGRO);
  }

  _rotacionarEsquerda(x) {
    const y = x.dir;
    if (y === null) throw new Error('rotação à esquerda exige filho direito');
    x.dir = y.esq;
    if (y.esq !== null) y.esq.pai = x;
    y.pai = x.pai;
    if (x.pai === null) this.raiz = y;
    else if (x === x.pai.esq) x.pai.esq = y;
    else x.pai.dir = y;
    y.esq = x;
    x.pai = y;
    this._reg(`rotação à esquerda em ${rotulo(x.chave)}`, 'rotacao', [x.uid, y.uid]);
  }

  _rotacionarDireita(x) {
    const y = x.esq;
    if (y === null) throw new Error('rotação à direita exige filho esquerdo');
    x.esq = y.dir;
    if (y.dir !== null) y.dir.pai = x;
    y.pai = x.pai;
    if (x.pai === null) this.raiz = y;
    else if (x === x.pai.dir) x.pai.dir = y;
    else x.pai.esq = y;
    y.dir = x;
    x.pai = y;
    this._reg(`rotação à direita em ${rotulo(x.chave)}`, 'rotacao', [x.uid, y.uid]);
  }

  verificar() {
    const falha = { raiz: null, vermelhos: null, negra: null, ordem: null, pais: null, tamanho: null };
    let contados = 0;
    let bh = 0;
    if (this.raiz !== null) {
      if (this.raiz.cor !== NEGRO) falha.raiz = `a raiz ${rotulo(this.raiz.chave)} é vermelha`;
      if (this.raiz.pai !== null) falha.pais = 'a raiz não deve ter pai';
      const visitar = (no, min, max) => {
        if (no === null) return 1;
        contados += 1;
        if ((min !== null && !(compararChaves(no.chave, min) > 0)) ||
            (max !== null && !(compararChaves(no.chave, max) < 0))) {
          falha.ordem = falha.ordem ?? `ordem violada no nó ${rotulo(no.chave)}`;
        }
        for (const f of [no.esq, no.dir]) {
          if (f !== null && f.pai !== no) falha.pais = falha.pais ?? `pai inconsistente em ${rotulo(f.chave)}`;
          if (no.cor === VERMELHO && f !== null && f.cor === VERMELHO) {
            falha.vermelhos = falha.vermelhos ?? `dois vermelhos seguidos: ${rotulo(no.chave)} e ${rotulo(f.chave)}`;
          }
        }
        const he = visitar(no.esq, min, no.chave);
        const hd = visitar(no.dir, no.chave, max);
        if (he !== hd) falha.negra = falha.negra ?? `alturas negras diferentes abaixo de ${rotulo(no.chave)}`;
        return Math.max(he, hd) + (no.cor === NEGRO ? 1 : 0);
      };
      bh = visitar(this.raiz, null, null) - 1;
    }
    if (contados !== this.tamanho) falha.tamanho = `registrado ${this.tamanho}, alcançáveis ${contados}`;
    return { falha, bh, altura: this.altura(), nos: this.tamanho };
  }

  validar() {
    const { falha } = this.verificar();
    for (const k of Object.keys(falha)) {
      if (falha[k] !== null) throw new RBInvalidaError(falha[k]);
    }
  }
}

