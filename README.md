# IFCM Cuida

Sistema web para registrar e acompanhar problemas de infraestrutura e manutenção escolar. Alunos, professores e funcionários podem abrir solicitações com descrição, local, categoria e foto; gestores atualizam prioridade, status e histórico.

## Funcionalidades

- Cadastro, login e logout. Senhas são armazenadas com hash seguro.
- Registro de problemas com categoria, local e foto opcional.
- Listagem e filtros por categoria, status e local.
- Página de detalhes com histórico de atualizações.
- Painel restrito a gestores para acompanhar solicitações e administrar categorias.
- Banco relacional SQLite com usuários, categorias, solicitações e histórico.
- Interface responsiva com Bootstrap.

## Requisitos

- Python 3.10 ou superior
- pip

## Instalação e execução local (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
flask --app run.py init-db
flask --app run.py seed-demo
flask --app run.py run --debug
```

Abra `http://127.0.0.1:5000`.

O SQLite é criado em `instance/ifcm.db`; fotos ficam em `app/static/uploads/`. Para outro banco compatível com SQLAlchemy, configure `DATABASE_URL`. Configure também `SECRET_KEY` com um valor aleatório antes de disponibilizar o sistema na internet.

### Contas locais de demonstração

Execute `seed-demo` somente em ambiente local:

| Perfil | E-mail | Senha |
|---|---|---|
| Gestor | admin@ifcm.edu.br | Admin123! |
| Aluno | aluno@ifcm.edu.br | Aluno123! |

O comando também cria categorias iniciais. Não execute esse seed em produção: as credenciais são públicas e servem apenas para demonstração local. Em implantação, crie um gestor com credencial própria e remova ou altere qualquer conta de demonstração.

## Testes de sistema

Os testes exercitam formulários, autenticação, autorização, filtros, persistência, histórico, categorias e envio de imagens usando um banco temporário:

```powershell
pytest -q
```

## Modelo de dados

- **Usuário** (`User`): nome, e-mail, hash de senha e perfil.
- **Categoria** (`Category`): nome, descrição e estado ativo/inativo.
- **Solicitação** (`Report`): título, descrição, local, status, prioridade, data, imagem, autor e categoria.
- **Histórico** (`ReportHistory`): solicitação, responsável pela atualização, status, observação e data.

Um usuário pode registrar várias solicitações; cada solicitação pertence a uma categoria e possui entradas de histórico. Categorias usadas podem ser desativadas sem perder as solicitações associadas.

## Backlog e processo de desenvolvimento

Use um GitHub Project para acompanhar este backlog. Antes de iniciar cada sprint, selecione as tarefas, atribua responsáveis do grupo e defina o período de 15 dias. Ao mover uma tarefa para **Em Teste**, indique outro integrante como responsável pela verificação e registre a evidência; só mova para **Concluído** após atender aos critérios de aceite.

| Prioridade | Tarefa | Descrição | Critérios de aceite |
|---|---|---|---|
| Alta | Configurar aplicação e banco | Criar a aplicação Flask, persistência relacional e configuração local. | O projeto inicia conforme o README; as tabelas são criadas e os registros persistem após reiniciar. |
| Alta | Implementar contas e acesso | Criar cadastro, login, logout e perfis de usuário e gestor. | Cadastro válido funciona; senhas não ficam em texto puro; páginas de gestão respondem 403 para usuários comuns. |
| Alta | Registrar solicitações | Criar formulários de problema com categoria, local e foto opcional. | Usuário autenticado envia dados válidos; a solicitação aparece nos detalhes e continua salva após reiniciar. Campos inválidos mostram mensagens e não criam registros. |
| Alta | Acompanhar solicitações | Exibir listagem, detalhes, filtros e histórico. | Filtros de categoria, status e local combinam corretamente; detalhes inexistentes retornam 404; mudanças ficam no histórico. |
| Média | Administrar categorias | Permitir que gestores cadastrem, editem e desativem categorias. | Gestor consegue manter categorias; usuários comuns recebem 403; categorias inativas não podem ser usadas em novas solicitações. |
| Alta | Testar fluxos do sistema | Implementar testes de sistema para autenticação, solicitações e gestão. | `pytest -q` executa pelo menos 16 testes sem falhas; os testes cobrem validações, permissões e persistência. |
| Média | Preparar implantação | Configurar execução de produção e armazenamento persistente. | Aplicação inicia com Gunicorn; banco e imagens usam armazenamento persistente; `SECRET_KEY` vem do ambiente. |
| Média | Finalizar apresentação e registros | Atualizar documentação, quadro, evidências e contribuição individual. | README permite configurar e testar; quadro e sprint refletem o trabalho real; cada integrante registra sua contribuição. |

### Kanban do grupo

O GitHub Project deve conter exatamente estas colunas:

1. **A Fazer** — tarefas priorizadas que ainda não começaram.
2. **Em Andamento** — tarefas em desenvolvimento.
3. **Em Teste** — tarefas implementadas; registrar o integrante diferente do autor que realizou o teste.
4. **Concluído** — tarefas que atendem aos critérios de aceite.

Em cada cartão, registrem sprint, responsável, descrição, critérios de aceite, estado e evidência. O quadro do grupo, seus responsáveis e as evidências de sprint devem ser preenchidos e mantidos no GitHub; não são presumidos por este código.

## Implantação

O arquivo `render.yaml` descreve uma implantação no Render com Gunicorn e disco persistente para o SQLite e as imagens. Revise plano, cobrança e configuração atual da plataforma antes de criar o serviço. Em produção:

1. Configure uma `SECRET_KEY` própria e credenciais de gestor não compartilhadas.
2. Confirme que `/var/data` está em disco persistente e que o serviço pode gravar nele.
3. Configure `DATABASE_URL` e `UPLOAD_FOLDER` para caminhos nesse volume.
4. Execute o seed apenas localmente; crie as categorias e contas de produção com credenciais próprias.

SQLite e o armazenamento local do serviço não são adequados para várias instâncias simultâneas sem um volume compartilhado; para essa escala, use um banco gerenciado e armazenamento de arquivos apropriado.

## Limitações e próximos passos

- A implementação é um MVP acadêmico; não substitui canais oficiais de emergência.
- Os relatos ficam visíveis aos usuários autenticados da comunidade escolar.
- Para uso real, definir política de retenção, privacidade, backup, recuperação de senha e revisão institucional dos perfis de gestor.
- O quadro Kanban, a divisão nominal de tarefas, os registros individuais e a implantação precisam ser concluídos pelo grupo.
