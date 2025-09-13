import socket # Permite enviar e receber pacotes UDP
import struct # Para empacotar e desempacotar bytes, formato de mensagens DNS
import threading # Permite atender múltiplos clientes simultaneamente, criando threads para cada requisição DNS]
from dnslib import DNSRecord # Biblioteca para facilitar a construção de pacotes DNS
import random

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
    
    # Cabeçalho DNS de 12 bytes: ID, Flags, QDCOUNT, ANCOUNT, NSCOUNT, ARCOUNT
    transaction_id = random.randint(0, 0xFFFF) # Gera um ID de 16 bits
    flags = 0x0100 # Define as características da consulta
    qdcount = 1 # Número de perguntas na seção
    header = struct.pack(">HHHHHH", transaction_id, flags, qdcount, 0, 0, 0)

    # Nome do domínio em formato DNS
    qname = b"".join(
        bytes([len(part)]) + part.encode() for part in domain.split(".")
    ) + b"\x00"

    qtype = QUERY_TYPES.get(query_type.upper(), 1) # Tipo de registro que está sendo consultado
    qclass = 1

    question = qname + struct.pack(">HH", qtype, qclass) # Empacota o tipo e a classe da pergunta

    return header + question # Retorna o pacote completo

def query_upstream(domain, query_type="A"):
    """
    Envia uma consulta DNS para o servidor upstream via UDP e retorna a resposta.
    """
    packet = build_query(domain, query_type) 
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Cria um socket
    s.settimeout(5) # Define um tempo limite de resposta de 5 segundos
    s.sendto(packet, UPSTREAM_DNS) # Envia os dados da consulta DNS para um servidor upstream
    response, _ = s.recvfrom(512) # Recebe resposta do servidor

    return response

if __name__ == "__main__":
    raw_response = query_upstream("example.com", "MX")
    print("Resposta recebida com", len(raw_response), "bytes") # Indica que o pacote de consulta foi aceito e houve resposta
