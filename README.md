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

## Uso no README

Depois de publicar a API, adicione ao README do seu perfil:

```md
![GitHub Stats](https://SEU-DOMINIO/SEU-USUARIO?theme=dark)
![Linguagens mais usadas](https://SEU-DOMINIO/SEU-USUARIO/languages?theme=dark)
```

Temas disponíveis: `dark` (padrão) e `light`.

O card geral mostra repositórios públicos, total de estrelas recebidas, seguidores e contas seguidas. O endpoint `/SEU-USUARIO/languages` gera um segundo card com as cinco linguagens mais usadas e suas proporções, calculadas pelos bytes de código informados pela API do GitHub. O resultado fica em cache por 15 minutos para reduzir chamadas à API do GitHub.

## Testes

```powershell
pytest
```
