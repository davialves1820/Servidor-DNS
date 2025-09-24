# 📌 Projeto Final – Redes de Computadores (2025.1)

## 👥 Integrantes
- Davi Alves Rodrigues
- Ryan Caetano Cesar de Araújo
- Diego de Carvalho Dias
  
---

## 📖 Descrição do Projeto

Este projeto foi desenvolvido como **trabalho final da disciplina de Redes de Computadores (2025.1)**.  
O objetivo principal foi implementar um **resolvedor de DNS local com suporte a cache e bloqueio de domínios via blocklist**, além de prover métricas de desempenho e uma interface web para monitoramento.

O sistema atua como um **intermediário entre os clientes e os servidores DNS upstream**, realizando:

- Encaminhamento de consultas DNS (forwarding).  
- Armazenamento temporário de respostas (cache local).  
- Bloqueio de domínios com base em listas de bloqueio.  
- Monitoramento de desempenho (tempo de resposta, cache hits, upstream hits).  

---

## 🛠️ Tecnologias Utilizadas
- **Python 3**  
- **Sockets** e **Threading** (para consultas DNS concorrentes)  
- **Pickle** (persistência do cache em disco)  
- **Django** (interface web e API JSON)  

---

## 🚀 Arquitetura do Sistema

O sistema foi dividido em **módulos principais**:

1. **Servidor DNS (Core):**
   - Recebe consultas DNS via UDP.
   - Encaminha para upstream (`8.8.8.8`, `1.1.1.1`) se necessário.
   - Retorna resposta ao cliente (cache, bloqueio ou upstream).

2. **Cache de Respostas (LRU + TTL):**
   - Reduz latência e tráfego.
   - Implementa política **Least Recently Used (LRU)**.
   - Expira entradas conforme o TTL definido pelo upstream.
   - Persistência em disco para reinicializações.

3. **Blocklist de Domínios:**
   - Baixa e atualiza listas de bloqueio.
   - Armazena localmente com TTL.
   - Bloqueia domínios e subdomínios.
   - Retorna resposta **NXDOMAIN**.

4. **Concorrência:**
   - Uso de **threads** para múltiplas consultas em paralelo.
   - **Locks** para garantir consistência no cache e blocklist.

5. **Monitoramento e Métricas:**
   - Contadores globais: cache hits, upstream hits, bloqueios.  
   - Histórico: domínio, tipo da consulta, fonte da resposta, tempo de resposta.  
   - Testes de desempenho com script de stress (requisições simultâneas).  

6. **Interface Web (Django):**
   - Painel com:
     - Estado do cache.
     - Número de domínios bloqueados.
     - Histórico de consultas.
     - Métricas de desempenho.  
   - API JSON para taxa de requisições (total, cache, upstream).  

---

## 📊 Resultados Obtidos

### Teste de Desempenho
- **Requisições bem-sucedidas:** 29.780  
- **Falhas:** 691  
- **Domínios bloqueados:** 7.919  
- **Total de requisições:** 38.390  
- **Percentual de falhas:** 1,80%  
- **Tempo total:** 64,71s  
- **Vazão calculada:** **460,21 req/s**  

### Benefícios
- Redução de latência nas consultas.  
- Menor tráfego externo de rede.  
- Filtragem de conteúdo indesejado e malicioso.  
- Controle sobre registros DNS internos/externos.  
- Proteção contra ataques de spoofing DNS.  

---

## 🖼️ Interface Web

A interface web desenvolvida em Django apresenta:  
- Estado atual do cache.  
- Histórico das últimas consultas.  
- Quantidade de domínios bloqueados.  
- Métricas de cache hits e upstream hits.  

> *(inserir prints da interface aqui)*

---

## 🗂️ Organização do Repositório
- `servidor_dns/` → Código do servidor e da interface web.  
- `blocklist/` → Gerenciamento da lista de bloqueios.  
- `cache/` → Implementação do cache e persistência.  
- `tests/` → Scripts de teste de carga e desempenho.  

---

## 💻 Instruções de Uso

Clone o repositório:
```bash
git clone https://github.com/davialves1820/Servidor-DNS
cd Servidor-DNS
```

Ative o ambiente virtual:
```bash
venv\Scripts\activate   # Windows
```

Execute o servidor:
```bash
cd servidor_dns
python manage.py runserver
```

Acesse no navegador:
```
http://127.0.0.1:8000/
```

Encerrar execução:
```
Ctrl + C  # encerra o servidor
deactivate  # encerra o ambiente virtual
```

---
