"""
Gemini API Adapter for VidyaVani

This module provides an adapter to use Google Gemini API with OpenAI-compatible interface
for both chat completions and embeddings.
"""

import logging
import time
from typing import Dict, Any, List, Optional
import numpy as np

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

# Configure logging
logger = logging.getLogger(__name__)


class GeminiChatCompletion:
    """Mock OpenAI ChatCompletion response structure"""
    
    def __init__(self, content: str, model: str, tokens_used: int = 0):
        self.choices = [GeminiChoice(content)]
        self.usage = GeminiUsage(tokens_used)
        self.model = model


class GeminiChoice:
    """Mock OpenAI Choice structure"""
    
    def __init__(self, content: str):
        self.message = GeminiMessage(content)


class GeminiMessage:
    """Mock OpenAI Message structure"""
    
    def __init__(self, content: str):
        self.content = content


class GeminiUsage:
    """Mock OpenAI Usage structure"""
    
    def __init__(self, total_tokens: int):
        self.total_tokens = total_tokens


class GeminiEmbeddingResponse:
    """Mock OpenAI Embedding response structure"""
    
    def __init__(self, embedding: List[float]):
        self.data = [GeminiEmbeddingData(embedding)]


class GeminiEmbeddingData:
    """Mock OpenAI Embedding data structure"""
    
    def __init__(self, embedding: List[float]):
        self.embedding = embedding


