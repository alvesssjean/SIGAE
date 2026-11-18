class FilaDePrioridades:
    def __init__(self):
        self.v = []
    
    def _pai(self, i): return (i-1)//2
    def _esq(self, i): return 2 * i + 1
    def _dir(self, i): return 2* i + 2
    def tamanho(self): return len(self.v)
    def topo(self): return self.v[0]

    def inserir(self, valor):
        self.v.append(valor)
        self._subir(len(self.v) - 1)
    
    def _subir(self, i):
        while i > 0 and self.v[i] > self.v[self._pai(i)]:
            pai = self._pai(i)
            self.v[i], self.v[pai] = self.v[pai], self.v[i]
            i = pai

    def remover_topo(self):
        topo = self.[0]
        ultimo = self.v.pop()
        if self.v:
            self.v[0] = ultimo
            self._descer(0)
        return topo

    def _descer(self, i):
        n = len(self.v)
        while True:
            maior, e, d = i, self._esq(i), self._dir(i)
            if e < n and self.v[e] > self.v[maior]: maior = e
            if d < n and self.v[d] > self.v[maior]: maior = d
            if maior == i: break
            self.v[i], self.v[maior] = self.v[maior], self.v[i]