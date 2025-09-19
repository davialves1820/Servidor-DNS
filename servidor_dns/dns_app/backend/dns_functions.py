import socket  # Permite criar soquetes para enviar e receber pacotes UDP
from dnslib import DNSRecord, DNSHeader, DNSQuestion, QTYPE, RCODE  # Biblioteca que facilita a criação e análise de pacotes DNS
from .config import UPSTREAM_DNS

# Dicionário de tipos de consulta DNS
QUERY_TYPES = {
    "A": 1,     # Resolve para endereços IPv4
    "AAAA": 28, # Resolve para endereços IPv6
    "MX": 15,   # Registros de servidor de e-mail
    "TXT": 16   # Registros de texto
}

def build_query(domain, query_type="A"):
    """
    Constrói um pacote DNS de consulta para enviar ao servidor upstream
    """
    query_type = query_type.upper()

    # Obtém o valor numérico do tipo de consulta corretamente
    if query_type in QUERY_TYPES:
        qtype_enum = QUERY_TYPES[query_type]
    else:
        qtype_enum = 1  # Default A

    request = DNSRecord(q=DNSQuestion(domain, qtype_enum))
    return request.pack()

def query_upstream(domain, query_type="A", transaction_id = None, timeout = 5):
    """
    Envia uma consulta DNS para o servidor upstream via UDP e retorna a resposta
    """
    try:
        query_type = query_type.upper()
        if query_type in QUERY_TYPES:
            qtype_enum = QUERY_TYPES[query_type]
        else:
            qtype_enum = 1  # Default A

        request = DNSRecord(q=DNSQuestion(domain, qtype_enum))
        if transaction_id is not None:
            request.header.id = int(transaction_id)

        # Cria socket UDP
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)

        # Envia a consulta para o servidor upstream
        sock.sendto(request.pack(), UPSTREAM_DNS)

        # Recebe a resposta (até 4096 bytes, para respostas maiores)
        resposta_bytes, _ = sock.recvfrom(4096)
        sock.close()

        if transaction_id is not None:
            try:
                response = DNSRecord.parse(resposta_bytes)
                response.header.id = int(transaction_id)
                return response.pack()
            except Exception:
                return resposta_bytes


        return resposta_bytes

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

def parse_response(data, query_type):
    """
    Parseia uma resposta DNS recebida de um servidor upstream
    """
    
    try:
        d = DNSRecord.parse(data)
        registros = []
        ttl = None

        for rr in d.rr:
            tipo = QTYPE[rr.rtype]

            if tipo != query_type.upper():
                continue  # ignora registros de outros tipos

            # Tratamento para diferentes tipos de rdata
            if tipo == "A" or tipo == "AAAA":
                address = str(rr.rdata)
            elif tipo == "MX":
                address = str(rr.rdata.exchange)  # MX tem atributo exchange
            else:
                address = str(rr.rdata)

            registros.append({
                "name": str(rr.rname),
                "type": tipo,
                "address": address,
                "ttl": rr.ttl
            })

            if ttl is None:
                ttl = rr.ttl

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