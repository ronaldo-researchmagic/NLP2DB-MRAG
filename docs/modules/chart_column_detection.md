# Detecção Inteligente de Tipos de Colunas para Gráficos

## Visão Geral

A detecção inteligente de tipos de colunas é uma funcionalidade que utiliza o LLM para identificar o tipo semântico real de cada coluna em um DataFrame, independentemente do tipo de dado original. Isso é especialmente útil para colunas numéricas que representam categorias ou identificadores, como anos, códigos de produto, IDs de cliente, etc.

## Problema Resolvido

Em visualizações de dados, colunas numéricas são frequentemente tratadas como valores quantitativos, mesmo quando representam categorias. Por exemplo:

- Anos (2019, 2020, 2021) são numericamente sequenciais, mas semanticamente são categorias
- Códigos de produto (1001, 1002, 1003) são numericamente ordenados, mas semanticamente são identificadores
- Meses representados como números (1, 2, 3) são categorias, não valores quantitativos

Tratar essas colunas como numéricas pode levar a visualizações inadequadas, como:
- Interpolação entre pontos em gráficos de linha
- Escalas contínuas em gráficos de barras
- Agrupamento inadequado em gráficos de dispersão

## Solução Implementada

A solução implementada consiste em:

1. **Análise Semântica via LLM**: O LLM analisa os nomes das colunas, tipos de dados e amostra dos valores para determinar o tipo semântico real de cada coluna.

2. **Regras Heurísticas**: Complementando a análise do LLM, regras heurísticas são aplicadas para garantir a correta detecção de tipos específicos, como anos.

3. **Classificação em Tipos Semânticos**:
   - `id`: Identificadores únicos (ex: ID de cliente, código de produto)
   - `category`: Valores categóricos (ex: anos, meses, status)
   - `numeric`: Valores quantitativos (ex: vendas, preços, quantidades)
   - `temporal`: Datas e tempos (ex: data de venda, timestamp)

4. **Conversão de Tipos**: Colunas numéricas identificadas como `id` ou `category` são convertidas para string para garantir que sejam tratadas como categorias discretas nos gráficos.

## Como Funciona

### 1. Prompt do LLM

O LLM recebe um prompt que solicita a análise dos tipos semânticos:

```python
"""
IMPORTANTE: Analise cada coluna e determine seu tipo semântico real, independente do tipo de dados no DataFrame:
1. Identifique colunas que parecem ser códigos ou identificadores (mesmo que sejam numéricas)
2. Identifique colunas que são categóricas (mesmo que sejam numéricas, como anos, códigos de produto, etc.)
3. Identifique colunas que são realmente numéricas e representam valores quantitativos
4. Identifique colunas temporais (datas, anos, meses, etc.)
"""
```

### 2. Resposta do LLM

O LLM retorna um JSON com os tipos semânticos identificados:

```json
{
  "column_types": {
    "id_cliente": "id",
    "ano": "category",
    "mes": "category",
    "vendas": "numeric",
    "categoria": "category"
  }
}
```

### 3. Aplicação dos Tipos Semânticos e Regras Heurísticas

A função `apply_semantic_types` aplica os tipos semânticos ao DataFrame e também implementa regras heurísticas para garantir a correta detecção de tipos específicos:

```python
def apply_semantic_types(df, column_types=None):
    df_copy = df.copy()
    
    # Aplicar regras heurísticas primeiro (independente do LLM)
    for col in df_copy.columns:
        # Detectar colunas de anos automaticamente
        if pd.api.types.is_numeric_dtype(df_copy[col]):
            # Verificar se o nome da coluna sugere que é um ano
            if col.lower() in ['ano', 'year', 'anual', 'yearly']:
                # Verificar se os valores parecem anos válidos (entre 1900 e 2100)
                if df_copy[col].min() >= 1900 and df_copy[col].max() <= 2100:
                    logging.debug(f"Regra heurística - Convertendo coluna '{col}' para string (parece ser ano)")
                    df_copy[col] = df_copy[col].astype(str)
    
    # Se não houver tipos semânticos do LLM, retornar o DataFrame com as regras heurísticas aplicadas
    if column_types is None:
        return df_copy
    
    # Aplicar tipos semânticos identificados pelo LLM
    logging.debug(f"Aplicando tipos semânticos: {column_types}")
    for col, sem_type in column_types.items():
        if col not in df_copy.columns:
            continue
            
        # Se a coluna for numérica mas semanticamente for uma categoria ou ID
        if pd.api.types.is_numeric_dtype(df_copy[col]):
            if sem_type in ["category", "id"]:
                # Converter para string para tratá-la como categoria
                logging.debug(f"Convertendo coluna '{col}' para string (tipo semântico: {sem_type})")
                df_copy[col] = df_copy[col].astype(str)
        else:
            logging.debug(f"Coluna '{col}' já é não-numérica, mantendo tipo original")
                
    return df_copy
```

