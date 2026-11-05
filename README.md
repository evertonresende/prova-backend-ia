# prova-backend-ia

Respostas da prova para Desenvolvedor Backend com foco em IA (Python). Enunciado: [PROVA.md](PROVA.md).

As três questões rodam numa API FastAPI só (`app/main.py`: um Swagger, uma seção por questão), e cada uma também roda pelo terminal.

| Questão | Pasta | Como rodar | Chave da OpenAI |
|---|---|---|---|
| 1. API de livros (FastAPI + SQLite) | `q1_livros/` | `python -m q1_livros.seed` e `uvicorn app.main:app --env-file .env` → http://localhost:8000/docs | não precisa |
| 2. Chatbot de Python (LangChain + OpenAI) | `q2_chatbot/` | `python -m q2_chatbot --demo` · `POST /chat` | **precisa** |
| 3. Busca semântica (embeddings + FAISS) | `q3_busca/` | `python -m q3_busca --demo` · `GET /busca` | não precisa |

Sem chave da OpenAI, roda tudo menos as respostas reais da Q2: a Q1, a Q3 e todos os testes offline.

## Requisitos e plataformas

Python **3.12 a 3.14** (o `numpy==2.5.4` exige 3.12+). O 3.15 ainda não: uma dependência indireta (`zstandard`, via `langsmith`) não tem wheel para ele e pediria um compilador C.

| Plataforma | Situação |
|---|---|
| Linux x86_64 | **testado** no CI: suíte offline (Python 3.12 e 3.14) e atalho só-Q1 (3.12). O modelo real da Q3 e a OpenAI real rodaram só em Linux (Ubuntu 24.04, Python 3.12), fora do CI |
| Windows x64 | **testado** no CI: suíte offline (Python 3.12). O CI não carrega o modelo real da Q3 |
| macOS Apple Silicon (macOS 14+) | os wheels existem; não testado |
| macOS Intel | **não suportado** na instalação completa (o torch 2.15 não tem wheel); a Q1 roda pelo atalho só-Q1 |
| Linux aarch64 | os wheels existem para Python 3.12 e 3.14; não testado |

O Python 3.13 está na faixa, mas fora do CI. Outras plataformas (Windows ARM64, por exemplo) não foram avaliadas.

## Instalação

Use **pip**, não uv. O `requirements.txt` busca o PyTorch só-CPU (`torch==2.15.0+cpu`, ~210 MB) num índice extra da PyTorch, e a estratégia de índices do uv pode não resolver esse pin. Se esse índice não responder, a instalação falha, em vez de baixar em silêncio a versão com CUDA (~3 GB).

