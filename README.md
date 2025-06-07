# Mount and Blade Warband - Tradutor Automático OTIMIZADO

Este projeto contém um sistema automático OTIMIZADO para traduzir arquivos CSV de mods do Mount and Blade Warband de qualquer idioma para português brasileiro (PT-BR) com máxima velocidade e eficiência.

## 🚀 Características OTIMIZADAS

- **Detecção automática de idioma**: Identifica automaticamente o idioma dos textos
- **Tradução paralela**: Processamento multithreading para máxima velocidade
- **Cache inteligente**: Sistema de cache para evitar traduções duplicadas
- **Modo Turbo**: Opção de velocidade máxima com mais recursos
- **Processamento em lotes**: Otimização para grandes volumes de texto
- **Pool de tradutores**: Múltiplas instâncias para evitar rate limiting
- **Preservação da estrutura**: Mantém a formatação original dos arquivos CSV
- **Log detalhado**: Registra todo o processo de tradução
- **Tratamento de erros**: Continua a tradução mesmo com erros pontuais
- **Estatísticas avançadas**: Relatório completo com velocidade e idiomas detectados
- **Barra de progresso**: Interface visual em tempo real do progresso

## 🚀 Como usar

### Método 1: Execução automática (Recomendado)

1. **Coloque seus arquivos CSV** na pasta `input/`
2. **Execute o arquivo** `run_translator.bat`
3. **Aguarde a conclusão** da tradução
4. **Verifique os resultados** na pasta `output/`

### Método 2: Execução manual

1. **Instale o Python 3.7+** se não tiver instalado
2. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Execute o script otimizado**:
   ```bash
   python translate_optimized.py
   ```

## 📁 Estrutura do projeto

```
MountAndBlade - TranslatePTBR/
├── input/                     # Arquivos CSV originais (qualquer idioma)
│   ├── dialogs.csv
│   ├── troops.csv
│   ├── item_kinds.csv
│   └── ...
├── output/                    # Arquivos CSV traduzidos (português)
│   └── translation_cache_optimized.json  # Cache de traduções
├── translate_optimized.py     # Script OTIMIZADO de tradução
├── translate_protected.py     # Script com proteção de variáveis
├── translate_csv.py          # Script básico (legado)
├── requirements.txt          # Dependências do Python
├── run_translator.bat        # Script de execução automática
├── README.md                # Este arquivo
├── translation_optimized.log # Log das traduções otimizadas
└── translation.log          # Log das traduções básicas
```

## ⚡ Modos de Operação

O script otimizado oferece dois modos de operação:

### 🚀 Modo Turbo
- **Máxima velocidade**: Até 32 threads simultâneas
- **Lotes maiores**: Processa 50 textos por vez
- **Delay reduzido**: 0.05s entre traduções
- **Uso intensivo de recursos**: Recomendado para PCs potentes

### ⚡ Modo Padrão
- **Velocidade equilibrada**: Até 8 threads simultâneas
- **Lotes moderados**: Processa 20 textos por vez
- **Delay padrão**: 0.1s entre traduções
- **Uso moderado de recursos**: Recomendado para uso geral

## 🔧 Configurações

### Modificar idioma alvo

Para traduzir para outro idioma, edite o arquivo `translate_optimized.py` e altere:

```python
target_language = "pt"  # Português brasileiro
```

Códigos de idioma suportados:
- `pt` - Português
- `en` - Inglês
- `es` - Espanhol
- `de` - Alemão
- `it` - Italiano
- E muitos outros...

### Ajustar velocidade de tradução

Para evitar rate limiting, o script faz pausas entre traduções. Para ajustar:

```python
# Pausa a cada 10 linhas (em segundos)
time.sleep(0.1)  # Diminua para mais velocidade, aumente para mais estabilidade
```

## 📊 Formato dos arquivos

Os arquivos CSV do Mount and Blade seguem o formato:

```
parametro|texto_para_traduzir
```

**Exemplo:**
```
dlga_do_lady_options:lady_end_talk.3|Nous parlerons plus tard.
```

**Resultado:**
```
dlga_do_lady_options:lady_end_talk.3|Falaremos mais tarde.
```

## 🐛 Solução de problemas

### Erro: "Python não encontrado"
- Instale o Python 3.7+ em https://python.org
- Certifique-se de marcar "Add Python to PATH" durante a instalação

### Erro: "Falha na instalação das dependências"
- Execute como administrador
- Verifique sua conexão com a internet
- Tente: `pip install --upgrade pip`

### Tradução muito lenta
- Reduza o tempo de pausa no código
- Verifique sua conexão com a internet
- O Google Translate pode ter rate limiting

### Alguns textos não foram traduzidos
- Textos muito curtos (< 3 caracteres) são ignorados
- Textos já em português são mantidos
- Erros de tradução mantêm o texto original

## 📝 Log de tradução

O arquivo `translation_optimized.log` contém:
- Progresso da tradução em tempo real
- Idiomas detectados automaticamente
- Estatísticas de performance (velocidade, cache hits)
- Erros encontrados
- Estatísticas finais detalhadas
- Modo turbo vs padrão

O arquivo `translation.log` (legado) contém:
- Log do script básico `translate_csv.py`

## ⚠️ Limitações

- **Rate limiting**: O Google Translate pode limitar muitas requisições
- **Contexto**: Traduções automáticas podem perder contexto específico do jogo
- **Termos técnicos**: Nomes próprios e termos específicos podem ser traduzidos incorretamente

## 🔍 Verificação manual

Após a tradução automática, recomenda-se:

1. **Revisar termos específicos** do jogo
2. **Verificar nomes próprios** (cidades, personagens)
3. **Testar no jogo** para garantir que tudo funciona
4. **Fazer ajustes manuais** se necessário

## 📞 Suporte

Em caso de problemas:

1. Verifique o arquivo `translation.log`
2. Certifique-se de que todos os arquivos estão na pasta `input/`
3. Verifique se o Python e as dependências estão instalados
4. Teste com um arquivo pequeno primeiro

## 🎮 Sobre Mount and Blade Warband

Este script foi desenvolvido especificamente para mods do Mount and Blade Warband que utilizam arquivos CSV para textos do jogo. É compatível com a maioria dos mods populares que seguem esta estrutura.

---

**Desenvolvido para a comunidade Mount and Blade Brasil** 🇧🇷

---
Dev: Bypass - 2025