#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para traduzir automaticamente arquivos CSV do Mount and Blade Warband
do francês (ou outros idiomas) para português brasileiro (PT-BR)

Autor: Bypass
Data: 2025
"""

import os
import csv
import time
from pathlib import Path
from typing import List, Tuple, Optional
import requests
from langdetect import detect, DetectorFactory
from googletrans import Translator
import logging

# Configurar seed para detecção consistente de idioma
DetectorFactory.seed = 0

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('translation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MountBladeTranslator:
    def __init__(self, input_dir: str, output_dir: str, target_lang: str = 'pt'):
        """
        Inicializa o tradutor para arquivos Mount and Blade
        
        Args:
            input_dir: Diretório com arquivos CSV de entrada
            output_dir: Diretório para arquivos CSV traduzidos
            target_lang: Idioma alvo (padrão: 'pt' para português)
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.target_lang = target_lang
        self.translator = Translator()
        
        # Criar diretório de saída se não existir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Estatísticas
        self.stats = {
            'files_processed': 0,
            'lines_translated': 0,
            'errors': 0
        }
        
        logger.info(f"Tradutor inicializado: {input_dir} -> {output_dir}")
        logger.info(f"Idioma alvo: {target_lang}")
    
    def detect_language(self, text: str) -> Optional[str]:
        """
        Detecta o idioma de um texto
        
        Args:
            text: Texto para detectar idioma
            
        Returns:
            Código do idioma detectado ou None se falhar
        """
        try:
            # Limpar texto para melhor detecção
            clean_text = text.strip()
            if len(clean_text) < 3:
                return None
                
            detected = detect(clean_text)
            return detected
        except Exception as e:
            logger.debug(f"Erro na detecção de idioma para '{text[:50]}...': {e}")
            return None
    
    def translate_text(self, text: str, src_lang: str = 'auto') -> str:
        """
        Traduz um texto para o idioma alvo
        
        Args:
            text: Texto a ser traduzido
            src_lang: Idioma de origem (padrão: 'auto')
            
        Returns:
            Texto traduzido
        """
        try:
            # Verificar se já está em português
            detected_lang = self.detect_language(text)
            if detected_lang == 'pt':
                return text
            
            # Traduzir
            result = self.translator.translate(
                text, 
                src=src_lang, 
                dest=self.target_lang
            )
            
            translated = result.text
            
            # Log da tradução
            logger.debug(f"Traduzido ({detected_lang}->{self.target_lang}): '{text}' -> '{translated}'")
            
            return translated
            
        except Exception as e:
            logger.warning(f"Erro na tradução de '{text[:50]}...': {e}")
            return text  # Retorna texto original em caso de erro
    
    def process_csv_line(self, line: str) -> str:
        """
        Processa uma linha do CSV, traduzindo apenas a parte após o separador '|'
        
        Args:
            line: Linha do CSV
            
        Returns:
            Linha processada com tradução
        """
        line = line.strip()
        
        # Verificar se a linha contém o separador
        if '|' not in line:
            return line
        
        # Dividir em parâmetro e texto
        parts = line.split('|', 1)
        if len(parts) != 2:
            return line
        
        parameter = parts[0]
        text_to_translate = parts[1]
        
        # Verificar se há texto para traduzir
        if not text_to_translate.strip():
            return line
        
        # Traduzir apenas o texto
        translated_text = self.translate_text(text_to_translate)
        
        # Reconstruir a linha
        return f"{parameter}|{translated_text}"
    
    def process_csv_file(self, input_file: Path) -> bool:
        """
        Processa um arquivo CSV completo
        
        Args:
            input_file: Caminho do arquivo de entrada
            
        Returns:
            True se processado com sucesso, False caso contrário
        """
        try:
            output_file = self.output_dir / input_file.name
            
            logger.info(f"Processando: {input_file.name}")
            
            with open(input_file, 'r', encoding='utf-8') as infile, \
                 open(output_file, 'w', encoding='utf-8', newline='') as outfile:
                
                lines_processed = 0
                
                for line_num, line in enumerate(infile, 1):
                    try:
                        # Processar linha
                        processed_line = self.process_csv_line(line.rstrip('\n\r'))
                        outfile.write(processed_line + '\n')
                        
                        lines_processed += 1
                        
                        # Log de progresso a cada 100 linhas
                        if line_num % 100 == 0:
                            logger.info(f"  Processadas {line_num} linhas...")
                        
                        # Pequena pausa para evitar rate limiting
                        if line_num % 10 == 0:
                            time.sleep(0.1)
                            
                    except Exception as e:
                        logger.error(f"Erro na linha {line_num} de {input_file.name}: {e}")
                        # Escrever linha original em caso de erro
                        outfile.write(line)
                        self.stats['errors'] += 1
            
            self.stats['lines_translated'] += lines_processed
            logger.info(f"Concluído: {input_file.name} ({lines_processed} linhas)")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao processar {input_file}: {e}")
            self.stats['errors'] += 1
            return False
    
    def translate_all_files(self) -> None:
        """
        Traduz todos os arquivos CSV no diretório de entrada
        """
        logger.info("Iniciando tradução de todos os arquivos CSV...")
        
        # Encontrar todos os arquivos CSV
        csv_files = list(self.input_dir.glob('*.csv'))
        
        if not csv_files:
            logger.warning(f"Nenhum arquivo CSV encontrado em {self.input_dir}")
            return
        
        logger.info(f"Encontrados {len(csv_files)} arquivos CSV")
        
        # Processar cada arquivo
        for csv_file in csv_files:
            try:
                success = self.process_csv_file(csv_file)
                if success:
                    self.stats['files_processed'] += 1
                    
            except KeyboardInterrupt:
                logger.info("Tradução interrompida pelo usuário")
                break
            except Exception as e:
                logger.error(f"Erro inesperado ao processar {csv_file}: {e}")
        
        # Exibir estatísticas finais
        self.print_stats()
    
    def print_stats(self) -> None:
        """
        Exibe estatísticas da tradução
        """
        logger.info("=== ESTATÍSTICAS DA TRADUÇÃO ===")
        logger.info(f"Arquivos processados: {self.stats['files_processed']}")
        logger.info(f"Linhas traduzidas: {self.stats['lines_translated']}")
        logger.info(f"Erros encontrados: {self.stats['errors']}")
        logger.info("=================================")

def main():
    """
    Função principal
    """
    # Configurações
    input_directory = "c:/Users/Usuario/Downloads/MountAndBlade - TranslatePTBR/input/"
    output_directory = "c:/Users/Usuario/Downloads/MountAndBlade - TranslatePTBR/output/"
    target_language = "pt"  # Português brasileiro
    
    try:
        # Verificar se os diretórios existem
        if not os.path.exists(input_directory):
            logger.error(f"Diretório de entrada não encontrado: {input_directory}")
            return
        
        # Criar tradutor
        translator = MountBladeTranslator(
            input_dir=input_directory,
            output_dir=output_directory,
            target_lang=target_language
        )
        
        # Executar tradução
        translator.translate_all_files()
        
        logger.info("Tradução concluída com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        raise

if __name__ == "__main__":
    main()