Linux e macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Windows (PowerShell ou cmd):

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Se o PowerShell bloquear o `activate` (política de execução), rode antes `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

Depois, preencha a `OPENAI_API_KEY` no `.env` (só a Q2 precisa).

### Configuração (`.env`)

| Variável | Para quê |
|---|---|
| `OPENAI_API_KEY` | Obrigatória só na Q2. |
| `OPENAI_MODEL` | Opcional; padrão `gpt-6-luna`. Tem que ser um modelo de raciocínio (o código sempre manda `reasoning_effort`). **Não use `gpt-4`**: a OpenAI desligou esse modelo em 23/10/2026. |
| `LANGSMITH_*` | Opcionais: tracing da Q2 (veja LangSmith, na Q2). |
| `LIVROS_DB_PATH` | Opcional; arquivo SQLite da Q1. Padrão (inclusive se ficar vazio): `livros.db`, relativo à pasta atual. |

- Os CLIs (`python -m q2_chatbot` e `python -m q1_livros.seed`) leem o `.env` sozinhos. A API só o lê se subir com `uvicorn app.main:app --env-file .env`; mudou o `.env`, reinicie o uvicorn. Se o `.env` mudar o `LIVROS_DB_PATH`, suba a API com `--env-file .env`, ou ela e o seed vão usar arquivos diferentes.
- Rode os comandos da raiz do repositório (o `livros.db` é relativo à pasta atual).
- O `.env` (e qualquer `.env.*`) fica fora do git; só o `.env.example` é versionado.

## Testes

| Comando | O que roda | Tempo na máquina de dev (VPS Linux, só CPU) |
|---|---|---|
| `pytest` | 123 testes rápidos, sem rede e sem chave (modelos fake) | ~5 s |
| `pytest -m slow` | o modelo real de embeddings (precisa de rede ou do modelo no cache do Hugging Face, ~0,49 GB) | ~1 min |
| `pytest -m live` | uma chamada real à OpenAI (precisa de `OPENAI_API_KEY` no ambiente ou no `.env`) | ~10 s |
| `pytest -m "not live"` | os rápidos e os `slow` juntos | ~1 min |

- Uma chave no ambiente nunca dispara teste pago: o `tests/conftest.py` remove a `OPENAI_API_KEY` e desliga o tracing do LangSmith antes de qualquer import de biblioteca de IA.
- CI (GitHub Actions, `.github/workflows/testes.yml`), a cada push: `pytest` em Ubuntu (Python 3.12 e 3.14) e Windows (3.12), com chave falsa, tracing ligado e rede bloqueada; e o atalho só-Q1 em Ubuntu 3.12. Sem segredos. O `-m slow` fica fora do CI (baixaria o modelo a cada cache frio); a saída real dele está na seção da Q3.

## Atalho só-Q1

Se a pilha de IA não instalar (no macOS Intel, por exemplo), a Q1 roda sozinha:

```bash
pip install -r requirements-q1.txt
pytest tests/test_ambiente.py tests/test_q1_dados.py tests/test_q1_api.py
uvicorn app.main:app
```

- O `pytest` sem argumentos precisa do `requirements.txt` completo: sem a pilha de IA, os testes da Q2 e da Q3 nem carregam, e o `tests/test_app.py` falha.
- O app sobe só com a Q1, e o log mostra dois avisos esperados: `Q2 (chatbot) indisponível: falta o pacote openai. Instale o requirements.txt.` e `Q3 (busca) indisponível: falta o pacote faiss. Instale o requirements.txt.` O `/chat` e o `/busca` ficam fora do Swagger.

## Subir a API (Q1 + Q2 + Q3)

```bash
python -m q1_livros.seed
uvicorn app.main:app --env-file .env
```

Abra http://localhost:8000/docs (a raiz `/` redireciona para lá). Em cada rota: **Try it out** → **Execute**.

- Sem o arquivo `.env`, o uvicorn para com `Error: Invalid value for '--env-file': Path '.env' does not exist.` (crie com `cp .env.example .env`).
- Sem o `--env-file`, a API não enxerga o `.env`, e o `/chat` responde 503.
- Não ligue a recarga automática do uvicorn (a opção `reload`): sem o pacote `watchfiles`, ela varre o `.venv` inteiro a cada 0,25 s.
- Subir a API não exige chave nem baixa o modelo: a Q2 e a Q3 carregam o que precisam na primeira requisição.

## Q1 — API de livros

`q1_livros/`: FastAPI + SQLModel + SQLite. As tabelas nascem no startup e os dados ficam no `livros.db`, então sobrevivem a reinícios.

| Rota | O que faz | Respostas |
|---|---|---|
| `POST /livros` | cadastra `titulo`, `autor`, `data_publicacao` (AAAA-MM-DD) e `resumo` | 201 com o livro (com `id`) e o header `Location: /livros/{id}` · 422 |
| `GET /livros?titulo=…&autor=…` | busca por trecho, sem diferenciar maiúsculas nem acentos | 200 com a lista (sem resultado: `[]`, nunca 404) · 422 |
| `GET /livros/{id}` | consulta um livro | 200 · 404 `{"detail": "Livro não encontrado"}` · 422 |

`python -m q1_livros.seed` cadastra 10 livros brasileiros e pode rodar de novo: só entram os que faltam (`10 livro(s) cadastrado(s).`, depois `0 livro(s) cadastrado(s).`).

Exemplos em bash (no Windows, o Swagger faz o mesmo). Todo POST precisa do header `Content-Type: application/json`; sem ele, a resposta é 422 com `Input should be a valid dictionary or object to extract fields from`.

```bash
curl -X POST http://localhost:8000/livros -H "Content-Type: application/json" \
  -d '{"titulo": "São Bernardo", "autor": "Graciliano Ramos", "data_publicacao": "1934-01-01", "resumo": "Paulo Honório conta como conquistou a fazenda São Bernardo e perdeu Madalena."}'
