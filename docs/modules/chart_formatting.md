# Formatação de Valores Grandes em Gráficos

## Visão Geral

Este documento descreve a implementação da formatação automática de valores grandes (milhares e milhões) nos gráficos gerados pelo sistema NLP2DB-MRAG.

## Problema

Quando os gráficos são gerados com valores numéricos muito grandes (como milhões), a escala do eixo Y pode ficar difícil de ler, mostrando valores como `50000000` em vez de formatos mais legíveis como `50M`.

## Solução

A solução implementada detecta automaticamente a magnitude dos valores no eixo Y e aplica a formatação apropriada:

1. Para valores em milhões (≥ 1.000.000), usa o formato `.1s` que converte para notação científica simplificada (ex: 50M)
2. Para valores em milhares (≥ 1.000), usa o formato `.3s` que converte para notação com K (ex: 50K)
3. Para valores menores, mantém a formatação padrão

## Implementação

A implementação está no arquivo `pilot/common/chart_generator.py` no método `generate_chart()`:

```python
# Verificar se os valores são muito grandes e precisam de formatação especial
max_value = df[y_col].max() if pd.api.types.is_numeric_dtype(df[y_col]) else 0

# Determinar o formato adequado com base na magnitude dos valores
tick_format = None
tick_suffix = ""

if max_value >= 1000000:  # Milhões
    tick_format = ".1s"
elif max_value >= 1000:  # Milhares
    tick_format = ".3s"

# Configurações comuns para todos os gráficos
common_layout = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(
        title=x_title,
        tickangle=x_rotation
    ),
    yaxis=dict(
        title=y_title,
        type=y_scale,
        # Formatação para valores grandes
        tickformat=tick_format,
        ticksuffix=tick_suffix
    ),
    colorway=px.colors.qualitative.Plotly if color_scheme == "plotly" else None
)
```

## Como Funciona

1. O sistema calcula o valor máximo no conjunto de dados para o eixo Y
2. Com base nesse valor, determina o formato de exibição adequado:
   - Para valores ≥ 1.000.000: formato `.1s` (ex: 1.2M, 50M)
   - Para valores ≥ 1.000: formato `.3s` (ex: 1.20K, 50.0K)
   - Para valores menores: formato padrão
3. Aplica essa configuração ao layout do gráfico usando a propriedade `tickformat` do Plotly

## Testes

Foi criado um script de teste específico (`tests/test_large_values_chart.py`) para validar a formatação de valores grandes:

1. Cria um DataFrame com valores grandes (milhões)
2. Gera um gráfico de barras com esses valores
3. Verifica se a formatação está sendo aplicada corretamente
4. Gera um HTML para visualização do resultado

## Resultados

A implementação garante que:

1. Valores em milhões sejam exibidos com o sufixo "M" (ex: 50M)
2. Valores em milhares sejam exibidos com o sufixo "K" (ex: 50K)
3. A escala do gráfico permaneça legível mesmo com valores muito grandes

Isso melhora significativamente a legibilidade dos gráficos quando os dados contêm valores de grande magnitude.
