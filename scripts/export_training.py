#!/usr/bin/env python3
"""
Export Training Data Script
Exports processed data from database to JSONL format for training
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
import json
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.db_manager import DatabaseManager
from src.processors.data_formatter import DataFormatter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Export training data from database to JSONL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export all unused training data
  python export_training.py --output training_data.jsonl

  # Export with train/validation split
  python export_training.py --output training_data.jsonl --split-validation 0.1

  # Export specific format only
  python export_training.py --output alpaca_data.jsonl --format alpaca

  # Export limited number of examples
  python export_training.py --output sample.jsonl --max-examples 1000

  # Export and create metadata
  python export_training.py --output data.jsonl --with-metadata
        """
    )
    
    parser.add_argument('--output', type=str, required=True,
                       help='Output JSONL file path')
    parser.add_argument('--format', type=str, choices=['alpaca', 'chatml', 'raw'],
                       help='Filter by training format')
    parser.add_argument('--unused-only', action='store_true', default=True,
                       help='Export only unused examples (default: True)')
    parser.add_argument('--max-examples', type=int,
                       help='Maximum number of examples to export')
    parser.add_argument('--split-validation', type=float,
                       help='Create validation split (0.0-1.0)')
    parser.add_argument('--with-metadata', action='store_true',
                       help='Include metadata in export')
    parser.add_argument('--shuffle', action='store_true', default=True,
                       help='Shuffle data before export (default: True)')
    
    args = parser.parse_args()
    
    # Initialize components
    db = DatabaseManager()
    formatter = DataFormatter()
    
    # Get statistics first
    stats = db.get_statistics()
    logger.info(f"Database contains {stats['total_training_examples']:,} training examples")
    
    # Export data
    logger.info(f"Exporting training data...")
    
    filters = {
        'unused_only': args.unused_only,
        'format_type': args.format,
        'limit': args.max_examples
    }
    
    training_data = db.get_training_data(**filters)
    
    if not training_data:
        logger.error("No training data found matching the criteria")
        sys.exit(1)
    
    logger.info(f"Retrieved {len(training_data)} examples")
    
    # Handle train/validation split
    if args.split_validation:
        split_point = int(len(training_data) * (1 - args.split_validation))
        train_data = training_data[:split_point]
        val_data = training_data[split_point:]
        
        # Save training set
        train_path = Path(args.output).with_suffix('') + '_train.jsonl'
        formatter.save_to_jsonl(train_data, str(train_path))
        logger.info(f"Saved {len(train_data)} training examples to {train_path}")
        
        # Save validation set
        val_path = Path(args.output).with_suffix('') + '_val.jsonl'
        formatter.save_to_jsonl(val_data, str(val_path))
        logger.info(f"Saved {len(val_data)} validation examples to {val_path}")
        
        # Create combined metadata
        metadata = {
            'created_at': datetime.now().isoformat(),
            'total_examples': len(training_data),
            'train_examples': len(train_data),
            'validation_examples': len(val_data),
            'split_ratio': args.split_validation,
            'statistics': formatter.get_statistics(training_data)
        }
        
    else:
        # Save all data to single file
        formatter.save_to_jsonl(training_data, args.output)
        logger.info(f"Saved {len(training_data)} examples to {args.output}")
        
        metadata = {
            'created_at': datetime.now().isoformat(),
            'total_examples': len(training_data),
            'statistics': formatter.get_statistics(training_data)
        }
    
    # Save metadata if requested
    if args.with_metadata:
        metadata_path = Path(args.output).with_suffix('.meta.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Saved metadata to {metadata_path}")
    
    # Validate exported file
    logger.info("Validating exported data...")
    is_valid, errors = formatter.validate_jsonl(args.output if not args.split_validation 
                                               else str(train_path))
    
    if is_valid:
        logger.info("✅ Exported data is valid and ready for training!")
    else:
        logger.error("❌ Validation errors found:")
        for error in errors[:5]:
            logger.error(f"  - {error}")
    
    # Print summary
    print("\n" + "="*60)
    print("EXPORT SUMMARY")
    print("="*60)
    print(f"Total examples exported: {len(training_data):,}")
    print(f"Estimated tokens: {metadata['statistics']['total_tokens_estimate']:,}")
    print(f"Average input length: {metadata['statistics']['avg_input_length']:.0f} chars")
    print(f"Average output length: {metadata['statistics']['avg_output_length']:.0f} chars")
    
    if args.split_validation:
        print(f"Training examples: {len(train_data):,}")
        print(f"Validation examples: {len(val_data):,}")
    
    print("\n✅ Data is ready for fine-tuning on RunPod!")
    print("\nNext steps:")
    print("1. Upload the JSONL file(s) to RunPod")
    print("2. Set up the Llama 3.1 environment with QLoRA")
    print("3. Start fine-tuning with your domain-specific data")
    print("="*60)


if __name__ == "__main__":
    main()