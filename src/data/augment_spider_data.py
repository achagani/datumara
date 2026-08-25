#!/usr/bin/env python3
"""
Schema Augmentation Pipeline for Spider Dataset

Converts Spider training data to include database schema context:
  Raw: {question: "...", query: "SELECT ..."}
  Augmented: {prompt: "Tables:...\n\nQuestion:...", response: "SELECT ..."}

This enables models to learn schema-aware SQL generation.
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple


def schema_to_text(schema: Dict) -> str:
    """
    Convert database schema JSON to human-readable text format.
    
    Format:
        table_name(col1 (type1), col2 (type2), ...)
        other_table(col1 (type1), col2 (type2), ...)
    
    Args:
        schema: Dictionary with 'table_names', 'column_names', 'column_types'
    
    Returns:
        Human-readable schema string
    """
    # Group columns by table
    table_columns = defaultdict(list)
    for col_idx, (table_idx, col_name) in enumerate(schema['column_names']):
        if table_idx >= 0:  # Skip the * column (index -1)
            col_type = schema['column_types'][col_idx]
            table_columns[table_idx].append((col_idx, col_name, col_type))
    
    # Format each table with its columns
    text_parts = []
    for table_idx, table_name in enumerate(schema['table_names']):
        cols = table_columns.get(table_idx, [])
        col_strs = [f"{col_name} ({col_type})" for _, col_name, col_type in cols]
        text_parts.append(f"{table_name}({', '.join(col_strs)})")
    
    return '\n'.join(text_parts)


def augment_example(
    example: Dict,
    schema: Dict,
    schema_key: str = "Tables:"
) -> Dict:
    """
    Augment a single training example with schema context.
    
    Args:
        example: Training example with 'question' and 'query' fields
        schema: Database schema dictionary
        schema_key: Label for schema section (default "Tables:")
    
    Returns:
        Augmented example with 'prompt' and 'response' fields
    """
    schema_text = schema_to_text(schema)
    
    augmented_prompt = (
        f"{schema_key}\n{schema_text}\n\n"
        f"Question: {example['question']}"
    )
    
    return {
        "prompt": augmented_prompt,
        "response": example['query']
    }


def augment_dataset(
    examples_file: Path,
    schema_file: Path,
    output_file: Path,
    limit: int = None
) -> Dict:
    """
    Augment entire dataset with schema context.
    
    Args:
        examples_file: Path to train.json (Spider training examples)
        schema_file: Path to tables.json (Spider schemas)
        output_file: Path to write augmented JSONL
        limit: Optional limit on examples to process
    
    Returns:
        Statistics dictionary
    """
    print(f"Loading data from {examples_file}...")
    with open(examples_file) as f:
        examples = json.load(f)
    
    print(f"Loading schemas from {schema_file}...")
    with open(schema_file) as f:
        schemas = json.load(f)
    
    # Create lookup
    schema_dict = {s['db_id']: s for s in schemas}
    
    # Limit if specified
    if limit:
        examples = examples[:limit]
    
    print(f"Augmenting {len(examples)} examples...")
    
    augmented = []
    skipped = 0
    
    for i, example in enumerate(examples):
        db_id = example['db_id']
        schema = schema_dict.get(db_id)
        
        if schema:
            augmented_ex = augment_example(example, schema)
            augmented.append(augmented_ex)
        else:
            skipped += 1
        
        if (i + 1) % 1000 == 0:
            print(f"  Processed {i + 1}/{len(examples)}")
    
    print(f"Writing augmented data to {output_file}...")
    with open(output_file, 'w') as f:
        for item in augmented:
            f.write(json.dumps(item) + '\n')
    
    stats = {
        "total_input": len(examples),
        "augmented": len(augmented),
        "skipped": skipped,
        "output_file": str(output_file),
        "output_lines": len(augmented),
        "augmentation_rate": len(augmented) / len(examples) if examples else 0
    }
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Augment Spider dataset with schema context"
    )
    parser.add_argument(
        "--examples",
        type=Path,
        default=Path("data/spider/evaluation_examples/examples/train_spider.json"),
        help="Path to Spider training examples JSON"
    )
    parser.add_argument(
        "--schemas",
        type=Path,
        default=Path("data/spider/evaluation_examples/examples/tables.json"),
        help="Path to Spider schema tables JSON"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/spider_augmented_train.jsonl"),
        help="Output path for augmented JSONL"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of examples to process (for testing)"
    )
    
    args = parser.parse_args()
    
    # Create output directory
    args.output.parent.mkdir(parents=True, exist_ok=True)
    
    # Run augmentation
    stats = augment_dataset(
        args.examples,
        args.schemas,
        args.output,
        limit=args.limit
    )
    
    print("\n" + "=" * 60)
    print("AUGMENTATION COMPLETE")
    print("=" * 60)
    print(f"Input examples: {stats['total_input']}")
    print(f"Augmented: {stats['augmented']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"Success rate: {stats['augmentation_rate']*100:.1f}%")
    print(f"Output: {stats['output_file']}")
    print(f"Lines: {stats['output_lines']}")


if __name__ == "__main__":
    main()
