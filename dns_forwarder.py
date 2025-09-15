import socket  # Permite criar soquetes para enviar e receber pacotes UDP
from dnslib import DNSRecord, DNSHeader, DNSQuestion, QTYPE, RCODE  # Biblioteca que facilita a criação e análise de pacotes DNS
from dns_cache import DNSCache
from dns_blocklist import blocklist_cache
from dns_functions import query_upstream, parse_query, parse_response, get_blocked_response

from config import UPSTREAM_DNS

if __name__ == "__main__":

    
    cache = DNSCache(tamanho_maximo_bytes=50 * 1024)  # cache com 50 KB
    blocklist = blocklist_cache() # Pode demorar no primeiro download
    domain_to_query = "www.google.com"
    qtype = "A"
    cache_key = f"{domain_to_query}|{qtype}"

    if (blocklist.is_blocked(domain_to_query)):
        print(f"Dominio {domain_to_query} está na blocklist")

    else:
        # 1) Tenta obter do cache
        print(f"Procurando no cache por: {cache_key}")
        cached = cache.get_key(cache_key)
        if cached:
            print("Cache HIT! Registros encontrados no cache:")
            for r in cached:
                print(f"  - {r['name']} {r['type']} {r['address']} TTL={r['ttl']}")
        else:
            print("Cache MISS. Enviando consulta ao upstream...")
            # 2) Se não estiver em cache, consulta upstream
            resposta_bytes = query_upstream(domain_to_query, qtype)
            if resposta_bytes:
                registros, ttl = parse_response(resposta_bytes)
                if registros:
                    print("Resposta do upstream:")
                    for r in registros:
                        print(f"  - {r['name']} {r['type']} {r['address']} TTL={r['ttl']}")
                    # 3) Armazena no cache usando o TTL (se existir)
                    if ttl is None:
                        # Se não vier TTL, evita armazenar com expire_at = now
                        ttl = 60  # fallback: 60s
                    cache.set_key(cache_key, registros, ttl)
                    print(f"Armazenado no cache por {ttl} segundos.")
                else:
                    print("Upstream respondeu, mas não retornou registros A.")
            else:
                print("Falha ao obter resposta do upstream.")

        # 4) Demonstração: consulta novamente — agora deve ser cache hit
        print("\nConsultando novamente (espera-se cache hit):")
        cached2 = cache.get_key(cache_key)
        if cached2:
            print("Cache HIT (2º consulta):")
            for r in cached2:
                print(f"  - {r['name']} {r['type']} {r['address']} TTL={r['ttl']}")
        else:
            print("Ainda nenhum resultado no cache (pode ter expirado).")

# if __name__ == "__main__":

#     # Exemplo 1: Construir e parsear uma consulta
#     domain_to_query = "www.google.com"
#     query_packet = build_query(domain_to_query, "A")
#     print(f"Consulta DNS construída para {domain_to_query}: {query_packet.hex()}")

#     parsed_tid, parsed_domain, parsed_type = parse_query(query_packet)
#     print(f"TID: {parsed_tid}, Domínio: {parsed_domain}, Tipo: {parsed_type}")

#     # Exemplo 2: Consultar um servidor upstream
#     print(f"\nConsultando upstream para {domain_to_query}...")
#     dados_resposta = query_upstream(domain_to_query, "A")

#     if dados_resposta:
#         print(f"Resposta bruta do upstream ({len(dados_resposta)} bytes): {dados_resposta.hex()}")
#         registros, ttl = parse_response(dados_resposta)
#         print("Registros DNS na resposta:")
        
#         if registros:
#             for reg in registros:
#                 print(f"  - Nome: {reg['name']}, Tipo: {reg['type']} TTL: {reg['ttl']}, Endereço: {reg['address']}")
#             print(f"TTL padrão (primeiro registro): {ttl}")
#         else:
#             print("  Nenhum registro A encontrado na resposta.")
#     else:
#         print("Não foi possível obter resposta do servidor upstream.")

#     Exemplo 3: Gerar uma resposta NXDOMAIN
#     Suponha que a consulta original tivesse o transaction_id b'\x4e\x69'
#     original_transaction_id = b'\x4e\x69'
#     nxdomain_response = get_blocked_response(original_transaction_id)
#     print(f"\nResposta NXDOMAIN gerada: {nxdomain_response.hex()}")