curl "http://localhost:8000/livros?autor=jose"                # Iracema (José de Alencar)
curl "http://localhost:8000/livros?titulo=sertao"             # Grande Sertão: Veredas
curl "http://localhost:8000/livros?titulo=sao"                # São Bernardo, o livro do POST acima
curl "http://localhost:8000/livros?autor=MACHADO"             # os 2 livros de Machado de Assis
curl "http://localhost:8000/livros?autor=machado&titulo=dom"  # os dois filtros (E): Dom Casmurro
curl http://localhost:8000/livros/1
curl -G http://localhost:8000/livros --data-urlencode "autor=José"   # termo com acento
```

Termo com acento vai com `--data-urlencode`: cru na URL (`?autor=JOSÉ`), o uvicorn o recusa com 400 `Invalid HTTP request received.` antes de chegar ao app. O seed grafa "Erico Verissimo" sem acento, como o próprio autor assinava; `autor=érico` acha o livro dele do mesmo jeito.

Regras:

- **Busca:** por trecho, ignorando maiúsculas e acentos; com `titulo` e `autor`, o livro precisa atender aos dois (E); parâmetro vazio = sem filtro; ordem por `id`; `%` e `_` valem como texto, não como curinga; até 200 caracteres por filtro.
- **Cadastro:** os 4 campos são obrigatórios; os espaços das pontas saem; `titulo` e `autor` com 1 a 200 caracteres, `resumo` com 1 a 5000; data de calendário válida (`2026-02-30` dá 422). Livros repetidos e datas futuras são aceitos.
- **`id`:** inteiro de 1 a 2⁶³−1 (o limite do INTEGER do SQLite); fora disso, 422.
- **Seed:** quando só se sabe o ano de publicação, a data é 1º de janeiro.

## Q2 — Chatbot de Python

`q2_chatbot/`: LangChain 1.x (`create_agent`, sem ferramentas) + `ChatOpenAI` com o modelo `gpt-6-luna`. Precisa de `OPENAI_API_KEY` no `.env`.

```bash
python -m q2_chatbot          # conversa no terminal; "sair", Ctrl+C ou Ctrl+D encerram
python -m q2_chatbot --demo   # faz 3 perguntas fixas e sai
```

- **Código de saída:** 0 se deu certo (inclusive ao sair com Ctrl+C ou Ctrl+D); 1 sem chave ou se alguma pergunta da demo falhar.
- **Sem chave:** imprime `OPENAI_API_KEY não definida. Copie .env.example para .env e preencha a chave. A API só lê o .env se subir com: uvicorn app.main:app --env-file .env` e sai com 1, sem traceback.
- **Falha da OpenAI** (chave inválida, cota, timeout): imprime `Falha ao consultar o modelo da OpenAI. Tente de novo em instantes.` e uma linha `Detalhe: …` com o erro; no modo interativo, a conversa continua. O timeout é de 60 s por tentativa, com 2 novas tentativas: no pior caso, ~3 min até a mensagem.

### Saída real da `--demo`

`python -m q2_chatbot --demo`, rodado em 05/11/2026 com o código final (`gpt-6-luna`, esforço `medium`):

````text
Você: Como criar uma lista em Python?
Bot: Você pode criar uma lista em Python usando colchetes `[]`, separando os itens por vírgulas:

```python
# Lista de números
numeros = [1, 2, 3, 4]

# Lista de textos
frutas = ["maçã", "banana", "laranja"]