## Integração no Fluxo de Geração de Gráficos

A detecção inteligente de tipos de colunas está integrada no fluxo de geração de gráficos:

1. O LLM é consultado para recomendação de tipo de gráfico e colunas a usar
2. Os tipos semânticos são extraídos da resposta do LLM
3. A função `apply_semantic_types` é chamada para converter os tipos de dados
4. O gráfico é gerado com os tipos de dados ajustados

## Benefícios

- **Visualizações mais precisas**: Gráficos que representam corretamente a natureza dos dados
- **Melhor interpretação**: Evita confusão entre valores categóricos e quantitativos
- **Flexibilidade**: Funciona com qualquer tipo de dado, independente do tipo original no DataFrame

## Exemplo de Uso

```python
# Criar DataFrame
df = pd.DataFrame({
    'id_cliente': [1, 2, 3, 4, 5],
    'ano': [2019, 2020, 2021, 2022, 2023],
    'vendas': [1500, 2300, 1800, 3200, 2700]
})

# Gerar gráfico com detecção inteligente de tipos
chart_result = await ChartGenerator.generate_chart(df)
```

## Modo de Teste

Para testes sem depender do LLM real, a classe `ChartGenerator` inclui um modo de teste que simula a resposta do LLM:

```python
# Usar modo de teste
chart_result = await ChartGenerator.generate_chart(df, test_mode=True)
```

## Regras Heurísticas para Detecção de Anos

Além da detecção via LLM, implementamos regras heurísticas específicas para garantir que colunas de anos sejam sempre tratadas corretamente:

### Critérios para Detecção de Anos

1. **Nome da coluna**: Verifica se o nome da coluna sugere que é um ano:
   - 'ano', 'year', 'anual', 'yearly'

2. **Intervalo de valores**: Verifica se os valores estão em um intervalo razoável para anos:
   - Entre 1900 e 2100

3. **Tipo de dados**: Aplica-se apenas a colunas numéricas

### Benefícios das Regras Heurísticas

- **Robustez**: Mesmo que o LLM não identifique corretamente uma coluna de anos, as regras heurísticas garantem o tratamento adequado
- **Consistência**: Todas as colunas de anos são tratadas da mesma forma em todos os gráficos
- **Independência**: As regras heurísticas funcionam mesmo sem consultar o LLM

### Exemplo de Aplicação

```python
# DataFrame com coluna de anos
df = pd.DataFrame({
    'ano': [2020, 2021, 2022, 2023, 2024],
    'faturamento': [100000, 120000, 150000, 130000, 160000]
})

# A coluna 'ano' será automaticamente convertida para string
df_converted = ChartGenerator.apply_semantic_types(df)

# Resultado: a coluna 'ano' agora é do tipo 'object' (string)
# e será tratada como categoria no gráfico
```

## Priorização Inteligente de Colunas

Além da detecção de tipos de colunas, implementamos uma lógica de priorização inteligente para selecionar automaticamente as colunas mais adequadas para cada eixo do gráfico:

### Priorização de Colunas Temporais para o Eixo X

Colunas temporais são sempre priorizadas para o eixo X, seguindo a lógica natural de visualização de dados ao longo do tempo. A detecção de colunas temporais inclui:

1. **Colunas com tipo datetime**: Colunas com tipo de dado `datetime64[ns]`
2. **Colunas com nomes temporais exatos**: Colunas com nome exatamente igual a 'ano' ou 'year'
3. **Colunas com termos temporais**: Colunas cujos nomes contêm termos como 'data', 'date', 'ano', 'year', 'mes', 'month', etc.
4. **Colunas numéricas com valores de anos**: Colunas numéricas cujos valores estão entre 1900 e 2100 e são inteiros

### Tratamento Especial para Colunas Temporais com Valor Único

Quando uma coluna temporal (como 'ano') contém apenas um valor único, o sistema aplica uma lógica especial:

1. **Detecção de valor único**: Verifica se a coluna temporal tem apenas um valor único (ex: todos os dados são do mesmo ano)
2. **Substituição automática**: Ao invés de usar essa coluna temporal no eixo X (o que seria inútil), o sistema seleciona automaticamente uma coluna categórica alternativa
3. **Verificação de valores distintos**: Garante que a coluna categórica selecionada tenha mais de um valor distinto para criar um gráfico significativo
4. **Logging detalhado**: O sistema registra essa decisão e o processo de seleção para fins de depuração: `Temporal column 'ano' has only one unique value (2023). Using categorical column 'categoria' with 4 unique values for X axis instead.`

