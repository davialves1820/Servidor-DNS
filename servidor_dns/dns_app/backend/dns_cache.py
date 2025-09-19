from collections import OrderedDict
import sys
import os
import pickle
import time
import atexit
import threading

class DNSCache:
    def __init__(self, tamanho_maximo_bytes = 10 * 1024, cache_file_path = "./dns_cache.pkl"):
        """
        Inicializa o cache DNS.
        """
        self.tamanho_maximo_bytes = tamanho_maximo_bytes
        self.tamanho_atual_bytes = 0
        self.cache_file_path = cache_file_path
        # OrderedDict preserva a ordem de inserção e permite mover itens para o fim,
        # o que facilita implementar uma política LRU (Least Recently Used).
        self.cache = OrderedDict()
        # Lock para garantir concorrência segura
        self._lock = threading.Lock()

        # Carregar o cache do disco
        self._load_cache_from_disk()

        # Salvar o cache no disco ao sair do programa
        atexit.register(self._save_cache_to_disk)

    def _load_cache_from_disk(self):
        """
        Carrega o estado do cache (dicionário e tamanho) de um arquivo pickle.
        """
        if os.path.exists(self.cache_file_path):
            try:
                with open(self.cache_file_path, 'rb') as f:
                    data_to_load = pickle.load(f)
                    # Carrega tanto o cache quanto seu tamanho calculado
                    self.cache = data_to_load['cache']
                    self.tamanho_atual_bytes = data_to_load['tamanho_atual_bytes']
                    print(f"Cache carregado com sucesso de {self.cache_file_path}.")
            except Exception as e:
                print(f"Erro ao carregar cache de {self.cache_file_path}: {e}. Iniciando cache vazio.")
                # Se houver erro (ex: arquivo corrompido), começa do zero
                self.tamanho_atual_bytes = 0
                self.cache = OrderedDict()
        else:
            print("Arquivo de cache não encontrado. Iniciando cache vazio.")
            # Se o arquivo não existe, também começa do zero (será criado no primeiro 'set')

    def _save_cache_to_disk(self):
        """
        Salva o estado atual do cache (dicionário e tamanho) em um arquivo pickle.
        """
        try:
            with open(self.cache_file_path, 'wb') as f:
                data_to_save = {
                    'cache': self.cache,
                    'tamanho_atual_bytes': self.tamanho_atual_bytes
                }
                pickle.dump(data_to_save, f)
                print("Cache salvo em disco.")
        except Exception as e:
            print(f"Erro ao salvar cache em {self.cache_file_path}: {e}")

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
        with self._lock:
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

            # Atualiza contador total de bytes no cache
            self.tamanho_atual_bytes += tamanho_entrada

            # Evita ultrapassar o limite: remove itens mais antigos até caber
            while self.tamanho_atual_bytes > self.tamanho_maximo_bytes:
                self.remove()

    def get_key(self, key):
        """
        Recupera uma resposta do cache.
        """
        with self._lock:
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