# Lista com tipos diferentes
dados = ["Ana", 25, True]
```

Uma lista vazia pode ser criada assim:

```python
itens = []
```

Para acessar um item, use seu índice. A contagem começa em `0`:

```python
frutas = ["maçã", "banana", "laranja"]

print(frutas[0])  # maçã
```

Também é possível adicionar itens depois:

```python
frutas.append("uva")
```

Você: E como adiciono um item nela?
Bot: Use o método `append()` para adicionar um item ao final da lista:

```python
frutas = ["maçã", "banana"]

frutas.append("laranja")

print(frutas)  # ['maçã', 'banana', 'laranja']
```

Se quiser inserir o item em uma posição específica, use `insert()`:

```python
frutas.insert(1, "uva")  # Insere "uva" na posição de índice 1

print(frutas)  # ['maçã', 'uva', 'banana', 'laranja']
```

Você: Qual é a capital da França?
Bot: Desculpe, só posso ajudar com assuntos relacionados a Python. Se quiser, posso mostrar como guardar `"Paris"` em uma variável ou em uma lista.
````

A 2ª pergunta só faz sentido com o histórico ("nela" é a lista da 1ª resposta), e o bot continua na mesma lista `frutas`. A 3ª, fora do tema, é redirecionada para Python.

### `POST /chat`

```bash
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"pergunta": "Como criar uma lista em Python?"}'
# {"resposta": "...", "conversa_id": "beb3854c-45e1-41f0-9a41-5261481ee0a4"}

