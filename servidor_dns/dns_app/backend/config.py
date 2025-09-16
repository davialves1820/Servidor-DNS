# Configurações do servidor

# --- CONFIGURAÇÕES DE UPSTREAM ---

# Endereço do servidor DNS upstream (a quem enviaremos as consultas)
# Exemplos:
# Google: ("8.8.8.8", 53)
# Cloudflare: ("1.1.1.1", 53)
# Quad9: ("9.9.9.9", 53)
UPSTREAM_DNS = ("8.8.8.8", 53)  # Servidor público da Google (porta 53 é a padrão de DNS)

# ---CONFIGURAÇÃO DE CACHE---


# ---CONFIGURAÇÕES DA BLOCKLIST---
# Lista de URLs que contêm os domínios a serem bloqueados.
# Usaremos a lista base da Steven Black, que é bem conceituada e bloqueia anúncios e malware.
BLOCKLIST_URLS =[
    "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts"
]

# Diretório para guardar uma cópia local das listas de bloqueio.
BLOCKLIST_CACHE_DIR = "dns_app/dns_modules/blocklist_cache"

# TTL do cache local da blocklist, em segundos (86400 segundos = 24 horas).
BLOCKLIST_CACHE_TTL = 86400