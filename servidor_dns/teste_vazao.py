import requests       
import threading       
import time            
import random          
import json            
from dns_app.backend.dns_blocklist import blocklist_cache 

# URL do endpoint de consulta do servidor DNS Django
URL = "http://127.0.0.1:8000/query/"

# Parâmetros do teste
DURACAO_TESTE = 60           # Duração do teste em segundos
THREADS_PARALELAS = 50       # Número máximo de threads simultâneas

# Contadores globais para resultados
sucesso = 0      
falhas = 0       
bloqueados = 0   
lock = threading.Lock()  # Lock para evitar condições de corrida nos contadores

# Carrega lista de domínios de um arquivo JSON
# Cada item do JSON deve ser um dicionário com a chave "target"
with open("dns_app/dns_modules/domains_list/backlink_rank.json", "r") as f:
    DOMINIOS = json.load(f)

# Inicializa a blocklist
blocklist = blocklist_cache()

def consulta(dominio):

    """
    Função que realiza a consulta de um domínio. Verifica se o domínio está bloqueado antes de contar como sucesso.
    """
    global sucesso, falhas, bloqueados
    params = {"domain": dominio, "type": "A"}  # Parâmetros da requisição GET
    try:
        # Faz a requisição HTTP para o endpoint Django
        resp = requests.get(URL, params=params, timeout=5)
        if resp.status_code == 200:
            # Verifica se o domínio está bloqueado
            if blocklist.is_blocked(dominio):
                with lock:
                    bloqueados += 1
            else:
                with lock:
                    sucesso += 1
        else:
            # Contabiliza falhas de status HTTP
            with lock:
                falhas += 1
    except Exception:
        # Contabiliza falhas de exceção, como timeout ou erro de rede
        with lock:
            falhas += 1

def teste_vazao():

    """
    Executa o teste de vazão criando múltiplas threads para consultar domínios. Mantém até THREADS_PARALELAS threads simultâneas e mede a duração do teste.
    """
    inicio = time.time()  # Marca o início do teste
    threads = []

    while time.time() - inicio < DURACAO_TESTE:
        # Seleciona um domínio aleatório da lista
        dominio = random.choice(DOMINIOS)

        # Cria uma thread para consultar o domínio
        t = threading.Thread(target=consulta, args=(dominio['target'],))
        threads.append(t)
        t.start()

        # Controla o número máximo de threads simultâneas
        if len(threads) >= THREADS_PARALELAS:
            threads_to_join = [t for t in threads if not t.is_alive()]
            for t in threads_to_join:
                t.join()
                threads.remove(t)

    # Aguarda todas as threads restantes terminarem
    for t in threads:
        t.join()

    fim = time.time()  # Marca o fim do teste
    duracao = fim - inicio  # Calcula o tempo total do teste

    # Calcula métricas do teste
    total_requisicoes = sucesso + falhas + bloqueados
    percentual_falhas = (falhas / total_requisicoes) * 100 if total_requisicoes > 0 else 0

    # Exibe os resultados do teste
    print("\n==== RESULTADOS ====")
    print(f"Requisições bem-sucedidas: {sucesso}")
    print(f"Falhas: {falhas}")
    print(f"Domínios bloqueados: {bloqueados}")
    print(f"Total de requisições: {total_requisicoes}")
    print(f"Percentual de falhas: {percentual_falhas:.2f}%")
    print(f"Tempo total (real): {duracao:.2f}s")
    print(f"Vazão calculada: {sucesso / duracao:.2f} req/s")


if __name__ == "__main__":
    teste_vazao()
