#!/usr/bin/env python3
"""
Data Validation Script
Validates and analyzes training data quality before fine-tuning
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import statistics
from collections import Counter
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.processors.data_formatter import DataFormatter
from src.database.db_manager import DatabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataValidator:
    """Validate training data quality"""
    
    def __init__(self):
        self.formatter = DataFormatter()
        self.db = DatabaseManager()
        self.issues = []
        self.warnings = []
        self.stats = {}
    
    def validate_jsonl_file(self, file_path: str) -> Tuple[bool, Dict]:
        """
        Comprehensive validation of JSONL training file
        
        Args:
            file_path: Path to JSONL file
            
        Returns:
            Tuple of (is_valid, statistics)
        """
        logger.info(f"Validating: {file_path}")
        
        # Basic file validation
        is_valid, errors = self.formatter.validate_jsonl(file_path)
        
        if not is_valid:
            self.issues.extend(errors)
            return False, {}
        
        # Load and analyze data
        training_data = self._load_jsonl(file_path)
        
        if not training_data:
            self.issues.append("No valid training examples found")
            return False, {}
        
        # Perform comprehensive checks
        self._check_data_format(training_data)
        self._check_data_quality(training_data)
        self._check_data_distribution(training_data)
        self._check_content_quality(training_data)
        self._calculate_statistics(training_data)
        
        # Generate report
        is_valid = len(self.issues) == 0
        
        return is_valid, self.stats
    
    def _load_jsonl(self, file_path: str) -> List[Dict]:
        """Load JSONL file"""
        data = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                try:
                    example = json.loads(line)
                    data.append(example)
                except json.JSONDecodeError as e:
                    self.issues.append(f"Line {i}: Invalid JSON - {str(e)}")
                    
        return data
    
    def _check_data_format(self, data: List[Dict]):
        """Check data format consistency"""
        formats = set()
        
        for i, example in enumerate(data):
            if 'instruction' in example:
                formats.add('alpaca')
                # Check Alpaca format
                if not all(k in example for k in ['instruction', 'input', 'output']):
                    self.issues.append(f"Example {i}: Incomplete Alpaca format")
                    
            elif 'messages' in example:
                formats.add('chatml')
                # Check ChatML format
                if not isinstance(example['messages'], list):
                    self.issues.append(f"Example {i}: Invalid ChatML format")
                    
            elif 'text' in example:
                formats.add('raw')
            else:
                self.issues.append(f"Example {i}: Unknown format")
        
        if len(formats) > 1:
            self.warnings.append(f"Mixed formats detected: {formats}")
            
        self.stats['formats'] = list(formats)
    
    def _check_data_quality(self, data: List[Dict]):
        """Check data quality metrics"""
        
        # Length checks
        lengths = []
        empty_count = 0
        
        for i, example in enumerate(data):
            text_content = self._extract_text(example)
            length = len(text_content)
            lengths.append(length)
            
            if length == 0:
                empty_count += 1
                self.issues.append(f"Example {i}: Empty content")
            elif length < 10:
                self.warnings.append(f"Example {i}: Very short content ({length} chars)")
            elif length > 10000:
                self.warnings.append(f"Example {i}: Very long content ({length} chars)")
        
        if lengths:
            self.stats['avg_length'] = statistics.mean(lengths)
            self.stats['min_length'] = min(lengths)
            self.stats['max_length'] = max(lengths)
            self.stats['empty_examples'] = empty_count
    
    def _check_data_distribution(self, data: List[Dict]):
        """Check data distribution and diversity"""
        
        # Check for duplicates
        seen_hashes = set()
        duplicate_count = 0
        
        for i, example in enumerate(data):
            content = json.dumps(example, sort_keys=True)
            content_hash = hash(content)
            
            if content_hash in seen_hashes:
                duplicate_count += 1
                self.warnings.append(f"Example {i}: Duplicate content")
            else:
                seen_hashes.add(content_hash)
        
        self.stats['unique_examples'] = len(seen_hashes)
        self.stats['duplicate_examples'] = duplicate_count
        
        # Check diversity
        all_text = ' '.join(self._extract_text(ex) for ex in data[:100])  # Sample
        words = all_text.lower().split()
        
        if words:
            vocab_size = len(set(words))
            total_words = len(words)
            diversity = vocab_size / total_words if total_words > 0 else 0
            
            self.stats['vocabulary_diversity'] = diversity
            
            if diversity < 0.2:
                self.warnings.append(f"Low vocabulary diversity: {diversity:.2f}")
    
    def _check_content_quality(self, data: List[Dict]):
        """Check content quality indicators"""
        
        quality_scores = []
        
        for i, example in enumerate(data[:100]):  # Sample for performance
            text = self._extract_text(example)
            score = self._calculate_quality_score(text)
            quality_scores.append(score)
            
            if score < 0.3:
                self.warnings.append(f"Example {i}: Low quality score ({score:.2f})")
        
        if quality_scores:
            self.stats['avg_quality_score'] = statistics.mean(quality_scores)
            self.stats['min_quality_score'] = min(quality_scores)
    
    def _extract_text(self, example: Dict) -> str:
        """Extract text content from example"""
        if 'instruction' in example:
            parts = [example.get('instruction', ''),
                    example.get('input', ''),
                    example.get('output', '')]
            return ' '.join(parts)
            
        elif 'messages' in example:
            return ' '.join(msg.get('content', '') for msg in example['messages'])
            
        elif 'text' in example:
            return example['text']
            
        return ""
    
    def _calculate_quality_score(self, text: str) -> float:
        """Calculate quality score for text (0-1)"""
        if not text:
            return 0.0
        
        score = 1.0
        
        # Check for minimum length
        if len(text) < 50:
            score *= 0.5
        
        # Check for word diversity
        words = text.split()
        if words:
            unique_words = len(set(words))
            diversity = unique_words / len(words)
            score *= diversity
        
        # Check for special character ratio
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        special_ratio = special_chars / len(text)
        if special_ratio > 0.3:
            score *= 0.7
        
        # Check for numeric content
        numeric_chars = sum(1 for c in text if c.isdigit())
        numeric_ratio = numeric_chars / len(text)
        if numeric_ratio > 0.3:
            score *= 0.8
        
        return min(max(score, 0.0), 1.0)
    
    def _calculate_statistics(self, data: List[Dict]):
        """Calculate comprehensive statistics"""
        
        self.stats['total_examples'] = len(data)
        
        # Token estimation (rough: 1 token ≈ 4 characters)
        total_chars = sum(len(self._extract_text(ex)) for ex in data)
        self.stats['estimated_tokens'] = total_chars // 4
        
        # Training time estimation (very rough)
        # Assuming ~100 tokens/second on RTX 4090
        tokens_per_second = 100
        estimated_seconds = self.stats['estimated_tokens'] / tokens_per_second
        self.stats['estimated_training_hours'] = estimated_seconds / 3600
        
        # Cost estimation for RunPod RTX 4090 (~$0.44/hour)
        hourly_rate = 0.44
        self.stats['estimated_cost_usd'] = self.stats['estimated_training_hours'] * hourly_rate
    
    def print_report(self):
        """Print validation report"""
        print("\n" + "="*60)
        print("DATA VALIDATION REPORT")
        print("="*60)
        
        # Issues
        if self.issues:
            print("\n❌ CRITICAL ISSUES:")
            for issue in self.issues[:10]:  # Show first 10
                print(f"  • {issue}")
            if len(self.issues) > 10:
                print(f"  ... and {len(self.issues) - 10} more issues")
        else:
            print("\n✅ No critical issues found")
        
        # Warnings
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings[:10]:  # Show first 10
                print(f"  • {warning}")
            if len(self.warnings) > 10:
                print(f"  ... and {len(self.warnings) - 10} more warnings")
        
        # Statistics
        print("\n📊 STATISTICS:")
        print(f"  Total examples: {self.stats.get('total_examples', 0):,}")
        print(f"  Unique examples: {self.stats.get('unique_examples', 0):,}")
        print(f"  Duplicate examples: {self.stats.get('duplicate_examples', 0):,}")
        print(f"  Formats: {', '.join(self.stats.get('formats', []))}")
        print(f"  Average length: {self.stats.get('avg_length', 0):.0f} chars")
        print(f"  Length range: {self.stats.get('min_length', 0)} - {self.stats.get('max_length', 0)} chars")
        print(f"  Vocabulary diversity: {self.stats.get('vocabulary_diversity', 0):.2%}")
        print(f"  Average quality score: {self.stats.get('avg_quality_score', 0):.2f}")
        
        # Training estimates
        print("\n🎯 TRAINING ESTIMATES:")
        print(f"  Estimated tokens: {self.stats.get('estimated_tokens', 0):,}")
        print(f"  Estimated training time: {self.stats.get('estimated_training_hours', 0):.1f} hours")
        print(f"  Estimated RunPod cost: ${self.stats.get('estimated_cost_usd', 0):.2f}")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        if self.stats.get('duplicate_examples', 0) > 0:
            print("  • Remove duplicate examples to improve training efficiency")
        
        if self.stats.get('vocabulary_diversity', 1) < 0.3:
            print("  • Consider adding more diverse content")
        
        if self.stats.get('avg_quality_score', 1) < 0.5:
            print("  • Review and improve content quality")
        
        if self.stats.get('estimated_training_hours', 0) > 24:
            print("  • Consider using a smaller subset for initial experiments")
        
        if not self.issues and not self.warnings:
            print("  • Data looks good for training!")
        
        print("\n" + "="*60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Validate training data for Llama fine-tuning"
    )
    
    parser.add_argument('input_file', type=str,
                       help='Path to JSONL training file')
    parser.add_argument('--export-stats', type=str,
                       help='Export statistics to JSON file')
    parser.add_argument('--from-db', action='store_true',
                       help='Validate data from database')
    parser.add_argument('--max-examples', type=int,
                       help='Maximum examples to validate')
    
    args = parser.parse_args()
    
    validator = DataValidator()
    
    if args.from_db:
        # Export from database first
        temp_file = Path('/tmp/validation_temp.jsonl')
        validator.db.export_training_data_to_jsonl(
            str(temp_file),
            limit=args.max_examples
        )
        is_valid, stats = validator.validate_jsonl_file(str(temp_file))
        temp_file.unlink()  # Clean up
    else:
        is_valid, stats = validator.validate_jsonl_file(args.input_file)
    
    # Print report
    validator.print_report()
    
    # Export statistics if requested
    if args.export_stats:
        with open(args.export_stats, 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"\nStatistics exported to: {args.export_stats}")
    
    # Exit with appropriate code
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()