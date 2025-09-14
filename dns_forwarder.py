import socket # Permite enviar e receber pacotes UDP
from dnslib import DNSRecord, DNSHeader, DNSQuestion, QTYPE # Biblioteca para facilitar a construção de pacotes DNS

UPSTREAM_DNS = ("8.8.8.8", 53) # Servidor Google Public DNS, rápido e confiável

# Tipos de consulta DNS
QUERY_TYPES = {
    "A": 1, # IPv4
    "AAAA": 28, # IPv6
    "MX": 15 # Mail Exchange
}

def build_query(domain, query_type="A"):

    """
    Constrói um pacote DNS de consulta para enviar ao servidor upstream
    """
    
    qtype_enum = QTYPE.get(query_type.upper(), QTYPE.A) # Usa enumeração de dnslib
    request = DNSRecord(
        q=DNSQuestion(domain, qtype_enum)
    )
    return request.pack() # dnslib cuida do empacotamento

def query_upstream(domain, query_type="A"):
    """
    Envia uma consulta DNS para o servidor upstream via UDP e retorna a resposta.
    """
    
    try:
        qtype_enum = QTYPE.get(query_type.upper(), QTYPE.A)
        request = DNSRecord(q=DNSQuestion(domain, qtype_enum))

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)
        sock.sendto(request.pack(), UPSTREAM_DNS)
        response_data, _ = sock.recvfrom(1024) # Buffer maior para respostas
        return response_data
    except socket.timeout:
        print("Timeout ao consultar servidor upstream.")
        return None
    except Exception as e:
        print(f"Erro ao consultar servidor upstream: {e}")
        return None

def parse_query(data):
    """
    Faz o parsing de uma consulta DNS recebida de um cliente.
    """

    try:
        d = DNSRecord.parse(data)
        transaction_id = d.header.id
        domain = str(d.q.qname) # Fácil acesso ao nome
        qtype = d.q.qtype # Fácil acesso ao tipo
        return transaction_id, domain, qtype
    except Exception as e:
        # Tratar erros de parsing
        print(f"Erro ao parsear consulta: {e}")
        return None, None, None


if __name__ == "__main__":
    # Exemplo 1: Construir e parsear uma consulta
    domain_to_query = "www.google.com"
    query_packet = build_query(domain_to_query, "A")
    print(f"Consulta DNS construída para {domain_to_query}: {query_packet.hex()}")

    parsed_tid, parsed_domain, parsed_type = parse_query(query_packet)
    print(f"TID: {parsed_tid}, Domínio: {parsed_domain}, Tipo: {parsed_type}")
