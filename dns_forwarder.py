import socket  # Permite criar soquetes para enviar e receber pacotes UDP
from dnslib import DNSRecord, DNSHeader, DNSQuestion, QTYPE, RCODE  # Biblioteca que facilita a criação e análise de pacotes DNS
from dns_cache import DNSCache
from dns_blocklist import blocklist_cache

from config import UPSTREAM_DNS

# Dicionário de tipos de consulta DNS
QUERY_TYPES = {
    "A": 1,     # Resolve para endereços IPv4
    "AAAA": 28, # Resolve para endereços IPv6
    "MX": 15    # Registros de servidor de e-mail
}

def build_query(domain, query_type="A"):

    """
    Constrói um pacote DNS de consulta para enviar ao servidor upstream
    """
    
    # Obtém o valor numérico do tipo de consulta
    qtype_enum = QTYPE.get(query_type.upper(), QTYPE.A)

    # Cria um objeto de consulta DNS com o domínio e tipo desejado
    request = DNSRecord(
        q=DNSQuestion(domain, qtype_enum)
    )

    # Empacota o objeto em bytes (formato binário do protocolo DNS)
    return request.pack()

def query_upstream(domain, query_type="A"):

    """
    Envia uma consulta DNS para o servidor upstream via UDP e retorna a resposta
    """
    
    try:
        # Cria uma consulta DNS
        qtype_enum = QTYPE.get(query_type.upper(), QTYPE.A)
        request = DNSRecord(q=DNSQuestion(domain, qtype_enum))

        # Cria um soquete UDP
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)  # Define tempo máximo de espera de 5 segundos

        # Envia o pacote DNS para o servidor upstream
        sock.sendto(request.pack(), UPSTREAM_DNS)

        # Aguarda a resposta (máximo 1024 bytes)
        dado_resposta, _ = sock.recvfrom(1024)

        return dado_resposta  # Retorna os bytes da resposta recebida
    except socket.timeout:
        print("Timeout ao consultar servidor upstream.")
        return None
    except Exception as e:
        print(f"Erro ao consultar servidor upstream: {e}")
        return None

def parse_query(data):

    """
    Faz o parsing de uma consulta DNS recebida de um cliente
    """

    try:
        # Interpreta os bytes da consulta DNS em um objeto DNSRecord
        d = DNSRecord.parse(data)

        # Extrai o ID da transação
        id_transicao = d.header.id

        # Extrai o nome do domínio consultado
        dominio = str(d.q.qname)

        # Extrai o tipo da consulta
        qtype = d.q.qtype

        return id_transicao, dominio, qtype
    except Exception as e:
        print(f"Erro ao parsear consulta: {e}")
        return None, None, None

def parse_response(data):

    """
    Parseia uma resposta DNS recebida de um servidor upstream
    """

    try:
        # Converte os bytes da resposta em um objeto DNSRecord
        d = DNSRecord.parse(data)

        # Lista onde serão armazenados os registros de resposta do tipo A
        registros = []
        ttl = None

        # Percorre todos os registros de resposta
        for rr in d.rr:
            registros.append({
                "name": str(rr.rname),     # Nome do domínio
                "type": QTYPE[rr.rtype],   # Nome do tipo
                "address": str(rr.rdata),  # Endereço IPv4
                "ttl": rr.ttl               # Tempo de vida do registro
            })
            if ttl is None:
                ttl = rr.ttl  # Guarda o primeiro TTL encontrado

        # Retorna a lista de registros e o TTL do primeiro registro
        return registros, ttl
    
    except Exception as e:
        print(f"Erro ao parsear resposta: {e}")
        return [], None

def get_blocked_response(id_transicao):
    
    """ 
    Gera uma resposta NXDOMAIN para domínios bloqueados
    """
    
    # Converter de bytes para inteiro, se necessário
    if isinstance(id_transicao, bytes):
        id_transicao = int.from_bytes(id_transicao, "big")
    
    response = DNSRecord(
        header=DNSHeader(id=id_transicao, qr=1, rcode=RCODE.NXDOMAIN),
        q=DNSQuestion("blocked.domain", QTYPE.A)
    )

    return response.pack()


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
