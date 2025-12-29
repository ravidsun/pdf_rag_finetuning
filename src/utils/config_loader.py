"""
Configuration loader for QA Generator
Supports YAML config files and .env files
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ModelConfig:
    """Model configuration"""
    name: str = "qwen2.5:14b"
    base_url: str = "http://localhost:11434"
    temperature: float = 0.3
    max_tokens: int = 4096


@dataclass
class ProcessingConfig:
    """Processing configuration"""
    qa_multiplier: float = 2.0
    target_qa_count: Optional[int] = None
    chunk_size: int = 4000
    chunk_overlap: int = 400
    rate_limit_delay: float = 0.5


@dataclass
class PathsConfig:
    """Paths configuration"""
    input_folder: str = ""
    output_folder: str = "data/output"
    log_file: str = "qa_generation.log"


@dataclass
class ResumeConfig:
    """Resume/checkpoint configuration"""
    enabled: bool = True
    checkpoint_file: str = "checkpoint.json"
    progress_file: str = "progress.json"


@dataclass
class DomainConfig:
    """Domain-specific configuration"""
    name: str = "General"
    qa_types: list = field(default_factory=lambda: [
        "definition", "concept", "rule", "procedure",
        "comparison", "example", "interpretation", "checklist"
    ])
    special_instructions: str = ""


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(levelname)s - %(message)s"
    file_enabled: bool = True
    console_enabled: bool = True


@dataclass
class Config:
    """Main configuration object"""
    model: ModelConfig = field(default_factory=ModelConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)
    resume: ResumeConfig = field(default_factory=ResumeConfig)
    domain: DomainConfig = field(default_factory=DomainConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    system_prompt: str = ""


class ConfigLoader:
    """Load configuration from YAML and/or .env files"""

    @staticmethod
    def load_from_yaml(yaml_path: str) -> Config:
        """Load configuration from YAML file"""
        config_path = Path(yaml_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {yaml_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        config = Config()

        # Load model config
        if 'model' in data:
            model_data = data['model']
            config.model = ModelConfig(
                name=model_data.get('name', config.model.name),
                base_url=model_data.get('base_url', config.model.base_url),
                temperature=model_data.get('temperature', config.model.temperature),
                max_tokens=model_data.get('max_tokens', config.model.max_tokens)
            )

        # Load processing config
        if 'processing' in data:
            proc_data = data['processing']
            config.processing = ProcessingConfig(
                qa_multiplier=proc_data.get('qa_multiplier', config.processing.qa_multiplier),
                target_qa_count=proc_data.get('target_qa_count'),
                chunk_size=proc_data.get('chunk_size', config.processing.chunk_size),
                chunk_overlap=proc_data.get('chunk_overlap', config.processing.chunk_overlap),
                rate_limit_delay=proc_data.get('rate_limit_delay', config.processing.rate_limit_delay)
            )

        # Load paths config
        if 'paths' in data:
            paths_data = data['paths']
            config.paths = PathsConfig(
                input_folder=paths_data.get('input_folder', ''),
                output_folder=paths_data.get('output_folder', config.paths.output_folder),
                log_file=paths_data.get('log_file', config.paths.log_file)
            )

        # Load resume config
        if 'resume' in data:
            resume_data = data['resume']
            config.resume = ResumeConfig(
                enabled=resume_data.get('enabled', config.resume.enabled),
                checkpoint_file=resume_data.get('checkpoint_file', config.resume.checkpoint_file),
                progress_file=resume_data.get('progress_file', config.resume.progress_file)
            )

        # Load domain config
        if 'domain' in data:
            domain_data = data['domain']
            config.domain = DomainConfig(
                name=domain_data.get('name', config.domain.name),
                qa_types=domain_data.get('qa_types', config.domain.qa_types),
                special_instructions=domain_data.get('special_instructions', '')
            )

        # Load logging config
        if 'logging' in data:
            log_data = data['logging']
            config.logging = LoggingConfig(
                level=log_data.get('level', config.logging.level),
                format=log_data.get('format', config.logging.format),
                file_enabled=log_data.get('file_enabled', config.logging.file_enabled),
                console_enabled=log_data.get('console_enabled', config.logging.console_enabled)
            )

        # Load system prompt
        if 'system_prompt' in data:
            config.system_prompt = data['system_prompt']

        return config

    @staticmethod
    def load_from_env(env_path: str = '.env') -> Config:
        """Load configuration from .env file"""
        from dotenv import load_dotenv

        load_dotenv(env_path)

        config = Config()

        # Load model config from env
        config.model = ModelConfig(
            name=os.getenv('MODEL_NAME', config.model.name),
            base_url=os.getenv('OLLAMA_BASE_URL', config.model.base_url),
            temperature=float(os.getenv('MODEL_TEMPERATURE', config.model.temperature)),
            max_tokens=int(os.getenv('MODEL_MAX_TOKENS', config.model.max_tokens))
        )

        # Load processing config from env
        config.processing = ProcessingConfig(
            qa_multiplier=float(os.getenv('QA_MULTIPLIER', config.processing.qa_multiplier)),
            target_qa_count=int(os.getenv('TARGET_QA_COUNT')) if os.getenv('TARGET_QA_COUNT') else None,
            chunk_size=int(os.getenv('CHUNK_SIZE', config.processing.chunk_size)),
            chunk_overlap=int(os.getenv('CHUNK_OVERLAP', config.processing.chunk_overlap)),
            rate_limit_delay=float(os.getenv('RATE_LIMIT_DELAY', config.processing.rate_limit_delay))
        )

        # Load paths config from env
        config.paths = PathsConfig(
            input_folder=os.getenv('INPUT_FOLDER', ''),
            output_folder=os.getenv('OUTPUT_FOLDER', config.paths.output_folder),
            log_file=os.getenv('LOG_FILE', config.paths.log_file)
        )

        # Load resume config from env
        config.resume = ResumeConfig(
            enabled=os.getenv('RESUME_ENABLED', 'true').lower() == 'true'
        )

        # Load domain config from env
        config.domain = DomainConfig(
            name=os.getenv('DOMAIN_NAME', config.domain.name),
            special_instructions=os.getenv('DOMAIN_SPECIAL_INSTRUCTIONS', '')
        )

        return config

    @staticmethod
    def load(yaml_path: Optional[str] = None, env_path: Optional[str] = None) -> Config:
        """
        Load configuration from YAML and/or .env files
        YAML takes precedence over .env
        """
        config = Config()

        # Load from .env first (if exists)
        if env_path and Path(env_path).exists():
            try:
                config = ConfigLoader.load_from_env(env_path)
            except Exception as e:
                print(f"Warning: Failed to load .env: {e}")

        # Load from YAML (overrides .env)
        if yaml_path and Path(yaml_path).exists():
            try:
                yaml_config = ConfigLoader.load_from_yaml(yaml_path)
                # Merge with env config
                config = yaml_config
            except Exception as e:
                print(f"Warning: Failed to load YAML config: {e}")

        return config


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Convenience function to load configuration

    Priority:
    1. Specified config_path (YAML)
    2. config.yaml in current directory
    3. .env file in current directory
    4. Default configuration
    """
    if config_path:
        return ConfigLoader.load_from_yaml(config_path)

    # Try config.yaml
    if Path('config.yaml').exists():
        return ConfigLoader.load(yaml_path='config.yaml', env_path='.env')

    # Try .env
    if Path('.env').exists():
        return ConfigLoader.load_from_env('.env')

    # Return default
    return Config()
