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
import re
from difflib import SequenceMatcher
from collections import Counter

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
        self.include_continuation = self.config.get('include_continuation', False)
        self.max_output_similarity = self.config.get('max_output_similarity', 0.75)
        self.max_summary_ratio = self.config.get('max_summary_ratio', 0.35)
        self.max_summary_length = self.config.get('max_summary_length', 200)
        self.min_keyword_count = self.config.get('min_keyword_count', 4)
        self.max_keyword_count = self.config.get('max_keyword_count', 8)
        self.qa_only = self.config.get('qa_only', False)
        self.qa_per_chunk = self.config.get('qa_per_chunk', 2)
        self.qa_templates = self.config.get('qa_templates', [
            "What is the main topic of the text?",
            "What does the text say about {keyword}?",
            "Why is {keyword} important in this context?",
            "How is {keyword} described or applied?",
            "Who is involved or referenced in relation to {keyword}?"
        ])
        
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

        self._stopwords = {
            "the", "and", "or", "of", "to", "in", "a", "an", "is", "are", "was", "were",
            "for", "on", "with", "as", "by", "at", "from", "that", "this", "it", "be",
            "can", "may", "not", "we", "they", "their", "our", "you", "your", "its",
        }
        
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
            
            # Process the text or provided chunks
            text = doc_data.get('text', '')
            chunks = doc_data.get('chunks')
            if not text and not chunks:
                continue
                
            # Create training examples from the text
            if output_format == 'alpaca':
                examples = self._format_alpaca_style(text, doc_metadata, chunks=chunks)
            elif output_format == 'chatML':
                examples = self._format_chatml_style(text, doc_metadata, chunks=chunks)
            else:  # raw
                examples = self._format_raw_style(text, doc_metadata, chunks=chunks)
                
            training_data.extend(examples)
            
        # Add data augmentation if configured
        if self.config.get('augment_data', False):
            training_data = self._augment_training_data(training_data)
            
        # Shuffle if configured
        if self.config.get('shuffle', True):
            random.shuffle(training_data)
            
        logger.info(f"Created {len(training_data)} training examples from {len(extracted_data)} documents")
        
        return training_data
    
    def _format_alpaca_style(self, text: str, metadata: Dict, chunks: Optional[List[str]] = None) -> List[Dict]:
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
        chunks = chunks or self._create_text_chunks(text)
        
        for i, chunk in enumerate(chunks):
            qa_pairs = self._generate_qa_pairs(chunk, limit=self.qa_per_chunk)
            for question, answer in qa_pairs:
                answer = self._ensure_non_redundant_output(chunk, answer)
                example = {
                    "instruction": question,
                    "input": chunk,
                    "output": answer,
                    "metadata": {**metadata, "chunk_index": i, "type": "qa"}
                }
                examples.append(example)

            if not self.qa_only:
                # Summary
                summary = self._generate_summary(chunk)
                summary = self._ensure_non_redundant_output(chunk, summary)
                example = {
                    "instruction": "Summarize the following text concisely.",
                    "input": chunk,
                    "output": summary,
                    "metadata": {**metadata, "chunk_index": i, "type": "summary"}
                }
                examples.append(example)

                # Key points extraction
                key_points = self._generate_key_points(chunk)
                key_points = self._ensure_non_redundant_output(chunk, key_points)
                example = {
                    "instruction": "List the key points from the following text.",
                    "input": chunk,
                    "output": key_points,
                    "metadata": {**metadata, "chunk_index": i, "type": "key_points"}
                }
                examples.append(example)

            # 3. Continuation (optional)
            if not self.qa_only and self.include_continuation and len(chunk) > 200:
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
                    domain_output = self._generate_domain_response(chunk, prompt_template)
                    domain_output = self._ensure_non_redundant_output(chunk, domain_output)
                    example = {
                        "instruction": prompt_template.get("instruction", "Analyze the following content."),
                        "input": chunk,
                        "output": domain_output,
                        "metadata": {**metadata, "chunk_index": i, "type": "domain"}
                    }
                    examples.append(example)
                    
        return examples
    
    def _format_chatml_style(self, text: str, metadata: Dict, chunks: Optional[List[str]] = None) -> List[Dict]:
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
        chunks = chunks or self._create_text_chunks(text)
        
        system_prompt = (
            "You are an AI assistant with expertise in the domain covered by this document. "
            "Provide accurate, helpful responses based on the content."
        )
        
        for i, chunk in enumerate(chunks):
            # Create conversation-style examples
            explanation = self._generate_explanation(chunk)
            explanation = self._ensure_non_redundant_output(chunk, explanation)
            example = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Explain the following content:\n\n{chunk[:500]}"},
                    {"role": "assistant", "content": explanation}
                ],
                "metadata": {**metadata, "chunk_index": i}
            }
            examples.append(example)
            
        return examples
    
    def _format_raw_style(self, text: str, metadata: Dict, chunks: Optional[List[str]] = None) -> List[Dict]:
        """
        Format text in raw completion style
        
        Format:
        {
            "text": "...",
            "metadata": {...}
        }
        """
        examples = []
        chunks = chunks or self._create_text_chunks(text)
        
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
    
    def _generate_summary(self, text: str) -> str:
        """Generate a concise summary using simple heuristics."""
        sentences = self._split_sentences(text)
        if not sentences:
            return self._generate_keyword_summary(text)

        max_length = min(self.max_summary_length, max(50, int(len(text) * self.max_summary_ratio)))
        summary_sentences = []
        current_length = 0
        for sentence in sentences:
            if current_length + len(sentence) > max_length:
                break
            summary_sentences.append(sentence)
            current_length += len(sentence)
            if len(summary_sentences) >= 3:
                break

        summary = '. '.join(summary_sentences).strip()
        if summary and not summary.endswith(('.', '!', '?')):
            summary += '.'

        if not summary:
            summary = self._generate_keyword_summary(text)

        return summary
    
    def _generate_explanation(self, text: str) -> str:
        """Generate a compact explanation without copying full sentences."""
        keywords = self._extract_keywords(text, limit=max(self.min_keyword_count, 5))
        if keywords:
            return "This text covers: " + ", ".join(keywords) + "."
        return "This text contains domain-specific information."
    
    def _generate_domain_response(self, text: str, prompt_template: Dict) -> str:
        """Generate domain-specific response based on template"""
        # This is a placeholder - in practice, you might want to:
        # 1. Use a small model to generate responses
        # 2. Extract key information based on domain rules
        # 3. Use template-based generation
        
        response_type = prompt_template.get("response_type", "extraction")
        
        if response_type == "extraction":
            # Extract key terms and concepts
            key_terms = self._extract_keywords(text, limit=self.max_keyword_count)
            if key_terms:
                return f"Key concepts: {', '.join(key_terms)}"
            return "Key concepts: (insufficient signal)"
            
        elif response_type == "analysis":
            return self._generate_explanation(text)
            
        else:
            return self._generate_summary(text)

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences for summarization."""
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s.strip() for s in sentences if s.strip()]

    def _extract_keywords(self, text: str, limit: int = 8) -> List[str]:
        """Extract simple keyword list from text."""
        tokens = re.findall(r"[A-Za-z0-9']+", text.lower())
        filtered = [t for t in tokens if t not in self._stopwords and len(t) > 2]
        if not filtered:
            return []
        counts = Counter(filtered)
        keywords = [word for word, _ in counts.most_common(limit)]
        return keywords

    def _generate_keyword_summary(self, text: str) -> str:
        """Generate a short key-topic summary."""
        keywords = self._extract_keywords(text, limit=self.max_keyword_count)
        if not keywords:
            return "Key topics unavailable."
        return "Key topics: " + ", ".join(keywords) + "."

    def _generate_key_points(self, text: str) -> str:
        """Generate key points from text without copying sentences."""
        keywords = self._extract_keywords(text, limit=self.max_keyword_count)
        if not keywords:
            return "Key points unavailable."
        return "Key points: " + "; ".join(keywords[: self.max_keyword_count]) + "."

    def _generate_qa_pairs(self, text: str, limit: int = 2) -> List[Tuple[str, str]]:
        """Generate QA pairs from a text chunk using templates."""
        qa_pairs = []
        keywords = self._extract_keywords(text, limit=max(self.min_keyword_count, limit + 2))
        summary = self._generate_summary(text)

        templates = list(self.qa_templates) if self.qa_templates else []
        if not templates:
            templates = ["What is the main topic of the text?"]

        for template in templates:
            if len(qa_pairs) >= limit:
                break
            if "{keyword}" in template:
                if not keywords:
                    continue
                for kw in keywords:
                    if len(qa_pairs) >= limit:
                        break
                    question = template.format(keyword=kw)
                    answer = self._generate_key_points(text)
                    qa_pairs.append((question, answer))
            else:
                question = template
                answer = summary
                qa_pairs.append((question, answer))

        return qa_pairs[:max(1, limit)]

    def _ensure_non_redundant_output(self, input_text: str, output_text: str) -> str:
        """Avoid outputs that closely mirror the input."""
        if not input_text or not output_text:
            return output_text

        normalized_input = self._normalize_for_similarity(input_text)
        normalized_output = self._normalize_for_similarity(output_text)
        if not normalized_output:
            return output_text

        similarity = SequenceMatcher(None, normalized_input, normalized_output).ratio()
        if similarity >= self.max_output_similarity or normalized_output in normalized_input:
            return self._generate_keyword_summary(input_text)
        return output_text

    def _normalize_for_similarity(self, text: str) -> str:
        """Normalize text for similarity checks."""
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]+", " ", text)
        return " ".join(text.split())
    
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
