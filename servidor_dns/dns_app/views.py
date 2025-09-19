from django.shortcuts import render
from django.http import JsonResponse
from .backend.dns_functions import query_upstream, parse_response 
from .backend.dns_cache import DNSCache                              
from .backend.dns_blocklist import blocklist_cache                  
import time
from datetime import datetime

cache = DNSCache(tamanho_maximo_bytes=50*1024)  # Cache com tamanho máximo de 50 KB
blocklist = blocklist_cache()                   # Blocklist de domínios

# Contadores globais
cache_hit_count = 0      # Contador de acertos no cache
upstream_hit_count = 0   # Contador de consultas ao servidor upstream
history = []             # Armazena últimos N acessos (histórico de consultas)

def query_domain(request):
    """
    Consulta de domínio via formulário.
    Retorna resultado renderizado em template HTML.
    """
    global cache_hit_count, upstream_hit_count, history

    result = None
    domain = request.GET.get('domain')          # Obtém domínio da requisição GET
    qtype = request.GET.get('type', 'A')        # Tipo de consulta, padrão 'A'
    cache_key = f"{domain}|{qtype}" if domain else None
    elapsed_time = None
    source = "upstream"                         # Fonte inicial (upstream)

    if domain:
        start_time = time.time()
        
        if blocklist.is_blocked(domain):
            result = f"Domínio {domain} está bloqueado!"
        else:
            cached = cache.get_key(cache_key)   # Tenta obter do cache local
            
            if cached:
                result = cached
                source = "cache"
                cache_hit_count += 1
            else:
                # Consulta ao servidor upstream se não estiver no cache
                resposta_bytes = query_upstream(domain, qtype)
                
                if resposta_bytes:
                    registros, ttl = parse_response(resposta_bytes, qtype)
                    
                    if registros:
                        if ttl is None:
                            ttl = 60  # TTL padrão

                        # Adiciona tipo de consulta aos registros
                        for r in registros:
                            r['qtype'] = qtype

                        cache.set_key(cache_key, registros, ttl)  # Armazena no cache
                        result = registros
                    else:
                        result = f"Nenhum registro válido encontrado para {domain} ({qtype})"
                else:
                    result = "Falha ao consultar o upstream."
                upstream_hit_count += 1

        elapsed_time = time.time() - start_time  # Calcula tempo de consulta

        history.append({
            'domain': domain,
            'qtype': qtype,
            'source': source,
            'result': result,
            'elapsed_time': f"{elapsed_time:.2f}s" if elapsed_time else None,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        # Mantém apenas os últimos 20 registros
        history = history[-20:]

    # Renderiza resultado no template HTML
    return render(request, 'dns_app/query_result.html', {
        'domain': domain,
        'qtype': qtype,
        'result': result,
        'elapsed_time': f"{elapsed_time:.2f}s" if elapsed_time else None,
        'source': source,
        'cache_hit': cache_hit_count,
        'upstream_hits': upstream_hit_count
    })


def index(request):

    """
    Página inicial mostrando:
    - Estado do cache
    - Quantidade de domínios bloqueados
    - Histórico de consultas
    - Contadores de hits
    """

    display_cache = {}
    keys_to_delete = []

    # Itera sobre cache para exibir registros válidos e remover expirados
    for key, entry in cache.cache.items():
        time_left = entry['expire_at'] - datetime.now().timestamp()
        if time_left <= 0:
            keys_to_delete.append(key)
            continue

        # Extrai nome de domínio e tipo de consulta
        domain_name, qtype = key.split('|', 1)
        registros = entry['value']
        formatted_records = []

        for r in registros:
            formatted_records.append({
                'name': r['name'],
                'address': r['address'],
                'qtype': qtype,
                'time_left': int(time_left)
            })
        display_cache[key] = formatted_records

    # Remove entradas expiradas do cache
    for key in keys_to_delete:
        cache.remove(key)

    # Renderiza página inicial
    return render(request, 'dns_app/index.html', {
        'cache': display_cache,
        'blocked_domains_count': len(blocklist.blocked_domains),
        'history': history,
        'cache_hit_count': cache_hit_count,
        'upstream_hit_count': upstream_hit_count
    })


def calcular_vazao(intervalo_segundos=60):

    """
    Calcula a vazão média de requisições por segundo nos últimos 'intervalo_segundos'. Retorna vazão total, vazão do cache e do upstream.
    """

    total_hits = cache_hit_count + upstream_hit_count
    vazao_total = total_hits / max(intervalo_segundos, 1)
    vazao_cache = cache_hit_count / max(intervalo_segundos, 1)
    vazao_upstream = upstream_hit_count / max(intervalo_segundos, 1)
    return vazao_total, vazao_cache, vazao_upstream


def vazao_json(request):

    """
    Retorna vazão em JSON, usado para atualização dinâmica via JavaScript.
    """

    vazao_total, vazao_cache, vazao_upstream = calcular_vazao(intervalo_segundos=60)
    return JsonResponse({
        'vazao_total': f"{vazao_total:.2f} req/s",
        'vazao_cache': f"{vazao_cache:.2f} req/s",
        'vazao_upstream': f"{vazao_upstream:.2f} req/s"
    })
