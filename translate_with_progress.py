#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para traduzir arquivos CSV do Mount and Blade Warband
do francês para português brasileiro (PT-BR) com barra de progresso

Versão com tqdm para mostrar progresso em tempo real

Autor: Assistant
Data: 2024
"""

import os
import time
from pathlib import Path
from googletrans import Translator
import logging
from tqdm import tqdm

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('translation_progress.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MountBladeTranslatorWithProgress:
    def __init__(self, input_dir: str, output_dir: str):
        """
        Inicializa o tradutor com barra de progresso
        
        Args:
            input_dir: Diretório com arquivos CSV de entrada
            output_dir: Diretório para arquivos CSV traduzidos
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.translator = Translator()
        
        # Criar diretório de saída
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Estatísticas
        self.stats = {
            'files_processed': 0,
            'lines_translated': 0,
            'lines_skipped': 0,
            'errors': 0
        }
        
        logger.info(f"Tradutor com progresso inicializado: {input_dir} -> {output_dir}")
    
    def count_lines_in_file(self, file_path: Path) -> int:
        """
        Conta o número de linhas em um arquivo
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Número de linhas
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f)
        except Exception:
            return 0
    
    def is_french_text(self, text: str) -> bool:
        """
        Verifica se o texto parece ser francês (método simples)
        
        Args:
            text: Texto para verificar
            
        Returns:
            True se parece francês, False caso contrário
        """
        text_lower = text.lower()
        
        # Palavras comuns em francês
        french_words = [
            'le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'et', 'ou', 'est', 'sont',
            'avec', 'pour', 'dans', 'sur', 'par', 'vous', 'nous', 'ils', 'elle',
            'cette', 'qui', 'que', 'où', 'comment', 'quand', 'pourquoi',
            'très', 'plus', 'moins', 'bien', 'mal', 'bon', 'mauvais', 'grand', 'petit'
        ]
        
        # Verificar se contém palavras francesas
        words = text_lower.split()
        if not words:
            return False
            
        french_count = sum(1 for word in words if any(fw in word for fw in french_words))
        
        # Se mais de 20% das palavras parecem francesas
        return (french_count / len(words)) > 0.2
    
    def should_translate(self, text: str) -> bool:
        """
        Verifica se um texto deve ser traduzido
        
        Args:
            text: Texto a verificar
            
        Returns:
            True se deve traduzir, False caso contrário
        """
        text = text.strip()
        
        # Ignorar textos muito curtos
        if len(text) < 3:
            return False
        
        # Ignorar textos que são apenas números
        if text.isdigit():
            return False
        
        # Ignorar textos que são códigos (maiúsculas com underscore)
        if text.isupper() and '_' in text:
            return False
        
        # Ignorar textos específicos
        ignore_texts = ['INVALID ITEM', 'NO ITEM', 'NONE', 'Correctif bug langage']
        if text in ignore_texts:
            return False
        
        # Verificar se parece francês
        return self.is_french_text(text)
    
    def translate_text(self, text: str) -> str:
        """
        Traduz um texto para português
        
        Args:
            text: Texto a ser traduzido
            
        Returns:
            Texto traduzido ou original em caso de erro
        """
        try:
            # Tentar traduzir
            result = self.translator.translate(text, src='fr', dest='pt')
            translated = result.text
            
            # Pequena pausa para evitar rate limiting
            time.sleep(0.1)
            
            return translated
            
        except Exception as e:
            logger.warning(f"Erro na tradução: {e}")
            self.stats['errors'] += 1
            return text  # Retorna texto original
    
    def process_line(self, line: str) -> str:
        """
        Processa uma linha do CSV
        
        Args:
            line: Linha do CSV
            
        Returns:
            Linha processada
        """
        line = line.strip()
        
        # Verificar se tem o separador
        if '|' not in line:
            return line
        
        # Dividir em parâmetro e texto
        parts = line.split('|', 1)
        if len(parts) != 2:
            return line
        
        parameter = parts[0]
        text = parts[1]
        
        # Verificar se deve traduzir
        if self.should_translate(text):
            translated_text = self.translate_text(text)
            self.stats['lines_translated'] += 1
            return f"{parameter}|{translated_text}"
        else:
            self.stats['lines_skipped'] += 1
            return line
    
    def process_file(self, input_file: Path) -> bool:
        """
        Processa um arquivo CSV com barra de progresso
        
        Args:
            input_file: Arquivo de entrada
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            output_file = self.output_dir / input_file.name
            
            # Contar linhas para a barra de progresso
            total_lines = self.count_lines_in_file(input_file)
            
            logger.info(f"Processando: {input_file.name} ({total_lines} linhas)")
            
            with open(input_file, 'r', encoding='utf-8') as infile, \
                 open(output_file, 'w', encoding='utf-8', newline='') as outfile:
                
                # Criar barra de progresso
                with tqdm(total=total_lines, desc=f"📄 {input_file.name}", 
                         unit="linhas", ncols=100, colour='green') as pbar:
                    
                    for line_num, line in enumerate(infile, 1):
                        try:
                            processed_line = self.process_line(line.rstrip('\n\r'))
                            outfile.write(processed_line + '\n')
                            
                            # Atualizar barra de progresso
                            pbar.update(1)
                            
                            # Atualizar descrição com estatísticas
                            if line_num % 10 == 0:
                                pbar.set_postfix({
                                    'Traduzidas': self.stats['lines_translated'],
                                    'Ignoradas': self.stats['lines_skipped'],
                                    'Erros': self.stats['errors']
                                })
                            
                        except Exception as e:
                            logger.error(f"Erro na linha {line_num}: {e}")
                            outfile.write(line)  # Escrever linha original
                            self.stats['errors'] += 1
                            pbar.update(1)
            
            logger.info(f"✅ Concluído: {input_file.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar {input_file}: {e}")
            return False
    
    def translate_all(self) -> None:
        """
        Traduz todos os arquivos CSV com progresso
        """
        print("🚀 INICIANDO TRADUÇÃO COM PROGRESSO")
        print("=" * 50)
        
        # Encontrar arquivos CSV
        csv_files = list(self.input_dir.glob('*.csv'))
        
        if not csv_files:
            logger.warning(f"❌ Nenhum arquivo CSV encontrado em {self.input_dir}")
            return
        
        logger.info(f"📁 Encontrados {len(csv_files)} arquivos CSV")
        
        # Processar cada arquivo com barra de progresso geral
        with tqdm(csv_files, desc="🗂️  Arquivos", unit="arquivo", colour='blue') as file_pbar:
            for csv_file in file_pbar:
                try:
                    file_pbar.set_description(f"🗂️  {csv_file.name}")
                    
                    success = self.process_file(csv_file)
                    if success:
                        self.stats['files_processed'] += 1
                    
                    # Atualizar estatísticas na barra
                    file_pbar.set_postfix({
                        'Processados': self.stats['files_processed'],
                        'Total Traduzidas': self.stats['lines_translated']
                    })
                    
                    # Pausa entre arquivos
                    time.sleep(1)
                    
                except KeyboardInterrupt:
                    print("\n⏹️  Tradução interrompida pelo usuário")
                    break
                except Exception as e:
                    logger.error(f"❌ Erro inesperado: {e}")
        
        # Estatísticas finais
        self.print_stats()
    
    def print_stats(self) -> None:
        """
        Exibe estatísticas finais
        """
        print("\n" + "=" * 50)
        print("📊 ESTATÍSTICAS FINAIS")
        print("=" * 50)
        print(f"📁 Arquivos processados: {self.stats['files_processed']}")
        print(f"✅ Linhas traduzidas: {self.stats['lines_translated']}")
        print(f"⏭️  Linhas ignoradas: {self.stats['lines_skipped']}")
        print(f"❌ Erros: {self.stats['errors']}")
        print("=" * 50)

def main():
    """
    Função principal
    """
    input_dir = "c:/Users/Usuario/Downloads/MountAndBlade - TranslatePTBR/input/"
    output_dir = "c:/Users/Usuario/Downloads/MountAndBlade - TranslatePTBR/output/"
    
    try:
        if not os.path.exists(input_dir):
            logger.error(f"❌ Diretório não encontrado: {input_dir}")
            return
        
        # Criar e executar tradutor
        translator = MountBladeTranslatorWithProgress(input_dir, output_dir)
        translator.translate_all()
        
        print("\n🎉 TRADUÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"📁 Arquivos salvos em: {output_dir}")
        
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        raise

if __name__ == "__main__":
    main()