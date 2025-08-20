# Modo de Teste para Geração de Gráficos com LLM

Este documento descreve a implementação do modo de teste para a geração de gráficos com LLM no projeto NLP2DB-MRAG.

## Visão Geral

O sistema de geração de gráficos utiliza um modelo de linguagem grande (LLM) para recomendar o tipo de gráfico mais adequado e configurar os eixos com base nos dados da consulta SQL. Para facilitar os testes e desenvolvimento sem depender de um serviço LLM real, implementamos um modo de teste que simula as respostas do LLM de forma determinística.

## Componentes Modificados

### 1. ChartGenerator (pilot/common/chart_generator.py)

- Adicionado parâmetro `test_mode` aos métodos:
  - `ask_llm_for_chart_type`
  - `ask_llm_for_axis_config`
  - `generate_chart`

- Quando `test_mode=True`, os métodos retornam respostas simuladas em vez de consultar o LLM real:
  - O tipo de gráfico recomendado é determinado com base na presença de colunas numéricas e categóricas
  - A configuração de eixos é simplificada com títulos básicos e configurações de rotação

### 2. DbChatOutputParser (pilot/scene/chat_db/auto_execute/out_parser.py)

- Modificado o método `parse_view_response_async` para aceitar o parâmetro `test_mode`
- Atualizado o método wrapper síncrono `parse_view_response` para passar o parâmetro `test_mode` para a versão assíncrona
- Importação lazy do `ChartGenerator` dentro do método assíncrono para evitar importações circulares

### 3. Testes (tests/test_chart_generator_llm.py)

- Atualizado o script de teste para chamar `generate_chart` com `test_mode=True`
- Adicionada chamada ao parser com `test_mode=True` para testar a integração completa

## Como Usar o Modo de Teste

Para usar o modo de teste em seus próprios testes ou desenvolvimento:

```python
# Importar o ChartGenerator
from pilot.common.chart_generator import ChartGenerator

# Criar uma instância do ChartGenerator
chart_generator = ChartGenerator()

# Gerar um gráfico em modo de teste
chart_result = await chart_generator.generate_chart(
    df=seu_dataframe,
    sql_query="SELECT * FROM sua_tabela",
    test_mode=True  # Ativar o modo de teste
)

# Ou ao usar o parser de saída
from pilot.scene.chat_db.auto_execute.out_parser import DbChatOutputParser

parser = DbChatOutputParser(sep="\n", is_stream_out=False)
result = await parser.parse_view_response_async(sql_action, data, test_mode=True)
# Versão síncrona
result = parser.parse_view_response(sql_action, data, test_mode=True)
```

## Comportamento do Modo de Teste

### Tipos de Gráficos Simulados

- **Bar (Barras)**: Recomendado quando há colunas categóricas e numéricas
- **Line (Linha)**: Recomendado quando há colunas de data/tempo e numéricas
- **Scatter (Dispersão)**: Recomendado quando há duas colunas numéricas

### Configuração de Eixos Simulada

- Títulos baseados nos nomes das colunas
- Rotação de rótulos do eixo X baseada no comprimento dos valores
- Formatação básica para melhor legibilidade

## Benefícios do Modo de Teste

1. **Testes Determinísticos**: Resultados consistentes e previsíveis para testes automatizados
2. **Desenvolvimento Offline**: Permite desenvolver e testar sem conexão com serviços LLM
3. **Testes Rápidos**: Evita latência e custos associados a chamadas reais ao LLM
4. **Isolamento**: Isola falhas em componentes específicos sem interferência de serviços externos

## Limitações

- As respostas simuladas são simplificadas e não capturam toda a sofisticação do LLM real
- Alguns casos de uso avançados podem não ser cobertos pelo modo de teste atual
- A personalização das respostas simuladas é limitada

## Tratamento de Loops de Eventos Assíncronos

Uma consideração importante ao usar funções assíncronas em aplicações web é o gerenciamento correto de loops de eventos. Implementamos uma solução robusta para evitar o erro `asyncio.run() cannot be called from a running event loop` que ocorre quando tentamos usar `asyncio.run()` dentro de um loop de eventos já em execução.

### Solução Implementada

O método `parse_view_response` foi modificado para detectar e lidar com diferentes cenários de loops de eventos:

```python
def parse_view_response(self, speak, data, test_mode: bool = False) -> str:
    try:
        # Tenta obter o loop de eventos atual
        loop = asyncio.get_event_loop()
        # Verifica se o loop está rodando
        if loop.is_running():
            # Se já estiver em um loop, usamos nest_asyncio para permitir loops aninhados
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(self.parse_view_response_async(speak, data, test_mode=test_mode))
        else:
            # Se não estiver em um loop, podemos usar run_until_complete
            return loop.run_until_complete(self.parse_view_response_async(speak, data, test_mode=test_mode))
    except RuntimeError:
        # Fallback para asyncio.run se não conseguir obter o loop atual
        return asyncio.run(self.parse_view_response_async(speak, data, test_mode=test_mode))
```

### Dependência Adicional

Esta solução requer o pacote `nest_asyncio`, que permite a execução de loops de eventos aninhados:

```bash
uv pip install nest_asyncio
```

### Testes em Ambiente Web

Criamos um script de teste (`tests/test_asyncio_web_env.py`) que simula um ambiente web com um loop de eventos em execução para verificar se a solução funciona corretamente. O teste confirma que o parser pode ser chamado em modo síncrono mesmo quando já existe um loop de eventos em execução.

## Próximos Passos

- Expandir o modo de teste para cobrir mais tipos de gráficos e configurações
- Adicionar opções para personalizar as respostas simuladas
- Implementar testes de integração mais abrangentes usando o modo de teste
- Monitorar o desempenho da solução de asyncio em ambiente de produção
