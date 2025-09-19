from django.shortcuts import render
from .backend.dns_functions import query_upstream, parse_response
from .backend.dns_cache import DNSCache
from .backend.dns_blocklist import blocklist_cache
import time
from datetime import datetime

# Instâncias globais
cache = DNSCache(tamanho_maximo_bytes=50*1024)
blocklist = blocklist_cache()

# Histórico das últimas consultas
historico_consultas = []

# Contadores de hits
cache_hits = 0
upstream_hits = 0

def query_domain(request):
    """Consulta de domínio via formulário."""
    global cache_hits, upstream_hits
    result = None
    domain = request.GET.get('domain')
    qtype = request.GET.get('type', 'A')
    cache_key = f"{domain}|{qtype}" if domain else None
    elapsed_time = None
    source = "upstream"

    if domain:
        if blocklist.is_blocked(domain):
            result = f"Domínio {domain} está bloqueado!"
        else:
            start_time = time.time()
            cached = cache.get_key(cache_key)
            if cached:
                result = cached
                source = "cache"
                cache_hits += 1  # Incrementa contador de cache
            else:
                resposta_bytes = query_upstream(domain, qtype)
                if resposta_bytes:
                    registros, ttl = parse_response(resposta_bytes, qtype)
                    if registros:
                        if ttl is None:
                            ttl = 60
                        cache.set_key(cache_key, registros, ttl)
                        result = registros
                        upstream_hits += 1  # Incrementa contador de upstream
                    else:
                        result = f"Nenhum registro válido encontrado para {domain} ({qtype})"
                else:
                    result = "Falha ao consultar o upstream."
            elapsed_time = time.time() - start_time

        # Salva no histórico das últimas consultas
        historico_consultas.insert(0, {
            'domain': domain,
            'qtype': qtype,
            'result': result,
            'elapsed_time': f"{elapsed_time:.2f}s" if elapsed_time else None,
            'source': source,
            'timestamp': datetime.now()
        })

        if len(historico_consultas) > 20:
            historico_consultas.pop()

    return render(request, 'dns_app/query_result.html', {
        'domain': domain,
        'qtype': qtype,
        'result': result,
        'elapsed_time': f"{elapsed_time:.2f}s" if elapsed_time else None,
        'source': source,
        'cache_hits': cache_hits,
        'upstream_hits': upstream_hits
    })


def index(request):
    """Página inicial mostrando cache, blocklist e histórico."""
    display_cache = {}

    keys_to_delete = []
    for key, entry in cache.cache.items():
        time_left = entry['expire_at'] - datetime.now().timestamp()
        if time_left <= 0:
            keys_to_delete.append(key)
            continue

        registros = entry['value']
        formatted_records = []
        for r in registros:
            formatted_records.append({
                'name': r['name'],
                'address': r['address'],
                'qtype': r.get('qtype', 'A'),
                'time_left': int(time_left)
            })
        display_cache[key] = formatted_records

    for key in keys_to_delete:
        cache.remove(key)

    return render(request, 'dns_app/index.html', {
        'cache': display_cache,
        'blocked_domains_count': len(blocklist.blocked_domains),
        'historico': historico_consultas,
        'cache_hits': cache_hits,
        'upstream_hits': upstream_hits
    })