# troque ID-DEVOLVIDO-ACIMA pelo conversa_id da resposta anterior
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"pergunta": "E como adiciono um item nela?", "conversa_id": "ID-DEVOLVIDO-ACIMA"}'
```

- Sem `conversa_id` (ou com ele vazio), o servidor abre uma conversa nova e devolve o id dela (um UUID); reenviar o mesmo id continua a conversa.
- **422:** corpo inválido (`pergunta` vazia ou com mais de 4000 caracteres, `conversa_id` com mais de 100), com ou sem chave no servidor.
- **503:** servidor sem `OPENAI_API_KEY` (só para uma pergunta válida); o resto da API continua de pé.
- **502:** falha da OpenAI; o cliente recebe só a mensagem genérica, e o detalhe vai para o log do servidor.

### Memória

- O checkpointer `InMemorySaver` (LangGraph) guarda as mensagens de cada conversa sob um `thread_id`, e cada `conversa_id` é usado como `thread_id`: conversas diferentes não se misturam. O prompt de sistema não entra no histórico; o agente o põe na frente das mensagens a cada chamada.
- Um chatbot por processo. O CLI usa uma conversa por execução.
- **Limites:** a memória é volátil (some quando o processo reinicia) e não tem teto de turnos nem de conversas (o exemplo do Swagger, sem `conversa_id`, abre uma conversa nova a cada **Try it out**). Uma pergunta que falhou continua no histórico.

### Modelo

- **`gpt-6-luna`, não GPT-4:** o `gpt-4` e o `gpt-4-turbo`, citados no enunciado, foram desligados em 23/10/2026; o GPT-4o e o GPT-4.1 saem em 14/01/2027, e a OpenAI indica o `gpt-6-luna` no lugar deles. É o modelo de texto mais barato (US$ 0,10 / 0,50 por 1M de tokens de entrada / saída, em 04/11/2026). Fonte: https://developers.openai.com/api/docs/deprecations. Com `OPENAI_MODEL=gpt-4`, toda pergunta falha.
- **Esforço de raciocínio `medium`:** com `low`, o bot ignorava a regra de escopo e respondia "A capital da França é Paris." (8 de 8 execuções da demo); com `medium`, redirecionou em 9 de 10, com a mesma latência (~9 s na primeira chamada, ~2 s nas seguintes).
- **Sem `temperature`/`top_p`:** a OpenAI manda tirá-los nos modelos de raciocínio quando o esforço não é `none`, e o `langchain-openai` não os remove sozinho para a família gpt-6.

### LangSmith

Liga só por variáveis no `.env` (veja o `.env.example`), sem mudar código:

- `LANGSMITH_TRACING=true`, em minúsculas (`True` não liga), e `LANGSMITH_API_KEY`.
- **Um** destino, nunca os dois (com os dois, o SDK para de registrar traces): `LANGSMITH_PROJECT` (workspace por projeto, o mais comum) **ou** `LANGSMITH_AGENT_ID` + `LANGSMITH_AGENT_ENVIRONMENT` (workspace por agente). `LANGSMITH_ENDPOINT` só para conta fora dos EUA.
- Cada run leva a tag e o metadata `origem` (`cli` ou `api`). O `thread_id` (o `conversa_id`) vai no metadata, e o LangSmith agrupa cada conversa como uma thread. O CLI espera os traces subirem antes de sair.
- Sem `LANGSMITH_API_KEY`, deixe `LANGSMITH_TRACING=false`: ligado sem chave, nada quebra, mas o CLI imprime avisos do LangSmith e demora para sair.

Esta entrega não tem conta no LangSmith, por isso não há print de trace.

## Q3 — Busca semântica

`q3_busca/`: 20 posts originais em PT-BR sobre Python (`q3_busca/corpus/`), embeddings do `intfloat/multilingual-e5-small` (via sentence-transformers) e índice FAISS.

```bash
python -m q3_busca --demo                                    # rode uma vez antes de usar o /busca
python -m q3_busca "como ler um arquivo linha por linha" -k 5
curl -G http://localhost:8000/busca --data-urlencode "q=como isolar as bibliotecas de cada projeto?" -d k=3
```

- **Primeira vez:** baixa o modelo (~0,49 GB, para o cache do Hugging Face; só o necessário, não o repositório inteiro de 2,28 GB) e cria o índice em `q3_busca/.indice/`. Depois disso, cada execução só carrega o modelo.
- **CLI:** os resultados vão para o stdout; no stderr aparecem `Carregando o modelo de embeddings (na primeira vez baixa ~0,49 GB)...`, a barra `Loading weights`, avisos do Hub do Hugging Face (no primeiro download, também as barras dele) e, quando o índice é criado, uma linha avisando. `-k` padrão 3; acima do tamanho do corpus, devolve os 20 posts; `-k 0` sai com código 2.
- **API:** `GET /busca?q=…&k=3`, com `q` de 1 a 500 caracteres e `k` de 1 a 10; fora disso, 422 na hora, sem carregar o modelo. A primeira busca de cada processo carrega o modelo: 13 s na máquina de dev, com o índice já criado pelo `--demo` (sem o índice, ela também gera os embeddings dos posts; numa máquina nova, ainda baixa o modelo). As seguintes levam ~0,07 s. Numa máquina nova e sem rede, o modelo não baixa e o `/busca` responde 500.

### Como funciona, passo a passo

1. **Corpus.** `carregar_corpus` lê os 20 posts Markdown, de 150 a 250 palavras cada, com o título na primeira linha (`# …`).
2. **Prefixos do e5.** O e5 foi treinado com um prefixo que diz o papel do texto: cada post vira `passage: ` + título + corpo, e cada consulta vira `query: ` + texto. Os prefixos são postos à mão porque o modelo não traz `config_sentence_transformers.json`: os `prompts` dele ficam vazios, e o `encode_query`/`encode_document` do sentence-transformers não acrescentaria nada. Sem os prefixos, a busca piora sem erro nenhum.
3. **Embeddings.** O `encode` do sentence-transformers tokeniza o texto, passa os tokens pelo encoder do `transformers` (tipo BERT, que devolve um vetor por token), tira a média desses vetores (mean pooling) e normaliza o resultado para norma 1: um vetor de 384 números por texto. O e5 lê até 512 tokens e corta o resto em silêncio; o maior post (`14-arquivos.md`) tem 489, e um teste `slow` confere todos. Não há chunking.
4. **Índice.** Um `faiss.IndexFlatIP` guarda os 20 vetores. Como eles têm norma 1, o produto interno (IP) é exatamente o cosseno do ângulo entre eles. A busca é exata (compara a consulta com todos), o certo para 20 posts.
5. **Cache em disco.** `q3_busca/.indice/` guarda o índice (`faiss.serialize_index` + I/O do Python, porque o `write_index` do FAISS usa o `fopen` do C e quebra em caminho com acento no Windows; o teste disso roda no Windows do CI) e um `metadados.json` com a impressão digital (SHA-256 do nome do modelo + conteúdo do corpus). Se o corpus ou o modelo mudar, o índice é refeito sozinho. As gravações são atômicas (arquivo temporário + `os.replace`). Para forçar a reconstrução, ou se o cache se corromper, apague a pasta.
6. **Consulta.** `query: ` + texto → vetor → `index.search` → os `k` posts de maior score. Posição sem vizinho (id `-1` do FAISS) é descartada.

