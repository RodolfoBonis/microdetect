# Modelo de Atualizações e Releases

Este documento descreve o sistema de atualização e o ciclo de vida de versões do MicroDetect, explicando como o projeto é versionado, atualizado e distribuído.

## Sumário
- [Estratégia de Versionamento](#estratégia-de-versionamento)
- [Canais de Distribuição](#canais-de-distribuição)
- [Tipos de Release](#tipos-de-release)
- [Ciclo de Vida de Desenvolvimento](#ciclo-de-vida-de-desenvolvimento)
- [Sistema de Atualização Automática](#sistema-de-atualização-automática)
- [Ciclo de Release e Frequência](#ciclo-de-release-e-frequência)
- [Implementação Técnica](#implementação-técnica)
- [Política de Suporte a Versões](#política-de-suporte-a-versões)
- [Changelog e Documentação](#changelog-e-documentação)
- [Rollback e Recuperação](#rollback-e-recuperação)

## Estratégia de Versionamento

O MicroDetect segue os princípios do [Versionamento Semântico](https://semver.org/) (SemVer), usando um esquema de versão com três números no formato `MAJOR.MINOR.PATCH`:

- **MAJOR**: Incrementado para mudanças incompatíveis com versões anteriores
- **MINOR**: Incrementado para adições de funcionalidades compatíveis com versões anteriores
- **PATCH**: Incrementado para correções de bugs compatíveis com versões anteriores

### Exemplos:

- `1.0.0`: Versão inicial estável
- `1.1.0`: Adição de novas funcionalidades
- `1.1.1`: Correção de bugs na versão 1.1.0
- `2.0.0`: Mudanças que quebram compatibilidade com versões 1.x.x

## Canais de Distribuição

O MicroDetect é distribuído através de dois canais principais:

1. **AWS CodeArtifact**: Repositório privado para distribuição controlada
2. **GitHub Releases**: Pacotes e código-fonte para cada versão

### AWS CodeArtifact

O CodeArtifact é usado como repositório Python privado, permitindo:

- Controle de acesso para distribuição interna ou para clientes específicos
- Distribuição rápida de atualizações
- Versionamento rigoroso
- Verificação automática de atualizações

### GitHub Releases

Para cada versão estável, criamos:

- Uma tag Git com o número da versão
- Uma GitHub Release com notas de release detalhadas
- Assets contendo o código-fonte e distribuições empacotadas

## Tipos de Release

### Releases Major (X.0.0)

- Mudanças significativas com possíveis quebras de compatibilidade
- Novas arquiteturas ou refatorações importantes
- Alterações na API que não são retrocompatíveis
- Ciclo de desenvolvimento e testes mais longo
- Anúncio prévio e período de transição

### Releases Minor (0.X.0)

- Novas funcionalidades compatíveis com versões anteriores
- Melhorias de desempenho
- Adição de novos comandos ou opções
- Expansão de recursos existentes

### Releases Patch (0.0.X)

- Correções de bugs
- Pequenas melhorias
- Atualizações de documentação
- Otimizações menores

### Pré-releases

Para versões em desenvolvimento usamos sufixos:

- `1.2.0-alpha.1`: Muito instável, para testes iniciais
- `1.2.0-beta.1`: Razoavelmente estável, para testes mais amplos
- `1.2.0-rc.1`: Candidata a release, para testes finais

## Ciclo de Vida de Desenvolvimento

### 1. Planejamento

- Definição de escopo e requisitos
- Criação de issues e milestones no GitHub
- Priorização de funcionalidades e correções

### 2. Desenvolvimento

- Implementação em branches específicas
- Testes unitários e de integração
- Revisão de código através de Pull Requests

### 3. Testes

- Testes alfa internos
- Testes beta com usuários selecionados
- Validação de desempenho e usabilidade

### 4. Release

- Construção dos pacotes de distribuição
- Atualização de documentação e changelogs
- Publicação no AWS CodeArtifact e GitHub

### 5. Manutenção

- Monitoramento e coleta de feedback
- Correção de bugs reportados
- Planejamento de melhorias futuras

## Sistema de Atualização Automática

O MicroDetect inclui um sistema de atualização automática que:

1. Verifica periodicamente a disponibilidade de novas versões
2. Notifica os usuários sobre atualizações disponíveis
3. Permite atualização com um único comando

### Fluxo de Atualização

1. **Verificação**: O sistema verifica o AWS CodeArtifact em busca de versões mais recentes
2. **Notificação**: Se uma nova versão for encontrada, o usuário é notificado
3. **Confirmação**: O usuário decide se deseja atualizar
4. **Download e Instalação**: A nova versão é baixada e instalada
5. **Verificação**: O sistema confirma que a atualização foi bem-sucedida

### Configuração de Verificação

Os usuários podem configurar o comportamento de verificação:

- Desativar verificações automáticas
- Alterar a frequência de verificação
- Optar por atualizações automáticas sem confirmação

## Ciclo de Release e Frequência

### Planejamento de Versões

- **Major releases**: Uma ou duas vezes por ano
- **Minor releases**: A cada 1-2 meses
- **Patch releases**: Conforme necessário (geralmente semanais)

### Notificação de Releases

As releases são anunciadas através de:

- Notificações no aplicativo
- Mensagens do Telegram para inscritos
- GitHub Releases

## Implementação Técnica

### Release Automation

O processo de release é automatizado usando GitHub Actions:

1. Um PR é mesclado na branch principal
2. O CI valida a mudança
3. O workflow de auto-release é acionado
4. Baseado nas mensagens de commit, a versão é incrementada
5. Uma nova tag e release são criadas no GitHub
6. O pacote é construído e enviado para o AWS CodeArtifact

```yaml
# Trecho do workflow auto-release.yml
determine_version:
  steps:
    - name: Analyze PR for version type
      id: analyze_pr
      run: |
        # Determinar tipo de versão baseado em labels ou mensagens de commit
        if echo "$pr_data" | grep -i -q '"title":.*\(feat\|feature\|enhancement\)'; then
          echo "Detected feature from PR title, using minor version"
          echo "version_type=minor" >> $GITHUB_OUTPUT
        elif echo "$pr_data" | grep -i -q '"title":.*\(fix\|bugfix\|patch\)'; then
          echo "Detected bugfix from PR title, using patch version"
          echo "version_type=patch" >> $GITHUB_OUTPUT
        else
          echo "No specific version indicator found, using patch as default"
          echo "version_type=patch" >> $GITHUB_OUTPUT
        fi
```

### Sistema de Atualização

O sistema de atualização utiliza:

1. AWS CodeArtifact para armazenamento de pacotes
2. Tokens de autenticação temporários para acesso seguro
3. pip para instalação de pacotes
4. Comparação semântica de versões

```python
# Trecho de updater.py
def compare_versions(current: str, latest: str) -> bool:
    # Dividir versões em partes (major, minor, patch)
    current_parts = [int(part) for part in current.split('.')]
    latest_parts = [int(part) for part in latest.split('.')]
    
    # Comparar cada parte da versão
    for i in range(len(current_parts)):
        if latest_parts[i] > current_parts[i]:
            return True
        elif latest_parts[i] < current_parts[i]:
            return False
    
    return False
```

## Política de Suporte a Versões

### Suporte a Longo Prazo (LTS)

- Versões LTS são designadas pelo sufixo `-lts` (ex: `1.0.0-lts`)
- As versões LTS recebem correções de segurança por 12 meses
- Correções de bugs críticos por 8 meses
- Documentação mantida atualizada

### Versões Regulares

- Versões não-LTS recebem correções de segurança por 3 meses
- Correções de bugs críticos por 2 meses
- Usuários são encorajados a atualizar para a versão mais recente

### Fim de Suporte

Quando uma versão atinge o fim de suporte:

- Notificações são enviadas aos usuários
- A documentação é arquivada
- Não são mais emitidas correções
- Recursos de verificação de atualização continuam funcionando

## Changelog e Documentação

### Changelog

Cada release inclui um changelog detalhado, gerado automaticamente a partir das mensagens de commit e refinado manualmente, incluindo:

- Novas funcionalidades
- Correções de bugs
- Melhorias de desempenho
- Alterações na API
- Notas de migração (quando aplicável)

### Documentação de Versão

A documentação é atualizada com cada release, incluindo:

- Guias de usuário
- Exemplos
- Referência de API
- Alterações de comportamento
- Notas de migração

## Rollback e Recuperação

Para situações onde uma atualização causa problemas, temos estratégias de rollback:

### Rollback Manual

Os usuários podem reverter para uma versão anterior:

```bash
# Instalar uma versão específica
microdetect update --version 1.1.0
```

### Ambientes Isolados

Para testes de novas versões sem afetar o ambiente de produção:

```bash
# Criar um ambiente de teste
python -m venv test_env
source test_env/bin/activate
pip install microdetect==2.0.0
```

## Utilizando o Sistema de Atualização

### Verificando Atualizações

Para verificar manualmente se há atualizações disponíveis:

```bash
microdetect update --check-only
```

Este comando mostrará informações sobre a versão atual e indicará se há uma versão mais recente disponível.

### Atualizando o MicroDetect

Para atualizar o MicroDetect para a versão mais recente:

```bash
microdetect update
```

O processo de atualização irá:
1. Verificar se há uma nova versão
2. Pedir confirmação antes de atualizar
3. Baixar e instalar a nova versão
4. Exibir o progresso da atualização

### Forçando uma Atualização

Para atualizar sem confirmação:

```bash
microdetect update --force
```

### Configuração do AWS CodeArtifact

Antes de usar o sistema de atualização, você precisa configurar o AWS CodeArtifact:

```bash
microdetect setup-aws --domain seu-dominio --repository seu-repositorio --configure-aws
```

Você precisará fornecer:
- Credenciais de acesso AWS
- Nome do domínio CodeArtifact
- Nome do repositório
- Região (opcional)

### Desativando Verificações Automáticas de Atualização

Se você não deseja verificações automáticas de atualização, defina a variável de ambiente:

```bash
# Linux/macOS
export MICRODETECT_SKIP_UPDATE_CHECK=1

# Windows
set MICRODETECT_SKIP_UPDATE_CHECK=1
```

## Conclusão

O modelo de atualizações e releases do MicroDetect é projetado para:

1. Entregar novas funcionalidades e correções regularmente
2. Manter a estabilidade para usuários existentes
3. Fornecer um caminho claro de migração entre versões
4. Facilitar o processo de atualização
5. Comunicar claramente as mudanças em cada versão

Esse modelo equilibra a necessidade de evolução rápida do software com a estabilidade exigida por usuários em ambientes de produção.