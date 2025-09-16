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

## 📊 Avaliação de Desempenho

---

## 🖼️ Demonstração

---