### Resultados reais da `--demo`

Top-3 de `python -m q3_busca --demo` com o código final (score = cosseno):

| Consulta | 1º | 2º | 3º |
|---|---|---|---|
| encontrar todos os endereços de e-mail dentro de um texto | `16-regex.md` 0.888 | `18-f-strings.md` 0.839 | `06-geradores.md` 0.839 |
| medir quanto tempo uma função demora para rodar | `05-decorators.md` 0.877 | `10-pytest.md` 0.860 | `06-geradores.md` 0.860 |
| que horas são em Tóquio agora? | `15-datetime.md` 0.824 | `20-requisicoes-http.md` 0.797 | `12-asyncio.md` 0.793 |
| por que meu programa com várias threads não fica mais rápido? | `13-threads-processos-gil.md` 0.876 | `12-asyncio.md` 0.863 | `14-arquivos.md` 0.860 |
| como isolar as bibliotecas de cada projeto? | `09-ambientes-virtuais.md` 0.843 | `07-context-managers.md` 0.825 | `13-threads-processos-gil.md` 0.821 |

- **A última consulta não tem palavra de conteúdo em comum com nenhum post do corpus:** "isolar", "bibliotecas" e "projeto" não aparecem em nenhum deles; o post de ambientes virtuais fala em "dependências", "pacotes" e "aplicação". Uma busca por palavras-chave não teria por onde começar, e a busca por significado põe o post certo em 1º. Um teste confere que ela não tem palavra de conteúdo em comum com o post esperado, e o teste `slow`, o 1º lugar das 5 consultas.
- Na consulta do tempo de execução, uma busca ingênua por palavras-chave (contar as palavras em comum) escolheria `12-asyncio.md`: 3 palavras em comum, contra 2 do post de decorators.

<details>
<summary>Saída completa do <code>--demo</code></summary>

```text
Consulta: "encontrar todos os endereços de e-mail dentro de um texto"
  1. [0.888] Expressões regulares com o módulo re (16-regex.md)
     Expressões regulares descrevem padrões de texto. Com elas, você valida o formato de um CEP, extrai todos os e-mails de um documento ou muda datas de formato, tudo em poucas linhas. Em Python, elas fic…
  2. [0.839] Formatando textos com f-strings (18-f-strings.md)
     As f-strings, que chegaram no Python 3.6, são a forma mais direta de montar textos com valores dentro. Basta colocar um `f` antes das aspas e escrever qualquer expressão entre chaves: Depois dos dois-…
  3. [0.839] Geradores e a palavra-chave yield (06-geradores.md)
     Uma função comum calcula tudo e devolve o resultado de uma vez. Um gerador faz diferente: entrega um valor por vez, só quando alguém pede o próximo. Basta usar `yield` no lugar de `return`: Chamar `co…

