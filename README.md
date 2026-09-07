# Triagem IA vs Heurística

Sistema de triagem automatizada de e-mails corporativos que compara, em tempo real, duas abordagens de classificação: **IA Generativa (LLM via Groq)** e uma **baseline heurística** (palavras-chave). O objetivo do projeto é responder, com dados reais, uma pergunta prática: *o ganho de acurácia da IA generativa compensa seu custo e latência em relação a um método simples e gratuito?*

## Como funciona (visão geral)

1. O sistema roda sozinho em segundo plano (daemon), verificando a caixa de e-mail a cada 2 minutos.
2. Cada e-mail não lido é classificado por **dois métodos ao mesmo tempo**: o LLM (decide a categoria de verdade, que move o e-mail) e a heurística (roda em paralelo, só para comparação).
3. Categoria, tempo de resposta, tokens consumidos e se os dois métodos concordaram ficam registrados em um banco de dados local.
4. Um dashboard web mostra tudo isso em tempo real, com destaque visual para os casos em que IA e heurística discordaram — e um botão para desfazer qualquer movimentação.

## Resultados obtidos (amostra de teste, 80 e-mails)

| Método | Acurácia Geral | Casos Simples | Casos Complexos | Custo | Latência |
|---|---|---|---|---|---|
| LLM (Groq) | 91,25% | 97,50% | 85,00% | ~493 tokens/e-mail | ~2,3s |
| Heurística | 76,25% | 87,50% | 65,00% | 0 (grátis) | <1ms |

## Pré-requisitos

* Python 3.10+

### 1. Chave de API da Groq (gratuita)

1. Acesse [console.groq.com](https://console.groq.com/) e crie uma conta (pode entrar com Google).
2. No menu lateral, clique em **API Keys**.
3. Clique em **Create API Key**, dê um nome qualquer (ex: `triagem-teste`) e confirme.
4. Copie a chave gerada (começa com `gsk_...`) — ela só aparece uma vez, guarde antes de fechar a tela.

### 2. Senha de Aplicativo do Gmail

⚠️ **Não é a senha normal da sua conta Google.** É uma senha específica de 16 caracteres, criada só para este tipo de acesso.

1. Ative a **Verificação em Duas Etapas** na sua conta, se ainda não tiver: [myaccount.google.com/security](https://myaccount.google.com/security).
2. Acesse [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
3. Dê um nome ao app (ex: `classificador-teste`) e clique em **Criar**.
4. O Google vai mostrar uma senha de 16 letras, sem espaços — copie exatamente como aparece.

### 3. Pasta de teste no Gmail

1. No Gmail, vá em **Configurações → Ver todas as configurações → Marcadores**.
2. Crie um marcador (label) chamado exatamente `Classificador_Teste`.
3. É essa pasta que o sistema vai ler — nenhum outro e-mail da sua caixa principal é tocado.

## Instalação

```bash
git clone <URL_DO_REPOSITORIO>
cd triagem-ia-vs-heuristica

python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

## Configuração

Copie o arquivo de exemplo e preencha com suas próprias credenciais:

```bash
cp .env.example .env
```

Edite o `.env`:
```
GROQ_API_KEY=sua_chave_groq_aqui
EMAIL_USUARIO=seu_email@gmail.com
SENHA_EMAIL=sua_senha_de_aplicativo_de_16_caracteres
```
⚠️ `SENHA_EMAIL` **não é a senha da sua conta Google**. É a Senha de Aplicativo gerada no passo anterior — um código de 16 letras sem espaços, específico para este acesso. Colar sua senha real do Gmail aqui não vai funcionar e não é seguro.

> Cada pessoa que for rodar o projeto usa sua **própria** conta de e-mail e chave Groq — nada disso é compartilhado nem versionado no repositório.

### Usando outro provedor de e-mail (não Gmail)

O sistema usa IMAP/SMTP padrão, então funciona com qualquer provedor que suporte esses protocolos (Outlook/Office365, Yahoo, servidor corporativo próprio) — não é exclusivo do Gmail. Para trocar, adicione ao `.env`:
```
IMAP_HOST=outlook.office365.com
SMTP_HOST=smtp.office365.com
```
Se omitido, o sistema usa Gmail por padrão. **Atenção:** provedores com autenticação via OAuth2 obrigatório (em vez de login/senha simples) não são suportados nesta versão — isso vale para o próprio Gmail em configurações mais restritas de conta corporativa/Workspace, que também exigem uma "senha de aplicativo" gerada manualmente.

## Como rodar

**1. Suba o servidor:**
```bash
uvicorn api:app --reload
```
O daemon já começa a processar a caixa de entrada automaticamente (primeira varredura imediata, depois a cada 2 minutos).

**2. Abra o dashboard:**
```
http://127.0.0.1:8000
```

**3. (Opcional) Gerar massa de teste:**
Para popular sua caixa com e-mails fictícios de teste (domínio fintech, 80 e-mails balanceados entre casos simples e complexos):
```bash
python gerar_massa_v2.py     # gera mock_emails.json
python injetar_mocks.py      # envia os e-mails para o seu Gmail via SMTP
```

**4. (Opcional) Rodar a avaliação comparativa completa:**
Roda os 80 e-mails de teste direto contra os dois classificadores (sem precisar do Gmail) e gera o CSV de resultados + matrizes de confusão:
```bash
python avaliar.py
python matriz_confusao.py
```

## Estrutura do projeto

| Arquivo | Função |
|---|---|
| `core.py` | Motor de classificação (LLM + heurística) — usado tanto pelo daemon quanto pelos scripts de avaliação |
| `api.py` | Backend FastAPI: daemon de automação (APScheduler), rotas do dashboard, IMAP |
| `index.html` | Dashboard de auditoria (Tailwind + Fetch API) |
| `gerar_massa_v2.py` | Gera massa de e-mails de teste com diversidade lexical real |
| `injetar_mocks.py` | Envia os e-mails de teste para o Gmail via SMTP |
| `avaliar.py` | Roda a comparação LLM vs Heurística nos e-mails de teste |
| `matriz_confusao.py` | Gera matrizes de confusão (CSV + PNG) |

## Limitações conhecidas

* Lock de concorrência em memória — adequado para execução single-worker, não escala para múltiplos workers (ex: Gunicorn) sem ajuste.
* Endpoints da API sem autenticação — aceitável para ambiente local de demonstração, não recomendado para produção sem essa camada.
* Tier gratuito da Groq tem limite de requisições por minuto — por isso há um `sleep` entre chamadas nos scripts de lote.
