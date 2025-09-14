from collections import OrderedDict
import sys
import time

class DNSCache:
    def __init__(self, tamanho_maximo_bytes = 10 * 1024):
        """
        Inicializa o cache DNS.

        Parâmetros:
        - tamanho_maximo_bytes: capacidade máxima estimada do cache em bytes.
          (Usamos uma estimativa simples com sys.getsizeof para chave/valor.)
        """
        self.tamanho_maximo_bytes = tamanho_maximo_bytes
        self.tamanho_atual_bytes = 0
        # OrderedDict preserva a ordem de inserção e permite mover itens para o fim,
        # o que facilita implementar uma política LRU (Least Recently Used).
        self.cache = OrderedDict()

    def calculate_entry_size(self, key, value):
        """
        Estima o tamanho (em bytes) de uma entrada do cache.
        """
        return sys.getsizeof(key) + sys.getsizeof(value)
    
    def remove(self, key = None):
        """
        Remove uma entrada do cache.

        - Se 'key' não for informada, remove o item mais antigo (LRU) usando popitem(last=False).
        - Caso contrário, remove a entrada associada à chave informada.
        """
        entry = None

        if not key:
            # Remove o primeiro item inserido/menos recentemente usado
            _, entry = self.cache.popitem(last=False)
        else:
            # Remove a entrada específica solicitada
            entry = self.cache.pop(key)
        
        # Subtrai o tamanho da entrada removida do total atual
        self.tamanho_atual_bytes -= entry["size"]
    
    def set_key(self, key, value, ttl):
        """
        Adiciona ou atualiza uma entrada de resposta DNS no cache.
        """
        
        # Se já existe, remove antigo (assim atualizamos tamanho e posição)
        if key in self.cache:
            self.remove(key)

        # Estimativa de tamanho da nova entrada
        tamanho_entrada = self.calculate_entry_size(key, value)
        # Momento (timestamp) em que a entrada expirará
        expire_at = time.time() + ttl

        # Armazena objeto com valor, tempo de expiração e tamanho
        self.cache[key] = {
            "value": value,
            "expire_at": expire_at,
            "size": tamanho_entrada,
        }

        # Garante que a chave esteja no final (mais recentemente usada)
        self.cache.move_to_end(key)

        # Atualiza contador total de bytes no cache
        self.tamanho_atual_bytes += tamanho_entrada

        # Evita ultrapassar o limite: remove itens mais antigos até caber
        while self.tamanho_atual_bytes > self.tamanho_maximo_bytes:
            self.remove()

    def get_key(self, key):
        """
        Recupera uma resposta do cache.
        """
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        
        # Verifica expiração pelo TTL (expire_at)
        if time.time() > entry["expire_at"]:
            # Remove a entrada expirada e retorna None
            self.remove(key)
            return None
        
        # Marca como recentemente usada: move para o fim
        self.cache.move_to_end(key)

        # Retorna apenas o valor (ex.: lista de registros A)
        return entry["value"]