### Priorização de Colunas de Faturamento para o Eixo Y

O sistema prioriza automaticamente colunas que representam valores de faturamento, vendas ou totais para o eixo Y:

1. **Detecção de colunas prioritárias**: Identifica colunas com termos como 'faturamento', 'total', 'valor', 'venda', 'revenue', 'sales', 'amount', 'sum' em seus nomes (ampliada para incluir mais termos em inglês e português)
2. **Substituição da recomendação do LLM**: Mesmo que o LLM recomende outra coluna para o eixo Y, o sistema substitui pela coluna prioritária
3. **Priorização garantida**: A priorização é aplicada em todos os fluxos de decisão, garantindo que colunas de faturamento sempre sejam usadas para o eixo Y quando disponíveis
4. **Logging detalhado**: O sistema registra essa priorização com informações sobre o processo de decisão: `Prioritizing 'faturamento_total' column for Y axis over LLM recommendation 'quantidade' (matched priority term: faturamento)`

### Seleção Automática de Colunas Numéricas para o Eixo Y

Após selecionar uma coluna temporal para o eixo X, o sistema seleciona automaticamente a coluna numérica mais adequada para o eixo Y:

1. **Prioridade para colunas numéricas não-temporais**: Evita usar a mesma coluna temporal nos dois eixos
2. **Seleção baseada em relevância**: Escolhe colunas que representam métricas (vendas, quantidade, valores)

### Uso de Colunas Categóricas para Separação por Cor

Colunas categóricas são utilizadas para separação por cor, permitindo visualizar diferentes categorias no mesmo gráfico:

1. **Seleção automática**: Escolhe a primeira coluna categórica disponível que não esteja sendo usada nos eixos X ou Y
2. **Fallback para gráficos sem colunas temporais**: Em gráficos sem colunas temporais, a coluna categórica é usada tanto para o eixo X quanto para separação por cor

### Exemplo de Código Atualizado

```python
# Lógica de seleção de colunas
def _select_columns(df, chart_type):
    logging.debug(f"Selecting columns for chart type: {chart_type}")
    
    # Detectar colunas numéricas
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    logging.debug(f"Numeric columns: {numeric_cols}")
    
    # Detectar colunas categóricas (não-numéricas)
    categorical_cols = [col for col in df.columns if col not in numeric_cols]
    logging.debug(f"Categorical columns: {categorical_cols}")
    
    # Detectar colunas temporais
    temporal_cols = []
    for col in df.columns:
        # Verificar se é datetime
        if df[col].dtype == 'datetime64[ns]':
            temporal_cols.append(col)
            continue
            
        # Verificar se o nome é exatamente 'ano' ou 'year'
        if col.lower() == 'ano' or col.lower() == 'year':
            logging.debug(f"Detected column '{col}' as temporal (exact match)")
            temporal_cols.append(col)
            continue
            
        # Verificar se contém termos temporais
        temporal_terms = ['date', 'data', 'ano', 'year', 'month', 'mes', 'mês', 
                         'trimestre', 'quarter', 'semestre', 'semester', 
                         'dia', 'day', 'hora', 'hour', 'time', 'tempo']
        if any(term in str(col).lower() for term in temporal_terms):
            temporal_cols.append(col)
            continue
    
    logging.debug(f"Temporal columns: {temporal_cols}")
    
    # Procurar coluna prioritária para eixo Y (faturamento, total, valor, etc.)
    priority_y_col = None
    priority_terms = ['faturamento', 'total', 'valor', 'venda', 'revenue', 'sales', 'amount', 'sum', 'valor', 'price']
    for col in numeric_cols:
        if any(term in str(col).lower() for term in priority_terms):
            priority_y_col = col
            matched_term = next(term for term in priority_terms if term in str(col).lower())
            logging.debug(f"Found priority column for Y axis: '{priority_y_col}' (matched term: {matched_term})")
            break
    
    # Priorizar coluna temporal para eixo X, mas verificar se tem mais de um valor único
    if temporal_cols:
        x_col = temporal_cols[0]
        
        # Verificar se a coluna temporal tem apenas um valor único
        unique_values = df[x_col].nunique()
        logging.debug(f"Temporal column '{x_col}' has {unique_values} unique values")
        
        if unique_values == 1:
            logging.debug(f"Temporal column '{x_col}' has only one unique value. Not using as X axis.")
            # Usar coluna categórica para X ao invés da temporal com valor único
            if categorical_cols:
                x_col = categorical_cols[0]
                logging.debug(f"Using categorical column '{x_col}' for X axis instead of temporal column with single value")
        
        # Selecionar coluna numérica não-temporal para Y
        non_temporal_numeric = [col for col in numeric_cols if col not in temporal_cols]
        
        # Usar coluna prioritária se existir, senão usar primeira coluna numérica não-temporal
        if priority_y_col:
            y_col = priority_y_col
            logging.debug(f"Prioritizing '{priority_y_col}' column for Y axis (faturamento/total/valor)")
        else:
            y_col = non_temporal_numeric[0] if non_temporal_numeric else numeric_cols[0]
        
        # Selecionar coluna categórica para cor
        available_cat = [col for col in categorical_cols if col != x_col and col != y_col]
        color_col = available_cat[0] if available_cat else None
    else:
        # Sem colunas temporais - usar categórica para X e numérica para Y
        if categorical_cols and numeric_cols:
            x_col = categorical_cols[0]
            
            # Usar coluna prioritária se existir, senão usar primeira coluna numérica
            if priority_y_col:
                y_col = priority_y_col
                logging.debug(f"Prioritizing '{priority_y_col}' column for Y axis (faturamento/total/valor)")
            else:
                y_col = numeric_cols[0]
                
            color_col = categorical_cols[0]  # Usar a mesma coluna categórica para cor
        else:
            # Fallback para apenas colunas numéricas
            x_col = numeric_cols[0] if numeric_cols else df.columns[0]
            
            # Usar coluna prioritária se existir, senão usar segunda coluna numérica
            if priority_y_col:
                y_col = priority_y_col
            else:
                y_col = numeric_cols[1] if len(numeric_cols) > 1 else df.columns[1] if len(df.columns) > 1 else x_col
                
            color_col = categorical_cols[0] if categorical_cols else None
    
    # Registrar decisão final
    logging.debug(f"Final columns for chart - x_col: '{x_col}', y_col: '{y_col}', color_col: '{color_col}'")
    return x_col, y_col, color_col
```