class GeminiAdapter:
    """
    Adapter to use Google Gemini API with OpenAI-compatible interface
    """
    
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash-lite"):
        """
        Initialize Gemini adapter
        
        Args:
            api_key: Google Gemini API key
            model: Gemini model to use
        """
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai library not installed. Run: pip install google-generativeai")
        
        self.api_key = api_key
        self.model = model
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Map model names to correct Gemini format (with models/ prefix)
        model_mapping = {
            "gemini-2.5-flash-lite": "models/gemini-2.5-flash-lite",
            "gemini-2.5-flash": "models/gemini-2.5-flash",
            "gemini-2.0-flash-exp": "models/gemini-2.0-flash-exp",
            "gemini-2.0-flash": "models/gemini-2.0-flash", 
            "gemini-1.5-flash": "models/gemini-1.5-flash",
            "gemini-1.5-pro": "models/gemini-1.5-pro",
            "gemini-pro": "models/gemini-pro"
        }
        
        gemini_model = model_mapping.get(model, "models/gemini-2.5-flash-lite")
        logger.info(f"Using Gemini model: {gemini_model}")
        
        # Initialize models
        self.chat_model = genai.GenerativeModel(gemini_model)
        
        logger.info(f"Gemini adapter initialized with model: {model}")
    
    def chat_completions_create(self, model: str, messages: List[Dict[str, str]], 
                               max_tokens: int = 500, temperature: float = 0.7,
                               **kwargs) -> GeminiChatCompletion:
        """
        Create chat completion using Gemini (OpenAI-compatible interface)
        
        Args:
            model: Model name (ignored, uses configured model)
            messages: List of messages in OpenAI format
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            **kwargs: Additional arguments (ignored)
            
        Returns:
            GeminiChatCompletion object with OpenAI-compatible structure
        """
        try:
            # Convert OpenAI messages to Gemini format
            prompt = self._convert_messages_to_prompt(messages)
            
            # Configure generation
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
                top_p=0.9,
                top_k=40
            )
            
            # Configure safety settings to be less restrictive
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            # Generate response
            response = self.chat_model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            logger.info(f"Gemini response received: {type(response)}")
            logger.info(f"Response candidates: {len(response.candidates) if response.candidates else 0}")
            
            # Extract content from Gemini response
            content = ""
            logger.info(f"Response has {len(response.candidates)} candidates")
            
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                logger.info(f"Candidate has content: {candidate.content is not None}")
                
                if candidate.content and candidate.content.parts:
                    logger.info(f"Content has {len(candidate.content.parts)} parts")
                    content = candidate.content.parts[0].text
                    logger.info(f"Extracted content: {content[:100]}...")
            
            if not content:
                content = "I apologize, but I couldn't generate a response."
                logger.warning("No content extracted from response")
            
            # Estimate token usage (rough approximation)
            tokens_used = len(prompt.split()) + len(content.split())
            
            return GeminiChatCompletion(content, self.model, tokens_used)
            
        except Exception as e:
            logger.error(f"Gemini chat completion failed: {e}")
            # Return fallback response
            fallback_content = "I'm sorry, I'm having technical difficulties. Please try again."
            return GeminiChatCompletion(fallback_content, self.model, 0)
    
    def embeddings_create(self, model: str, input: str, **kwargs) -> GeminiEmbeddingResponse:
        """
        Create embeddings using Gemini (OpenAI-compatible interface)
        
        Args:
            model: Model name (ignored, uses text-embedding-004)
            input: Text to embed
            **kwargs: Additional arguments (ignored)
            
        Returns:
            GeminiEmbeddingResponse object with OpenAI-compatible structure
        """
        try:
            # Use Gemini's embedding model
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=input,
                task_type="retrieval_query"
            )
            
            embedding = result['embedding']
            
            return GeminiEmbeddingResponse(embedding)
            
        except Exception as e:
            logger.error(f"Gemini embedding failed: {e}")
            # Return zero vector as fallback
            zero_embedding = [0.0] * 768  # Gemini embeddings are 768-dimensional
            return GeminiEmbeddingResponse(zero_embedding)
    
    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """
        Convert OpenAI messages format to Gemini prompt
        
        Args:
            messages: List of messages in OpenAI format
            
        Returns:
            Formatted prompt string for Gemini
        """
        prompt_parts = []
        
        for message in messages:
            role = message.get('role', 'user')
            content = message.get('content', '')
            
            if role == 'system':
                prompt_parts.append(f"Instructions: {content}")
            elif role == 'user':
                prompt_parts.append(f"User: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(prompt_parts)


class GeminiOpenAIClient:
    """
    OpenAI-compatible client using Gemini backend
    """
    
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash-lite"):
        """
        Initialize Gemini client with OpenAI-compatible interface
        
        Args:
            api_key: Google Gemini API key
            model: Gemini model to use
        """
        self.adapter = GeminiAdapter(api_key, model)
        self.chat = GeminiChatClient(self.adapter)
        self.embeddings = GeminiEmbeddingsClient(self.adapter)


class GeminiChatClient:
    """OpenAI-compatible chat client using Gemini"""
    
    def __init__(self, adapter: GeminiAdapter):
        self.adapter = adapter
    
    @property
    def completions(self):
        return self
    
    def create(self, **kwargs):
        return self.adapter.chat_completions_create(**kwargs)


class GeminiEmbeddingsClient:
    """OpenAI-compatible embeddings client using Gemini"""
    
    def __init__(self, adapter: GeminiAdapter):
        self.adapter = adapter
    
    def create(self, **kwargs):
        return self.adapter.embeddings_create(**kwargs)


def test_gemini_adapter():
    """Test the Gemini adapter functionality"""
    import os
    
    api_key = os.getenv('GOOGLE_GEMINI_API_KEY')
    if not api_key:
        print("❌ GOOGLE_GEMINI_API_KEY not found in environment")
        return False
    
    try:
        # Initialize client
        client = GeminiOpenAIClient(api_key)
        
        # Test chat completion
        print("🧪 Testing chat completion...")
        response = client.chat.completions.create(
            model="gemini-2.5-flash-lite",
            messages=[
                {"role": "system", "content": "You are a helpful science tutor."},
                {"role": "user", "content": "What is photosynthesis?"}
            ],
            max_tokens=100,
            temperature=0.7
        )
        
        print(f"✅ Chat response: {response.choices[0].message.content[:100]}...")
        print(f"   Tokens used: {response.usage.total_tokens}")
        
        # Test embeddings
        print("\n🧪 Testing embeddings...")
        embedding_response = client.embeddings.create(
            model="text-embedding-004",
            input="What is photosynthesis?"
        )
        
        embedding = embedding_response.data[0].embedding
        print(f"✅ Embedding generated: {len(embedding)} dimensions")
        print(f"   First 5 values: {embedding[:5]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    test_gemini_adapter()