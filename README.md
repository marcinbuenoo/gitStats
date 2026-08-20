# Git Stats

Uma API própria para exibir estatísticas de um perfil GitHub como SVG, ideal para incorporar no `README.md` sem depender de serviços de terceiros.

## Executar localmente

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn api.main:app --reload
```

Abra `http://127.0.0.1:8000/octocat` para ver um card de exemplo. Também há o endpoint `http://127.0.0.1:8000/health`.

Para reduzir bastante a chance de limite de requisições, crie um token pessoal do GitHub sem permissões e defina-o antes de iniciar a API:

```powershell
$env:GITHUB_TOKEN = "seu_token"
```

Nunca versiona esse token; use as variáveis de ambiente da plataforma de hospedagem.

## Cards estáticos no GitHub Actions

O workflow `.github/workflows/update-cards.yml` gera os cards a cada seis horas e os salva em `assets/`. Ele usa o `GITHUB_TOKEN` temporário do próprio Actions, sem publicar uma API ou expor um token pessoal.

Por padrão, o workflow usa o dono do repositório como usuário. Para gerar cards de outro perfil, crie a variável de repositório `GITHUB_USERNAME` em **Settings > Secrets and variables > Actions > Variables**. Execute o workflow uma vez em **Actions > Update GitHub cards > Run workflow**.

## Uso no README

Depois que o workflow gerar os arquivos, adicione ao README do seu perfil:

```md
![GitHub Stats](https://raw.githubusercontent.com/SEU-USUARIO/gitStats/master/assets/github-stats.svg)
![Linguagens mais usadas](https://raw.githubusercontent.com/SEU-USUARIO/gitStats/master/assets/github-languages.svg)
```

Temas disponíveis: `dark` (padrão) e `light`.

O card geral mostra repositórios públicos, total de estrelas recebidas, seguidores e contas seguidas. O segundo card mostra as cinco linguagens mais usadas e suas proporções, calculadas pelos bytes de código informados pela API do GitHub. Os arquivos são atualizados pelo workflow a cada seis horas.

## Testes

```powershell
pytest
```