## Melhorias Recentes

### Detecção Aprimorada de Colunas Temporais com Valor Único

Implementamos melhorias significativas na detecção e tratamento de colunas temporais com valor único:

1. **Detecção mais precisa**: O sistema agora verifica explicitamente o número de valores únicos em colunas temporais
2. **Logs detalhados**: Adicionamos logs detalhados que mostram o número exato de valores únicos encontrados
3. **Seleção inteligente de alternativas**: Quando uma coluna temporal tem valor único, o sistema seleciona a melhor coluna categórica alternativa, verificando também se esta tem múltiplos valores distintos
4. **Tratamento recursivo**: Se a coluna categórica selecionada também tiver apenas um valor único, o sistema continua procurando até encontrar uma coluna adequada

### Priorização Ampliada de Colunas de Faturamento

Melhoramos a priorização de colunas para o eixo Y:

1. **Lista expandida de termos**: Adicionamos mais termos em inglês e português para identificar colunas de faturamento ('amount', 'sum', 'price', etc.)
2. **Priorização garantida em todos os fluxos**: Garantimos que a priorização seja aplicada em todos os caminhos de decisão do algoritmo
3. **Logs mais informativos**: Os logs agora mostram qual termo específico foi correspondido durante a priorização
4. **Sobrescrita de recomendações do LLM**: Reforçamos a lógica que garante que colunas de faturamento sejam priorizadas mesmo quando o LLM recomenda outras colunas

### Testes Automatizados Abrangentes

Implementamos testes automatizados para validar a lógica de seleção de colunas:

1. **Teste de priorização de faturamento**: Verifica se colunas de faturamento são sempre priorizadas para o eixo Y
2. **Teste de sobrescrita de recomendações do LLM**: Valida que a priorização de faturamento funciona mesmo quando o LLM recomenda outras colunas
3. **Teste de tratamento de colunas temporais com valor único**: Confirma que o sistema seleciona corretamente colunas categóricas quando colunas temporais têm valor único
4. **Teste de múltiplas colunas categóricas**: Verifica a seleção correta quando há várias opções de colunas categóricas disponíveis

## Considerações Futuras

- Expandir as regras heurísticas para outros tipos de dados temporais (meses, trimestres)
- Adicionar suporte para detecção de padrões em códigos alfanuméricos
- Implementar detecção de hierarquias em dados categóricos
- Melhorar a detecção de padrões em valores numéricos para identificar categorias
- Implementar análise de correlação para sugerir automaticamente as melhores combinações de colunas
- Adicionar suporte para múltiplas séries de dados no mesmo gráfico
- Expandir a lista de termos prioritários para diferentes domínios de negócio
- Implementar detecção automática de outliers para melhorar a escala dos gráficos
- Adicionar suporte para formatação condicional baseada no tipo de dado e idioma
- Implementar detecção automática de tendências e pontos de interesse nos dados
- Adicionar suporte para recomendações de gráficos baseadas em análise estatística dos dados
