"""
Data Formatter Module
Converts cleaned text to JSONL format for Llama 3.1 fine-tuning
"""

import json
import hashlib
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging
from datetime import datetime
import random

logger = logging.getLogger(__name__)


class DataFormatter:
    """
    Format cleaned text into training data for Llama 3.1 fine-tuning
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize data formatter with configuration
        
        Args:
            config: Dictionary with formatting settings
        """
        self.config = config or {}
        
        # Training data parameters
        self.max_length = self.config.get('max_length', 2048)
        self.chunk_size = self.config.get('chunk_size', 1024)
        self.chunk_overlap = self.config.get('chunk_overlap', 128)
        
        # Instruction templates for different training styles
        self.instruction_templates = {
            'qa': {
                'instruction': "Answer the following question based on the provided context.",
                'input_prefix': "Question: ",
                'output_prefix': "Answer: "
            },
            'summarization': {
                'instruction': "Summarize the following text concisely.",
                'input_prefix': "Text: ",
                'output_prefix': "Summary: "
            },
            'completion': {
                'instruction': "Complete the following text in a coherent manner.",
                'input_prefix': "Beginning: ",
                'output_prefix': "Continuation: "
            },
            'extraction': {
                'instruction': "Extract key information from the following document.",
                'input_prefix': "Document: ",
                'output_prefix': "Key Information: "
            },
            'domain_specific': {
                'instruction': "Provide expert analysis of the following domain-specific content.",
                'input_prefix': "Content: ",
                'output_prefix': "Analysis: "
            }
        }
        
        # Load domain-specific prompts if provided
        self.domain_prompts = self.config.get('domain_prompts', [])
        
    def format_for_training(self, 
                           extracted_data: List[Dict], 
                           output_format: str = 'alpaca') -> List[Dict]:
        """
        Format extracted PDF data for training
        
        Args:
            extracted_data: List of extraction results from PDFExtractor
            output_format: Training format ('alpaca', 'chatML', 'raw')
            
        Returns:
            List of formatted training examples
        """
        training_data = []
        
        for doc_data in extracted_data:
            if doc_data.get('extraction_failed'):
                logger.warning(f"Skipping failed extraction: {doc_data.get('filename')}")
                continue
                
            # Get document metadata
            doc_metadata = {
                'source': doc_data.get('filename', 'unknown'),
                'extraction_method': doc_data.get('extraction_method', 'unknown'),
                'quality': doc_data.get('extraction_quality', 'unknown')
            }
            
            # Process the text
            text = doc_data.get('text', '')
            if not text:
                continue
                
            # Create training examples from the text
            if output_format == 'alpaca':
                examples = self._format_alpaca_style(text, doc_metadata)
            elif output_format == 'chatML':
                examples = self._format_chatml_style(text, doc_metadata)
            else:  # raw
                examples = self._format_raw_style(text, doc_metadata)
                
            training_data.extend(examples)
            
        # Add data augmentation if configured
        if self.config.get('augment_data', False):
            training_data = self._augment_training_data(training_data)
            
        # Shuffle if configured
        if self.config.get('shuffle', True):
            random.shuffle(training_data)
            
        logger.info(f"Created {len(training_data)} training examples from {len(extracted_data)} documents")
        
        return training_data
    
    def _format_alpaca_style(self, text: str, metadata: Dict) -> List[Dict]:
        """
        Format text in Alpaca/Stanford style
        
        Format:
        {
            "instruction": "...",
            "input": "...",
            "output": "..."
        }
        """
        examples = []
        chunks = self._create_text_chunks(text)
        
        for i, chunk in enumerate(chunks):
            # Create different types of training examples
            
            # 1. Context-based QA
            if i < len(chunks) - 1:
                example = {
                    "instruction": "Based on the following context, answer questions accurately.",
                    "input": f"Context: {chunk}\n\nWhat is this text about?",
                    "output": self._generate_summary(chunk),
                    "metadata": {**metadata, "chunk_index": i, "type": "qa"}
                }
                examples.append(example)
            
            # 2. Continuation
            if len(chunk) > 200:
                split_point = len(chunk) // 2
                example = {
                    "instruction": "Continue the following text maintaining the same style and topic.",
                    "input": chunk[:split_point],
                    "output": chunk[split_point:],
                    "metadata": {**metadata, "chunk_index": i, "type": "continuation"}
                }
                examples.append(example)
            
            # 3. Domain-specific instruction
            if self.domain_prompts:
                for prompt_template in self.domain_prompts[:2]:  # Use up to 2 templates
                    example = {
                        "instruction": prompt_template.get("instruction", "Analyze the following content."),
                        "input": chunk,
                        "output": self._generate_domain_response(chunk, prompt_template),
                        "metadata": {**metadata, "chunk_index": i, "type": "domain"}
                    }
                    examples.append(example)
                    
        return examples
    
    def _format_chatml_style(self, text: str, metadata: Dict) -> List[Dict]:
        """
        Format text in ChatML style
        
        Format:
        {
            "messages": [
                {"role": "system", "content": "..."},
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."}
            ]
        }
        """
        examples = []
        chunks = self._create_text_chunks(text)
        
        system_prompt = (
            "You are an AI assistant with expertise in the domain covered by this document. "
            "Provide accurate, helpful responses based on the content."
        )
        
        for i, chunk in enumerate(chunks):
            # Create conversation-style examples
            example = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Explain the following content:\n\n{chunk[:500]}"},
                    {"role": "assistant", "content": self._generate_explanation(chunk)}
                ],
                "metadata": {**metadata, "chunk_index": i}
            }
            examples.append(example)
            
        return examples
    
    def _format_raw_style(self, text: str, metadata: Dict) -> List[Dict]:
        """
        Format text in raw completion style
        
        Format:
        {
            "text": "...",
            "metadata": {...}
        }
        """
        examples = []
        chunks = self._create_text_chunks(text)
        
        for i, chunk in enumerate(chunks):
            example = {
                "text": chunk,
                "metadata": {**metadata, "chunk_index": i, "type": "raw"}
            }
            examples.append(example)
            
        return examples
    
    def _create_text_chunks(self, text: str) -> List[str]:
        """Create overlapping text chunks for training"""
        chunks = []
        text_length = len(text)
        
        if text_length <= self.chunk_size:
            return [text]
            
        # Create overlapping chunks
        start = 0
        while start < text_length:
            end = min(start + self.chunk_size, text_length)
            
            # Try to end at a sentence boundary
            if end < text_length:
                # Look for sentence ending
                sentence_end = text.rfind('. ', start, end)
                if sentence_end != -1 and sentence_end > start + self.chunk_size // 2:
                    end = sentence_end + 1
                    
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
                
            # Move start position with overlap
            start = end - self.chunk_overlap
            if start >= text_length - self.chunk_overlap:
                break
                
        return chunks
    
    def _generate_summary(self, text: str, max_length: int = 200) -> str:
        """Generate a simple summary (placeholder for more sophisticated summarization)"""
        # For actual implementation, you might want to use a small model or heuristics
        # This is a simple extractive approach
        sentences = text.split('. ')[:3]
        summary = '. '.join(sentences)
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
        return summary
    
    def _generate_explanation(self, text: str) -> str:
        """Generate an explanation of the text"""
        # Simplified explanation generation
        key_points = []
        sentences = text.split('. ')
        
        # Extract key sentences (simple heuristic)
        for sentence in sentences[:5]:
            if len(sentence) > 20:
                key_points.append(sentence.strip())
                
        if key_points:
            explanation = "This text discusses: " + "; ".join(key_points[:3])
        else:
            explanation = "This text contains domain-specific information."
            
        return explanation
    
    def _generate_domain_response(self, text: str, prompt_template: Dict) -> str:
        """Generate domain-specific response based on template"""
        # This is a placeholder - in practice, you might want to:
        # 1. Use a small model to generate responses
        # 2. Extract key information based on domain rules
        # 3. Use template-based generation
        
        response_type = prompt_template.get("response_type", "extraction")
        
        if response_type == "extraction":
            # Extract key terms and concepts
            words = text.split()
            # Simple heuristic: capitalized words might be important
            key_terms = [w for w in words if w and w[0].isupper()][:10]
            return f"Key concepts: {', '.join(set(key_terms))}"
            
        elif response_type == "analysis":
            return self._generate_explanation(text)
            
        else:
            return self._generate_summary(text)
    
    def _augment_training_data(self, training_data: List[Dict]) -> List[Dict]:
        """Apply data augmentation techniques"""
        augmented = training_data.copy()
        
        for example in training_data[:len(training_data)//4]:  # Augment 25% of data
            # Create variations
            if 'instruction' in example:
                # Paraphrase instruction
                augmented_example = example.copy()
                augmented_example['instruction'] = self._paraphrase_instruction(example['instruction'])
                augmented_example['metadata'] = {**example.get('metadata', {}), 'augmented': True}
                augmented.append(augmented_example)
                
        return augmented
    
    def _paraphrase_instruction(self, instruction: str) -> str:
        """Simple instruction paraphrasing"""
        paraphrases = {
            "Answer": ["Respond to", "Address", "Reply to"],
            "Explain": ["Describe", "Clarify", "Elaborate on"],
            "Summarize": ["Provide a summary of", "Briefly describe", "Give an overview of"],
            "Analyze": ["Examine", "Evaluate", "Assess"],
        }
        
        for original, alternatives in paraphrases.items():
            if original in instruction:
                return instruction.replace(original, random.choice(alternatives))
                
        return instruction
    
    def save_to_jsonl(self, training_data: List[Dict], output_path: str):
        """
        Save training data to JSONL file
        
        Args:
            training_data: List of training examples
            output_path: Path to output JSONL file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for example in training_data:
                # Remove metadata before saving (if not needed in training)
                if self.config.get('include_metadata', False):
                    json_line = json.dumps(example, ensure_ascii=False)
                else:
                    # Remove metadata field
                    example_copy = {k: v for k, v in example.items() if k != 'metadata'}
                    json_line = json.dumps(example_copy, ensure_ascii=False)
                    
                f.write(json_line + '\n')
                
        logger.info(f"Saved {len(training_data)} examples to {output_path}")
        
    def validate_jsonl(self, file_path: str) -> Tuple[bool, List[str]]:
        """
        Validate JSONL file format
        
        Args:
            file_path: Path to JSONL file
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        file_path = Path(file_path)
        
        if not file_path.exists():
            return False, ["File does not exist"]
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f, 1):
                    try:
                        data = json.loads(line)
                        
                        # Check required fields based on format
                        if 'instruction' in data:  # Alpaca style
                            if not all(k in data for k in ['instruction', 'input', 'output']):
                                errors.append(f"Line {i}: Missing required fields for Alpaca format")
                                
                        elif 'messages' in data:  # ChatML style
                            if not isinstance(data['messages'], list):
                                errors.append(f"Line {i}: 'messages' must be a list")
                                
                        elif 'text' not in data:  # Raw style
                            errors.append(f"Line {i}: No recognized format (missing 'text', 'instruction', or 'messages')")
                            
                    except json.JSONDecodeError as e:
                        errors.append(f"Line {i}: Invalid JSON - {str(e)}")
                        
        except Exception as e:
            errors.append(f"Error reading file: {str(e)}")
            
        return len(errors) == 0, errors
    
    def get_statistics(self, training_data: List[Dict]) -> Dict:
        """Get statistics about the training data"""
        stats = {
            'total_examples': len(training_data),
            'format_types': {},
            'avg_input_length': 0,
            'avg_output_length': 0,
            'total_tokens_estimate': 0,
        }
        
        input_lengths = []
        output_lengths = []
        
        for example in training_data:
            # Detect format type
            if 'instruction' in example:
                format_type = 'alpaca'
                input_lengths.append(len(example.get('input', '')))
                output_lengths.append(len(example.get('output', '')))
            elif 'messages' in example:
                format_type = 'chatml'
                # Sum all message contents
                total_length = sum(len(msg.get('content', '')) for msg in example['messages'])
                input_lengths.append(total_length // 2)
                output_lengths.append(total_length // 2)
            else:
                format_type = 'raw'
                text_length = len(example.get('text', ''))
                input_lengths.append(text_length)
                
            stats['format_types'][format_type] = stats['format_types'].get(format_type, 0) + 1
            
        if input_lengths:
            stats['avg_input_length'] = sum(input_lengths) / len(input_lengths)
            
        if output_lengths:
            stats['avg_output_length'] = sum(output_lengths) / len(output_lengths)
            
        # Rough token estimate (1 token ≈ 4 characters)
        total_chars = sum(input_lengths) + sum(output_lengths)
        stats['total_tokens_estimate'] = total_chars // 4
        
        return stats