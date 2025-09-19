import socket  # Permite criar soquetes para enviar e receber pacotes UDP
import threading

from dnslib import DNSRecord, DNSHeader, DNSQuestion, QTYPE, RCODE, RR, A, QTYPE_MAP # Biblioteca que facilita a criação e análise de pacotes DNS

from servidor_dns.dns_app.backend.dns_cache import DNSCache
from servidor_dns.dns_app.backend.dns_blocklist import blocklist_cache
from servidor_dns.dns_app.backend.dns_functions import QUERY_TYPES, query_upstream, parse_query, parse_response, get_blocked_response

from .config import UPSTREAM_DNS

def handle_client(data, addr, server_socket, cache, blocklist):
    """
    Processa uma única requisição DNS recebida pelo servidor.
    """
    try:
        # 1. Parsear consulta DNS recebida de cliente
        transaction_id, domain, qtype_val = parse_query(data)

        qtype_str = QTYPE.get(qtype_val, "A")

        if not domain:
            print(f"Erro ao parserar requisição de {addr}")
            return

        print(f"[QUERY] Recebido de {addr}: {domain} TIPO={qtype_str}")

        # 2. Verificar se o domínio está na blocklist
        if blocklist.is_blocked(domain):
            print(f"[BLOCKED] Domínio '{domain}' está na blocklist.")
            # Gera uma resposta NXDOMAIN (Domínio Inexistente) preservando o ID da transação
            blocked_response = blocklist.get_blocked_response(data)
            server_socket.sendto(blocked_response, addr)
            return

        # 3. Verificar se a resposta já existe no cache
        cache_key = f"{domain}|{qtype_str}"
        cached = cache.get_key(cache_key)

        if cached:
            print(f"[CACHE HIT] Resposta para '{domain}' encontrada no cache.")
                
            header = DNSHeader(id=transaction_id, qr=1, aa=1, rcode=0) # qr=1: Resposta; aa=1: Autoritativa
            question = DNSQuestion(domain, qtype_val)
            reply = DNSRecord(header, q=question)

            for record in cached:
                reply.add_answer(RR(
                    rname = domain,
                    rtype = QTYPE_MAP.get(record['type'], 1),
                    rclass = 1,
                    ttl = record['ttl'],
                    rdata = A(record['address'])
                ))
                
            server_socket.sendto(reply.pack(), addr)
            return

        # 4. Se não está bloqueado nem em cache, consultar o servidor upstream
        print(f"[FORWARD] Encaminhando '{domain}' para {UPSTREAM_DNS[0]}...")
        upstream_response_bytes = query_upstream(domain, qtype_str, transaction_id)

        if upstream_response_bytes:
            # 5. Enviar resposta do upstream diretamente ao cliente
            server_socket.sendto(upstream_response_bytes, addr)
            # E então, parsear a resposta para armazenar no cache
            records, ttl = parse_response(upstream_response_bytes, qtype_str)
            if records and ttl:
                print(f"[CACHE SET] Armazenando resposta para '{domain}' no cache por {ttl}s.")
                cache.set_key(cache_key, records, ttl)
        else:
            print(f"[ERROR] Falha ao obter resposta do upstream para '{domain}'.")
    except Exception as e:
        print(f"Erro ao processar requisição de {addr}: {e}")

def start_server(host = "0.0.0.0", port = 5353):
    """
    Inicializa o servidor DNS, o cache e a blocklist, e inicia o loop de escuta.
    """
    print("Iniciando o servidor DNS...")

    cache = DNSCache(tamanho_maximo_bytes=50 * 1024)  # cache com 50 KB
    blocklist = blocklist_cache() # Pode demorar no primeiro download

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        server_socket.bind((host, port))
        print(f"Servidor DNS escutando em {host}:{port}")
    except PermissionError:
        print(f"Erro de permissão para vincular à porta {port}. Tente uma porta > 1024 ou execute como root.")
        return
    except Exception as e:
        print(f"Erro ao vincular à porta {port}: {e}")
        return

    # Loop de execução infinito para receber consultas
    while True:
        try:
            data, addr = server_socket.recvfrom(4096)

            # Usamos multithread para atendermos múltiplas requisições simultaneamente
            client_thread = threading.Thread (
                target = handle_client, # Função que a thread vai realizar
                args = (data, addr, server_socket, cache, blocklist)
            )
            client_thread.daemon = True # Garantindo que a thread não bloqueie a finalização do programa
            client_thread.start()       # Inicializa
        
        except KeyboardInterrupt:
            print(f"\nServidor sendo desligado...")
            break
        except Exception as e:
            print(f"Ocorreu um erro: {e}")

    server_socket.close()
    print("Servidor desligado.")