Consulta: "medir quanto tempo uma função demora para rodar"
  1. [0.877] Decorators: comportamento extra sem mexer na função (05-decorators.md)
     Em Python, funções são objetos: podem ser guardadas em variáveis, passadas como argumento e devolvidas por outras funções. Um decorator aproveita isso. Ele é uma função que recebe outra função e devol…
  2. [0.860] Testes automatizados com pytest (10-pytest.md)
     Testar na mão, rodando o programa e conferindo a saída, funciona até a terceira mudança no código. Depois disso, um teste automatizado avisa na hora quando algo que funcionava deixou de funcionar. O p…
  3. [0.860] Geradores e a palavra-chave yield (06-geradores.md)
     Uma função comum calcula tudo e devolve o resultado de uma vez. Um gerador faz diferente: entrega um valor por vez, só quando alguém pede o próximo. Basta usar `yield` no lugar de `return`: Chamar `co…

Consulta: "que horas são em Tóquio agora?"
  1. [0.824] Datas, horas e fusos com datetime (15-datetime.md)
     O módulo `datetime` resolve quase tudo que envolve datas em Python. As classes principais são `date` (só a data), `datetime` (data e hora) e `timedelta` (uma duração). A distinção mais importante é en…
  2. [0.797] Requisições HTTP com requests (20-requisicoes-http.md)
     Consumir uma API web é rotina para quem programa em Python, e o pacote `requests` é o jeito mais conhecido de fazer isso. Ele não vem com o Python; instale com `python -m pip install requests`. O argu…
  3. [0.793] Programação assíncrona com asyncio (12-asyncio.md)
     Um programa que conversa com a rede passa boa parte do tempo esperando: a resposta de uma API, o retorno de um banco de dados. O `asyncio` aproveita essa espera. Enquanto uma tarefa aguarda, o event l…

Consulta: "por que meu programa com várias threads não fica mais rápido?"
  1. [0.876] Threads, processos e o GIL (13-threads-processos-gil.md)
     O CPython, o interpretador oficial, tem o GIL (Global Interpreter Lock): uma trava que deixa só uma thread executar bytecode Python por vez. Na prática, quatro threads somando números não deixam o cál…
  2. [0.863] Programação assíncrona com asyncio (12-asyncio.md)
     Um programa que conversa com a rede passa boa parte do tempo esperando: a resposta de uma API, o retorno de um banco de dados. O `asyncio` aproveita essa espera. Enquanto uma tarefa aguarda, o event l…
  3. [0.860] Lendo e escrevendo arquivos de texto (14-arquivos.md)
     Ler e gravar arquivos de texto é uma das tarefas mais comuns em Python, e a receita recomendada é sempre a mesma: `open` dentro de um bloco `with`, que fecha o arquivo no fim, e com o `encoding` explí…

Consulta: "como isolar as bibliotecas de cada projeto?"
  1. [0.843] Ambientes virtuais: dependências separadas para cada aplicação (09-ambientes-virtuais.md)
     Imagine duas aplicações na mesma máquina: uma depende do Django 4 e a outra do Django 5. Se os pacotes forem instalados direto no Python do sistema, as duas disputam a mesma pasta `site-packages`, e a…
  2. [0.825] Context managers e o bloco with (07-context-managers.md)
     Muitos recursos precisam ser liberados depois do uso: arquivos e conexões de banco têm que ser fechados, travas entre threads têm que ser soltas. Esquecer essa etapa, ou pulá-la porque uma exceção aco…
  3. [0.821] Threads, processos e o GIL (13-threads-processos-gil.md)
     O CPython, o interpretador oficial, tem o GIL (Global Interpreter Lock): uma trava que deixa só uma thread executar bytecode Python por vez. Na prática, quatro threads somando números não deixam o cál…
```

</details>

### Por que não há limiar de score

Os scores de cosseno do e5 ficam numa faixa estreita: na demo, de 0.793 a 0.888, e o 1º lugar fica só 0.013 a 0.049 acima do 2º. Uma consulta sem nada a ver com o corpus, "receita de bolo de chocolate", fez 0.826 no 1º lugar, mais que o acerto da consulta de Tóquio (0.824). Só a ordem tem significado: um corte fixo esconderia acertos ou deixaria passar ruído. O card do modelo avisa o mesmo (scores entre ~0,7 e 1,0).

