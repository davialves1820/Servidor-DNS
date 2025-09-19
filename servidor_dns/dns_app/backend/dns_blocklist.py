import os
import time
import threading
import urllib.request
from dnslib import DNSRecord

from .config import BLOCKLIST_URLS, BLOCKLIST_CACHE_DIR, BLOCKLIST_CACHE_TTL

class blocklist_cache:

    def __init__(self):

        """
        Inicializando a blocklist
        """
        
        self._lock = threading.Lock()   # Garantindo multithreading sem rece conditions
        self.blocked_domains = set()

        if not os.path.exists(BLOCKLIST_CACHE_DIR):  # Verificando se o diretorio do cache existe
            os.makedirs(BLOCKLIST_CACHE_DIR)        # Se não existir, criamos
        
        print("Atualizando a blocklist...")
        self.update_blocklists()
        print(f"Blocklist carregada com {len(self.blocked_domains)} dominios.")

    def update_blocklists(self):

        """
        Atualiza blocklist com blocklists dos urls 
        """

        new_domains = set()

        for url in BLOCKLIST_URLS:
            new_domains.update(self._download_and_cache_blocklist(url))

        with self._lock:
            self.blocked_domains = new_domains

        print(f"Blocklist atualizada, domínios bloqueados: {len(self.blocked_domains)}.")

    def _download_and_cache_blocklist(self, url):

        """
        Baixa blocklist dos urls, processa e retorna um set com todos os dominios bloqueados
        """

        try:
            filename = url.split("/")[-1]
            cache_path = os.path.join(BLOCKLIST_CACHE_DIR, filename)

            # Usa o cache local se for válido, do contrário, baixa uma nova versão
            if self._is_cache_valid(cache_path):
                print(f"Usando cache local para '{filename}'...")
                with open(cache_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                print(f"Baixando nova blocklist de {url}...")
                with urllib.request.urlopen(url) as response:
                    content = response.read().decode('utf-8')
                
                with open(cache_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # Processa o conteúdo para extrair os domínios
            new_domains = set()
            for line in content.splitlines():
                line = line.strip()
                # Ignora linhas de comentário e linhas vazias
                if line and not line.startswith("#"):
                    parts = line.split()
                    # O formato "hosts" geralmente é "IP dominio"
                    if len(parts) > 1:
                        domain = parts[1]
                        if domain not in ("localhost", "localhost.localdomain", "0.0.0.0"):
                            new_domains.add(domain)

            return new_domains

        except Exception as e:
            print(f"Erro ao processar blocklist {url}: {e}")
            return set()

    def _is_cache_valid(self, cache_path):

        """
        Verifica se cache ainda é válido com base no TTL
        """

        if not os.path.exists(cache_path):
            return False
        
        file_mod_time = os.path.getmtime(cache_path)
        return (time.time() - file_mod_time) < BLOCKLIST_CACHE_TTL  # Comparando se a ultima vez que o cache foi atualizado excede TTL
        
    def is_blocked(self, domain):

        """
        Verificando se um domínio está na blocklist
        """

        domain = domain.rstrip('.')
        
        with self._lock:
            if domain in self.blocked_domains:
                return True
            
            # Verifica domínios pai
            parts = domain.split('.')
            for i in range(1, len(parts)):
                parent_domain = '.'.join(parts[i:])
                if parent_domain in self.blocked_domains:
                    return True
        
            return False

    def get_blocked_response(self, query_packet):
        """
        Cria uma resposta DNS do tipo NXDOMAIN (Non-Existent Domain) para um domínio bloqueado,
        preservando o ID da transação original.
        """
        request = DNSRecord.parse(query_packet)
        reply = request.reply(rcode=3) # rcode 3 significa ID não existente
        return reply.pack()