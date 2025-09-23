# 📌 Projeto Final – Redes de Computadores (2025.1)

## 👥 Integrantes
- Davi Alves Rodrigues
- Ryan Caetano Cesar de Araújo
- Diego de Carvalho Dias
  
---

## 📖 Descrição do Projeto

Este projeto foi desenvolvido como trabalho final da disciplina de **Redes de Computadores (2025.1)**.  
O objetivo principal é implementar um **resolvedor de DNS local com suporte a cache e bloqueio de domínios via blocklist**.

O sistema atua como um intermediário entre o cliente e os servidores DNS upstream, realizando:
- Armazenamento temporário de respostas DNS (cache local)
- Bloqueio de domínios maliciosos ou indesejados com base em uma lista de bloqueio (blocklist)
- Medição de desempenho em termos de tempo de resposta, acertos e falhas no cache

---

## 🛠️ Tecnologias Utilizadas

- Linguagem: **Python**
- Biblioteca padrão de **DNS** (socket, threading, time)

---

## Funcionalidades Principais

### 1. Encaminhamento de Consultas DNS (Forwarding)
- Recebe consultas DNS dos clientes.
- Caso o domínio não esteja bloqueado nem no cache, encaminha a consulta para um servidor DNS **upstream** (ex.: `8.8.8.8`, `1.1.1.1`).

### 2. Cache de Respostas DNS (com LRU e TTL)
- Armazena respostas localmente para reduzir latência e economizar tráfego.
- Expira entradas conforme o **TTL** retornado pelo upstream.
- Implementa política de substituição **Least Recently Used (LRU)**.
- Persiste em disco (`pickle`) e é carregado na inicialização.

### 3. Blocklist de Domínios
- Baixa e atualiza listas de bloqueio de URLs configuradas.
- Mantém cache local da blocklist com tempo de validade (TTL).
- Bloqueia domínios e subdomínios (ex.: `example.com` → `ads.example.com`).
- Retorna resposta **NXDOMAIN** para domínios bloqueados.

### 4. Respostas DNS Personalizadas
- **Domínios bloqueados** → gera resposta **NXDOMAIN** mantendo o ID da transação.
- **Domínios em cache** → monta resposta autoritativa com registros armazenados.
- **Domínios válidos** → consulta upstream e repassa resposta ao cliente.

### 5. Concorrência com Multithreading
- Processa múltiplas consultas em paralelo usando threads.
- Locks garantem consistência no cache e blocklist.

### 6. Monitoramento e Métricas
- Contadores globais:
  - **Cache hits** → consultas respondidas pelo cache.
  - **Upstream hits** → consultas enviadas ao servidor upstream.
- Histórico de consultas inclui:
  - Domínio consultado.
  - Tipo da consulta (A, AAAA, MX, TXT).
  - Fonte da resposta (cache, upstream, bloqueado).
  - Tempo de resposta.

### 7. Interface Web (Django)
- Página inicial exibe:
  - Estado atual do cache.
  - Quantidade de domínios bloqueados.
  - Histórico das últimas consultas.
  - Contadores de cache hits e upstream hits.
- Endpoint JSON fornece **vazão de requisições (req/s)**:
  - Total.
  - Cache.
  - Upstream.

### 8. Teste de Desempenho (Vazão)
- Script de stress test que:
  - Simula consultas simultâneas com múltiplas threads.
  - Mede taxa de sucesso, falhas e bloqueios.
  - Calcula a **vazão média (req/s)**.


## 🗂️ Organização



---

## 💻 Instruções de Uso

 **Clone o repositório**:
   ```bash
    git clone https://github.com/davialves1820/Servidor-DNS
    cd Servidor-DNS

    venv\Scripts\activate # Ativar o servidor venv

    cd servidor_dns # Entrar na pasta do projeto

    python manage.py runserver # Executar o projeto

    url: http://127.0.0.1:8000/

   ```

  **Encerrar a execução**
  ```
  Ctrl c no terminal encerra o servidor

  deactivate encerra o servidor venv
  ```

---
