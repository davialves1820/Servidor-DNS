from django.shortcuts import render
from .backend.dns_functions import query_upstream, parse_query, parse_response, get_blocked_response
from .backend.dns_cache import DNSCache
from .backend.dns_blocklist import blocklist_cache

import time
from datetime import datetime

# Instâncias globais
cache = DNSCache(tamanho_maximo_bytes=50*1024)
blocklist = blocklist_cache()

# Função para a página de consulta de domínio
def query_domain(request):
    # Inicializa variáveis para armazenar o resultado, tempo de execução e fonte da consulta
    result = None
    domain = request.GET.get('domain')
    qtype = request.GET.get('type', 'A')
    cache_key = f"{domain}|{qtype}" if domain else None

    elapsed_time = None
    source = "upstream" # Define o servidor DNS externo

    # Verifica se o dominio foi fornecido na requisição
    if domain:
        # Verifica se o dominio está na blocklist
        if blocklist.is_blocked(domain):
            result = f"Domínio {domain} está bloqueado!"
        else:
            start_time = time.time()
            cached = cache.get_key(cache_key) # Tenta obter a resposta do cache
            if cached:
                # Recupera apenas os registros do cache
                result = cached['value']
                source = "cache"
            else:
                # Se não encontrou no cache faz a consulta no servidor DNS
                resposta_bytes = query_upstream(domain, qtype)

                # Verifica se a busca retornou dados
                if resposta_bytes:
                    registros, ttl = parse_response(resposta_bytes, qtype)
                    
                    # Só salva se houver registros válidos
                    if registros:
                        if ttl is None:
                            ttl = 60
                        cache.set_key(cache_key, {
                            'value': registros,
                            'qtype': qtype
                        }, ttl)
                        result = registros
                    else:
                        result = f"Nenhum registro válido encontrado para {domain} ({qtype})"
                else:
                    result = "Falha ao consultar o upstream."
            
            end_time = time.time()
            elapsed_time = end_time - start_time

    return render(request, 'dns_app/query_result.html', {
        'domain': domain,
        'qtype': qtype,
        'result': result,
        'elapsed_time': f"{elapsed_time:.2f}s" if elapsed_time else None,
        'source': source
    })


# Página inicial com cache
def index(request):
    display_cache = {} # Armazenar dados da cache a serem exibidos

    # Itera sobre cada entrada no cache global
    for key, entry in cache.cache.items():
        # Calcula o tempo restante para a exibição da entrada na cache
        time_left = entry['expire_at'] - datetime.now().timestamp()
        time_left = max(0, int(time_left))

        # Cada item do cache pode ter múltiplos registros
        registros = entry['value']['value']  # lista de dicionários
        formatted_records = []

        # Itera sobre cada registro DNS dentro da cache
        for r in registros:
            formatted_records.append({
                'name': r['name'],       # será usado como chave
                'address': r['address'], # será usado como valor
                'qtype': entry['value']['qtype'],
                'time_left': time_left
            })
        
        display_cache[key] = formatted_records

    return render(request, 'dns_app/index.html', {
        'cache': display_cache,
        'blocked_domains_count': len(blocklist.blocked_domains),
    })