### Saída do `pytest -m slow`

```text
tests/test_q3_corpus.py ..                                               [100%]

====================== 2 passed, 124 deselected in 52.12s ======================
```

Os dois testes: todo post cabe em 512 tokens, e cada consulta da demo traz o post esperado em 1º.

## Decisões técnicas e limitações

- **`gpt-6-luna`, não GPT-4:** o GPT-4 foi desligado (veja Q2 → Modelo). Esforço `medium`, escolhido por medição; timeout explícito, porque o `ChatOpenAI` não tem nenhum por padrão.
- **Sem `temperature`:** modelos de raciocínio recusam parâmetros de amostragem.
- **Memória do LangChain 1.x:** checkpointer + `thread_id`, o padrão atual da documentação (nada de `ConversationChain` ou `ConversationBufferMemory`, que são legado).
- **e5 + prefixos à mão:** o `multilingual-e5-small` entende português, é pequeno (384 dimensões, roda em CPU), tem licença MIT e baixa sem cadastro no Hugging Face. Os prefixos são obrigatórios para ele (veja Q3 → Como funciona).
- **`IndexFlatIP`:** com vetores de norma 1, produto interno = cosseno, e a busca exata é a certa para 20 posts. O corpus tem um tema só (Python): separar assuntos vizinhos mostra mais da busca semântica do que separar "cozinha" de "finanças".
- **Busca sem acento na Q1:** o `LIKE` do SQLite só ignora maiúsculas em ASCII e nunca ignora acento. A função `normalizar()` (NFKD → tira as marcas de acento → `casefold()`) é registrada no SQLite em cada conexão e aplicada à coluna e ao termo. O escape dos curingas vem depois da normalização, porque o NFKD transforma `％` e `＿` de largura total em `%` e `_`.
- **Validação num modelo de entrada** (`LivroCriar`) separado da tabela: no SQLModel, um modelo `table=True` não valida no construtor.
- **Carregamento lazy com trava:** a API sobe sem chave e sem baixar o modelo; duas primeiras requisições simultâneas criam o chatbot ou o buscador uma vez só. As rotas são síncronas (`def`), então o trabalho bloqueante roda no threadpool do FastAPI, sem travar o servidor.
- **Q2 e Q3 opcionais no app:** sem a pilha de IA, o app sobe só com a Q1. A guarda pega só `ModuleNotFoundError`, nunca `Exception`: um bug real tem que derrubar o app.
- **Versões fixas** (`==`) nas dependências diretas e nas indiretas críticas.

Limitações:

- **Q1:** a busca aplica `normalizar` em toda linha (varredura completa da tabela). Em escala: coluna normalizada com índice, ou FTS5.
- **Q2:** memória volátil e sem limite (em produção: checkpointer em SQLite ou Postgres, corte do histórico e trava por conversa). O escopo depende só do prompt de sistema: com `medium`, em 1 de 10 execuções o bot respondeu a pergunta fora do tema antes de redirecionar.
- **Q3:** busca exata; com milhões de vetores, um índice aproximado (IVF ou HNSW). Sem chunking: um post acima de 512 tokens seria cortado (o teste `slow` impede).
- **Sem lockfile com hashes:** a complexidade multiplataforma não compensa numa prova; os pins `==` cobrem o essencial.
- **Fora do escopo:** frontend, Docker, autenticação, paginação, deploy, RAG (o chatbot não usa a busca da Q3), migrations (as tabelas são criadas no startup), streaming, PUT/DELETE de livros, avaliação no LangSmith.

## Solução de problemas

- **`/chat` responde 503 com a chave no `.env`:** a API subiu sem `--env-file .env`, ou o uvicorn não foi reiniciado depois de editar o `.env`.
- **Código de saída 132 (SIGILL) ao carregar o modelo da Q3**, numa VM sem AVX (a máquina de dev é uma): rode com `OMP_NUM_THREADS=1`. Lá, `HF_HUB_OFFLINE=1` também foi usado, para ler o modelo do cache sem consultar o Hub.
