"""
Intent recognition module for the FlipSync chatbot.

This module provides advanced NLP-based intent recognition with entity extraction
and confidence scoring, replacing the previous keyword-matching implementation.
"""

import json
import logging
import random
import re
from typing import Any, Dict, List, Optional, Tuple, Union

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from fs_agt_clean.core.models.chat import MessageEntity, MessageIntent
from fs_agt_clean.core.utils.nlp import extract_entities, preprocess_text

# Configure logging
logger = logging.getLogger(__name__)

# Initialize NLTK resources
try:
    nltk.data.find("tokenizers/punkt")
    nltk.data.find("corpora/stopwords")
    nltk.data.find("corpora/wordnet")
except LookupError:
    logger.warning("NLTK resources not found. Downloading required resources...")
    nltk.download("punkt")
    nltk.download("stopwords")
    nltk.download("wordnet")

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()


class IntentRecognizer:
    """
    Advanced intent recognition service for the FlipSync chatbot.

    This service uses NLP techniques to recognize user intents and extract entities
    from user messages. It supports:
    - Intent classification with confidence scoring
    - Entity extraction
    - Context-aware intent recognition
    - Custom intent patterns
    """

    def __init__(
        self,
        intent_definitions_path: Optional[str] = None,
        entity_definitions_path: Optional[str] = None,
        min_confidence: float = 0.6,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the intent recognizer.

        Args:
            intent_definitions_path: Path to intent definitions JSON file
            entity_definitions_path: Path to entity definitions JSON file
            min_confidence: Minimum confidence threshold for intent recognition
            config: Additional configuration options
        """
        self.config = config or {}
        self.min_confidence = min_confidence

        # Load intent and entity definitions
        self.intent_definitions = self._load_intent_definitions(intent_definitions_path)
        self.entity_definitions = self._load_entity_definitions(entity_definitions_path)

        # Initialize vectorizer for intent matching
        self.vectorizer = TfidfVectorizer(
            tokenizer=self._tokenize_and_lemmatize,
            stop_words=stopwords.words("english"),
            ngram_range=(1, 2),
            max_features=5000,
        )

        # Prepare intent examples for vectorization
        intent_examples = []
        self.intent_labels = []

        for intent_type, intent_def in self.intent_definitions.items():
            for example in intent_def.get("examples", []):
                intent_examples.append(example)
                self.intent_labels.append(intent_type)

        # Fit vectorizer on intent examples
        if intent_examples:
            self.intent_vectors = self.vectorizer.fit_transform(intent_examples)
        else:
            logger.warning(
                "No intent examples found. Intent recognition may not work properly."
            )
            self.intent_vectors = None

        logger.info(
            "Intent recognizer initialized with %d intent types and %d entity types",
            len(self.intent_definitions),
            len(self.entity_definitions),
        )

    def _load_intent_definitions(self, file_path: Optional[str]) -> Dict[str, Any]:
        """
        Load intent definitions from a JSON file.

        Args:
            file_path: Path to intent definitions JSON file

        Returns:
            Dictionary of intent definitions
        """
        if not file_path:
            # Use default intents
            return self._get_default_intent_definitions()

        try:
            with open(file_path, "r") as f:
                intent_definitions = json.load(f)
            logger.info("Loaded intent definitions from %s", file_path)
            return intent_definitions
        except Exception as e:
            logger.error("Error loading intent definitions: %s", str(e))
            return self._get_default_intent_definitions()

    def _load_entity_definitions(self, file_path: Optional[str]) -> Dict[str, Any]:
        """
        Load entity definitions from a JSON file.

        Args:
            file_path: Path to entity definitions JSON file

        Returns:
            Dictionary of entity definitions
        """
        if not file_path:
            # Use default entities
            return self._get_default_entity_definitions()

        try:
            with open(file_path, "r") as f:
                entity_definitions = json.load(f)
            logger.info("Loaded entity definitions from %s", file_path)
            return entity_definitions
        except Exception as e:
            logger.error("Error loading entity definitions: %s", str(e))
            return self._get_default_entity_definitions()

    def _get_default_intent_definitions(self) -> Dict[str, Any]:
        """
        Get default intent definitions.

        Returns:
            Dictionary of default intent definitions
        """
        return {
            "greeting": {
                "examples": [
                    "hello",
                    "hi",
                    "hey",
                    "good morning",
                    "good afternoon",
                    "good evening",
                    "howdy",
                    "what's up",
                    "greetings",
                ],
                "responses": [
                    "Hello! How can I help you today?",
                    "Hi there! What can I do for you?",
                    "Greetings! How may I assist you?",
                ],
            },
            "farewell": {
                "examples": [
                    "goodbye",
                    "bye",
                    "see you",
                    "see you later",
                    "talk to you later",
                    "have a good day",
                    "have a nice day",
                    "until next time",
                ],
                "responses": [
                    "Goodbye! Have a great day!",
                    "Bye! Feel free to come back if you need anything else.",
                    "See you later! Thanks for chatting.",
                ],
            },
            "help": {
                "examples": [
                    "help",
                    "help me",
                    "I need help",
                    "can you help me",
                    "what can you do",
                    "how do you work",
                    "what are your features",
                    "show me what you can do",
                    "instructions",
                    "guide",
                ],
                "responses": [
                    "I can help you with various tasks related to FlipSync. You can ask me about:",
                    "I'm here to assist you with FlipSync. Here are some things I can help with:",
                ],
            },
            "listing": {
                "examples": [
                    "list a product",
                    "create a listing",
                    "how do I list a product",
                    "help me list something",
                    "I want to sell a product",
                    "create a new listing",
                    "add a product to my store",
                ],
                "responses": [
                    "I can help you list a product. What would you like to list?",
                    "Let's create a listing. What product are you selling?",
                ],
            },
            "pricing": {
                "examples": [
                    "price a product",
                    "how much should I charge",
                    "pricing help",
                    "optimize my prices",
                    "price recommendation",
                    "competitive pricing",
                    "what's a good price for",
                    "pricing strategy",
                ],
                "responses": [
                    "I can help you determine the optimal price for your product.",
                    "Let's find the best price for your product.",
                ],
            },
            "inventory": {
                "examples": [
                    "check inventory",
                    "inventory status",
                    "stock levels",
                    "how many items do I have",
                    "update inventory",
                    "manage stock",
                    "inventory management",
                    "low stock alert",
                ],
                "responses": [
                    "I can help you check and manage your inventory.",
                    "Let's take a look at your inventory status.",
                ],
            },
            "order": {
                "examples": [
                    "check orders",
                    "order status",
                    "recent orders",
                    "pending orders",
                    "order history",
                    "track order",
                    "order details",
                    "order management",
                ],
                "responses": [
                    "I can help you check and manage your orders.",
                    "Let's take a look at your order status.",
                ],
            },
        }

    def _get_default_entity_definitions(self) -> Dict[str, Any]:
        """
        Get default entity definitions.

        Returns:
            Dictionary of default entity definitions
        """
        return {
            "product": {
                "patterns": [
                    r"(?i)product[s]?\s+(?:called|named)\s+([a-zA-Z0-9\s]+)",
                    r"(?i)(?:sell|list|selling|listing)\s+(?:a|my|the)?\s*([a-zA-Z0-9\s]+)",
                    r"(?i)([a-zA-Z0-9\s]+)\s+(?:product|item)",
                ]
            },
            "marketplace": {
                "values": [
                    "amazon",
                    "ebay",
                    "etsy",
                    "walmart",
                    "shopify",
                    "facebook marketplace",
                    "mercari",
                    "poshmark",
                ]
            },
            "price": {
                "patterns": [
                    r"(?i)\$(\d+(?:\.\d{1,2})?)",
                    r"(?i)(\d+(?:\.\d{1,2})?)\s+dollars",
                    r"(?i)price[d]?\s+at\s+\$?(\d+(?:\.\d{1,2})?)",
                ]
            },
            "quantity": {
                "patterns": [
                    r"(?i)(\d+)\s+(?:items?|products?|units?|pieces?)",
                    r"(?i)quantity\s+of\s+(\d+)",
                    r"(?i)stock\s+(?:level|count)\s+of\s+(\d+)",
                ]
            },
            "date": {
                "patterns": [
                    r"(?i)(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                    r"(?i)(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{2,4}",
                    r"(?i)(?:next|last)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
                ]
            },
            "order_id": {
                "patterns": [
                    r"(?i)order\s+(?:id|number|#)\s*[:#]?\s*([a-zA-Z0-9\-]+)",
                    r"(?i)order\s+([a-zA-Z0-9\-]{6,})",
                ]
            },
        }

    def _tokenize_and_lemmatize(self, text: str) -> List[str]:
        """
        Tokenize and lemmatize text.

        Args:
            text: Text to process

        Returns:
            List of lemmatized tokens
        """
        tokens = word_tokenize(text.lower())
        return [lemmatizer.lemmatize(token) for token in tokens if token.isalnum()]

    async def recognize_intent(
        self,
        text: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> MessageIntent:
        """
        Recognize intent from user message.

        Args:
            text: UnifiedUser message text
            conversation_history: Optional conversation history
            context: Optional context information

        Returns:
            Recognized intent with confidence score and entities
        """
        # Preprocess text
        preprocessed_text = preprocess_text(text)

        # Extract entities
        entities = await self._extract_entities(text)

        # Check for pattern-based intents first
        pattern_intent = self._check_pattern_intents(preprocessed_text, entities)
        if pattern_intent:
            return pattern_intent

        # Vectorize input text
        if not self.intent_vectors is None:
            text_vector = self.vectorizer.transform([preprocessed_text])

            # Calculate similarity with all intent examples
            similarities = cosine_similarity(text_vector, self.intent_vectors).flatten()

            # Find the most similar intent
            if len(similarities) > 0:
                max_similarity_idx = similarities.argmax()
                max_similarity = similarities[max_similarity_idx]

                if max_similarity >= self.min_confidence:
                    intent_type = self.intent_labels[max_similarity_idx]

                    # Create intent object
                    intent = MessageIntent(
                        intent_type=intent_type,
                        confidence=float(max_similarity),
                        entities=entities,
                    )

                    logger.debug(
                        "Recognized intent: %s (confidence: %.2f)",
                        intent_type,
                        max_similarity,
                    )
                    return intent

        # Apply context-based intent recognition if available
        if context:
            context_intent = self._apply_context(preprocessed_text, entities, context)
            if context_intent:
                return context_intent

        # Default to unknown intent with low confidence
        logger.debug("No intent recognized with sufficient confidence")
        return MessageIntent(
            intent_type="unknown",
            confidence=0.0,
            entities=entities,
        )

    def _check_pattern_intents(
        self,
        text: str,
        entities: List[MessageEntity],
    ) -> Optional[MessageIntent]:
        """
        Check for pattern-based intents.

        Args:
            text: Preprocessed user message
            entities: Extracted entities

        Returns:
            Intent if a pattern matches, None otherwise
        """
        # Check for greeting patterns
        greeting_patterns = [
            r"^(?:hi|hello|hey|greetings|good\s+(?:morning|afternoon|evening))(?:\s|$)",
        ]
        for pattern in greeting_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return MessageIntent(
                    intent_type="greeting",
                    confidence=0.95,
                    entities=entities,
                )

        # Check for farewell patterns
        farewell_patterns = [
            r"^(?:bye|goodbye|see\s+you|farewell|have\s+a\s+(?:good|nice)\s+day)(?:\s|$)",
        ]
        for pattern in farewell_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return MessageIntent(
                    intent_type="farewell",
                    confidence=0.95,
                    entities=entities,
                )

        # Check for help patterns
        help_patterns = [
            r"^(?:help|help\s+me|can\s+you\s+help|what\s+can\s+you\s+do|how\s+do\s+you\s+work)(?:\s|$)",
        ]
        for pattern in help_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return MessageIntent(
                    intent_type="help",
                    confidence=0.9,
                    entities=entities,
                )

        # Check for listing patterns
        listing_patterns = [
            r"(?:list|sell|create\s+listing|add\s+product)(?:\s|$)",
        ]
        for pattern in listing_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return MessageIntent(
                    intent_type="listing",
                    confidence=0.85,
                    entities=entities,
                )

        # Check for pricing patterns
        pricing_patterns = [
            r"(?:price|pricing|how\s+much|cost|charge)(?:\s|$)",
        ]
        for pattern in pricing_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return MessageIntent(
                    intent_type="pricing",
                    confidence=0.85,
                    entities=entities,
                )

        # No pattern matched
        return None

    def _apply_context(
        self,
        text: str,
        entities: List[MessageEntity],
        context: Dict[str, Any],
    ) -> Optional[MessageIntent]:
        """
        Apply context-based intent recognition.

        Args:
            text: Preprocessed user message
            entities: Extracted entities
            context: Context information

        Returns:
            Intent based on context, or None
        """
        # Check for active flows
        active_flow = context.get("active_flow")
        if active_flow:
            flow_step = context.get("flow_step", "")

            if active_flow == "listing":
                # UnifiedUser is in the listing flow
                if flow_step == "product_name" and text:
                    # UnifiedUser is providing product name
                    return MessageIntent(
                        intent_type="listing_product_name",
                        confidence=0.9,
                        entities=entities,
                    )
                elif flow_step == "product_price" and any(
                    e.entity_type == "price" for e in entities
                ):
                    # UnifiedUser is providing product price
                    return MessageIntent(
                        intent_type="listing_product_price",
                        confidence=0.9,
                        entities=entities,
                    )

            elif active_flow == "order":
                # UnifiedUser is in the order flow
                if flow_step == "order_id" and any(
                    e.entity_type == "order_id" for e in entities
                ):
                    # UnifiedUser is providing order ID
                    return MessageIntent(
                        intent_type="order_lookup",
                        confidence=0.9,
                        entities=entities,
                    )

        # Check for recent intents
        recent_intents = context.get("recent_intents", [])
        if recent_intents:
            last_intent = recent_intents[-1]

            if last_intent == "greeting":
                # UnifiedUser just greeted, likely to ask for help
                help_words = ["help", "can", "do", "how", "what", "show"]
                if any(word in text.lower().split() for word in help_words):
                    return MessageIntent(
                        intent_type="help",
                        confidence=0.7,
                        entities=entities,
                    )

            elif last_intent == "listing":
                # UnifiedUser was talking about listing, likely to continue
                return MessageIntent(
                    intent_type="listing_details",
                    confidence=0.7,
                    entities=entities,
                )

        # No context-based intent recognized
        return None

    async def _extract_entities(self, text: str) -> List[MessageEntity]:
        """
        Extract entities from text.

        Args:
            text: UnifiedUser message text

        Returns:
            List of extracted entities
        """
        entities = []

        # Process each entity type
        for entity_type, entity_def in self.entity_definitions.items():
            # Check for values-based entities
            if "values" in entity_def:
                for value in entity_def["values"]:
                    # Look for exact matches (case-insensitive)
                    pattern = r"\b" + re.escape(value) + r"\b"
                    matches = re.finditer(pattern, text, re.IGNORECASE)

                    for match in matches:
                        start_pos = match.start()
                        end_pos = match.end()
                        entity_value = match.group(0)
                        confidence = 0.9  # High confidence for exact matches

                        entities.append(
                            MessageEntity(
                                entity_type=entity_type,
                                value=entity_value,
                                confidence=confidence,
                                start_position=start_pos,
                                end_position=end_pos,
                            )
                        )

            # Check for pattern-based entities
            if "patterns" in entity_def:
                for pattern in entity_def["patterns"]:
                    matches = re.finditer(pattern, text)

                    for match in matches:
                        # Get the first capture group if available, otherwise use the whole match
                        if match.groups():
                            entity_value = match.group(1)
                            # Find the position of the capture group
                            start_pos = text.find(entity_value, match.start())
                            end_pos = start_pos + len(entity_value)
                        else:
                            entity_value = match.group(0)
                            start_pos = match.start()
                            end_pos = match.end()

                        confidence = 0.8  # Good confidence for pattern matches

                        entities.append(
                            MessageEntity(
                                entity_type=entity_type,
                                value=entity_value,
                                confidence=confidence,
                                start_position=start_pos,
                                end_position=end_pos,
                            )
                        )

        return entities

    def add_intent_definition(
        self, intent_type: str, definition: Dict[str, Any]
    ) -> None:
        """
        Add a new intent definition.

        Args:
            intent_type: Type of intent
            definition: Intent definition
        """
        self.intent_definitions[intent_type] = definition

        # Update vectorizer with new examples
        intent_examples = []
        intent_labels = []

        for intent_type, intent_def in self.intent_definitions.items():
            for example in intent_def.get("examples", []):
                intent_examples.append(example)
                intent_labels.append(intent_type)

        # Refit vectorizer
        if intent_examples:
            self.vectorizer = TfidfVectorizer(
                tokenizer=self._tokenize_and_lemmatize,
                stop_words=stopwords.words("english"),
                ngram_range=(1, 2),
                max_features=5000,
            )
            self.intent_vectors = self.vectorizer.fit_transform(intent_examples)
            self.intent_labels = intent_labels

        logger.info("Added intent definition: %s", intent_type)

    def add_entity_definition(
        self, entity_type: str, definition: Dict[str, Any]
    ) -> None:
        """
        Add a new entity definition.

        Args:
            entity_type: Type of entity
            definition: Entity definition
        """
        self.entity_definitions[entity_type] = definition
        logger.info("Added entity definition: %s", entity_type)

    def save_definitions(self, intent_path: str, entity_path: str) -> None:
        """
        Save intent and entity definitions to files.

        Args:
            intent_path: Path to save intent definitions
            entity_path: Path to save entity definitions
        """
        try:
            with open(intent_path, "w") as f:
                json.dump(self.intent_definitions, f, indent=2)
            logger.info("Saved intent definitions to %s", intent_path)

            with open(entity_path, "w") as f:
                json.dump(self.entity_definitions, f, indent=2)
            logger.info("Saved entity definitions to %s", entity_path)
        except Exception as e:
            logger.error("Error saving definitions: %s", str(e))
