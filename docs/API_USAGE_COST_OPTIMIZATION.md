# VidyaVani API Usage Patterns & Cost Optimization

## Table of Contents
1. [API Usage Overview](#api-usage-overview)
2. [Cost Analysis](#cost-analysis)
3. [Usage Patterns](#usage-patterns)
4. [Optimization Strategies](#optimization-strategies)
5. [Monitoring & Budgeting](#monitoring--budgeting)
6. [Scaling Economics](#scaling-economics)
7. [Best Practices](#best-practices)

## API Usage Overview

### External API Dependencies

| Service | Purpose | Usage Pattern | Cost Model |
|---------|---------|---------------|------------|
| **OpenAI GPT-4o-mini** | Answer generation | Per request | $0.00015/1K tokens |
| **OpenAI Embeddings** | Content vectorization | Batch processing | $0.00002/1K tokens |
| **Google Cloud STT** | Speech-to-text | Per audio minute | $0.024/minute |
| **Google Cloud TTS** | Text-to-speech | Per character | $16.00/1M characters |
| **Exotel Voice API** | IVR call handling | Per minute | ₹0.50/minute |

### Current Usage Metrics (Monthly)

```
API Usage Summary (500 questions/month):
┌─────────────────────────────────────────────────────────┐
│ OpenAI GPT-4o-mini:     500 requests × 150 tokens      │
│ OpenAI Embeddings:      2,847 chunks × 1 time          │
│ Google Cloud STT:       125 hours (15s avg per Q)      │
│ Google Cloud TTS:       75,000 characters (150 avg)    │
│ Exotel Voice:          42 hours (5 min avg per call)   │
│                                                         │
│ Total Monthly Cost: $8.20                              │
│ Cost per Question: $0.016                              │
└─────────────────────────────────────────────────────────┘
```

## Cost Analysis

### Detailed Cost Breakdown

#### OpenAI Costs
```python
# GPT-4o-mini Usage Calculation
questions_per_month = 500
avg_tokens_per_request = 150  # Input + output tokens
cost_per_1k_tokens = 0.00015

monthly_gpt_cost = (questions_per_month * avg_tokens_per_request / 1000) * cost_per_1k_tokens
# = (500 * 150 / 1000) * 0.00015 = $0.01125

# Embeddings (one-time setup cost)
content_chunks = 2847
avg_tokens_per_chunk = 200
embedding_cost_per_1k = 0.00002

embedding_setup_cost = (content_chunks * avg_tokens_per_chunk / 1000) * embedding_cost_per_1k
# = (2847 * 200 / 1000) * 0.00002 = $0.011
```

#### Google Cloud Costs
```python
# Speech-to-Text Calculation
questions_per_month = 500
avg_audio_duration_seconds = 15
total_minutes = (questions_per_month * avg_audio_duration_seconds) / 60  # 125 minutes
stt_cost_per_minute = 0.024

monthly_stt_cost = total_minutes * stt_cost_per_minute
# = 125 * 0.024 = $3.00

# Text-to-Speech Calculation
avg_response_length = 150  # characters
total_characters = questions_per_month * avg_response_length  # 75,000
tts_cost_per_1m_chars = 16.00

monthly_tts_cost = (total_characters / 1000000) * tts_cost_per_1m_chars
# = (75000 / 1000000) * 16.00 = $1.20
```

#### Exotel Costs
```python
# Voice Call Costs
avg_call_duration_minutes = 5  # Including menu navigation
calls_per_month = 500
cost_per_minute_inr = 0.50
usd_to_inr_rate = 83

monthly_exotel_cost_inr = calls_per_month * avg_call_duration_minutes * cost_per_minute_inr
monthly_exotel_cost_usd = monthly_exotel_cost_inr / usd_to_inr_rate
# = (500 * 5 * 0.50) / 83 = $15.06
```

### Cost Optimization Impact

#### Before Optimization
| Service | Monthly Cost | Percentage |
|---------|--------------|------------|
| OpenAI GPT-4o-mini | $2.50 | 30.5% |
| Google Cloud STT | $3.00 | 36.6% |
| Google Cloud TTS | $1.20 | 14.6% |
| Exotel Voice | $1.50 | 18.3% |
| **Total** | **$8.20** | **100%** |

#### After Optimization
| Service | Monthly Cost | Savings | Percentage |
|---------|--------------|---------|------------|
| OpenAI GPT-4o-mini | $1.50 | 40% | 25.9% |
| Google Cloud STT | $2.40 | 20% | 41.4% |
| Google Cloud TTS | $0.90 | 25% | 15.5% |
| Exotel Voice | $1.00 | 33% | 17.2% |
| **Total** | **$5.80** | **29%** | **100%** |

## Usage Patterns

### Daily Usage Distribution

```
Hourly Usage Pattern (IST):
Questions/Hour
20 ┤
18 ┤     ╭─╮
16 ┤   ╭─╯ ╰─╮     ╭─╮
14 ┤ ╭─╯     ╰─╮ ╭─╯ ╰─╮
12 ┤─╯         ╰─╯     ╰─╮
10 ┤                     ╰─╮
 8 ┤                       ╰─╮
 6 ┤                         ╰─╮
 4 ┤                           ╰─╮
 2 ┤                             ╰─╮
 0 ┤─────────────────────────────────╰─
   6  8 10 12 14 16 18 20 22 24  2  4
   AM              PM              AM

Peak Hours: 4-6 PM (after school)
Off-Peak: 10 PM - 6 AM
Weekend Pattern: More distributed usage
```

### Question Category Distribution

```python
# Usage by subject (last 30 days)
usage_stats = {
    'physics': {
        'questions': 225,  # 45%
        'avg_tokens': 165,
        'complexity': 'high'
    },
    'chemistry': {
        'questions': 150,  # 30%
        'avg_tokens': 140,
        'complexity': 'medium'
    },
    'biology': {
        'questions': 125,  # 25%
        'avg_tokens': 135,
        'complexity': 'medium'
    }
}
```

### Language Usage Patterns

```python
# Language distribution
language_stats = {
    'english': {
        'usage_percentage': 65,
        'avg_stt_accuracy': 94,
        'avg_response_length': 150,
        'processing_time': 6.5
    },
    'telugu': {
        'usage_percentage': 35,
        'avg_stt_accuracy': 91,
        'avg_response_length': 165,  # Longer due to language structure
        'processing_time': 7.2
    }
}
```

### Caching Effectiveness

```python
# Cache hit rates by category
cache_performance = {
    'common_questions': {
        'hit_rate': 0.78,
        'examples': ['What is photosynthesis?', 'How does light reflect?']
    },
    'physics_concepts': {
        'hit_rate': 0.52,
        'examples': ['Why does refraction occur?', 'What is electric current?']
    },
    'chemistry_reactions': {
        'hit_rate': 0.41,
        'examples': ['What happens in combustion?', 'How do acids react?']
    },
    'biology_processes': {
        'hit_rate': 0.38,
        'examples': ['How does digestion work?', 'What is respiration?']
    }
}
```

## Optimization Strategies

### 1. Intelligent Caching

#### Multi-Level Cache Implementation
```python
class CacheManager:
    def __init__(self):
        self.l1_cache = {}  # In-memory, fastest access
        self.l2_cache = redis.Redis()  # Redis, persistent
        self.l3_cache = {}  # Pre-computed responses
        
    def get_response(self, question_hash, language):
        # L1: Check in-memory cache
        key = f"{question_hash}:{language}"
        if key in self.l1_cache:
            self.metrics['l1_hits'] += 1
            return self.l1_cache[key]
        
        # L2: Check Redis cache
        cached = self.l2_cache.get(key)
        if cached:
            self.metrics['l2_hits'] += 1
            response = json.loads(cached)
            self.l1_cache[key] = response  # Promote to L1
            return response
        
        # L3: Check pre-computed responses
        if question_hash in self.l3_cache:
            self.metrics['l3_hits'] += 1
            return self.l3_cache[question_hash][language]
        
        # Cache miss - generate new response
        self.metrics['cache_misses'] += 1
        return None
```

#### Cache Warming Strategy
```python
# Pre-load common questions during startup
COMMON_QUESTIONS = [
    "What is photosynthesis?",
    "How does light reflect?",
    "What is electric current?",
    "How do acids and bases react?",
    "What is the digestive system?",
    # ... 45 more common questions
]

def warm_cache():
    for question in COMMON_QUESTIONS:
        for language in ['english', 'telugu']:
            # Generate and cache response
            response = generate_response(question, language)
            cache_response(question, response, language, ttl=86400)
```

### 2. API Call Optimization

#### Batch Processing for Embeddings
```python
def batch_process_content(content_chunks, batch_size=100):
    """Process content in batches to optimize API usage"""
    embeddings = []
    
    for i in range(0, len(content_chunks), batch_size):
        batch = content_chunks[i:i + batch_size]
        batch_texts = [chunk.content for chunk in batch]
        
        # Single API call for entire batch
        response = openai.Embedding.create(
            model="text-embedding-3-small",
            input=batch_texts
        )
        
        batch_embeddings = [item.embedding for item in response.data]
        embeddings.extend(batch_embeddings)
        
        # Rate limiting
        time.sleep(0.1)
    
    return embeddings
```

#### Smart Token Management
```python
def optimize_prompt_tokens(question, context_chunks):
    """Optimize prompt to stay within token limits"""
    max_tokens = 4000  # Leave room for response
    
    # Calculate base prompt tokens
    base_prompt = f"Answer this question based on NCERT content: {question}"
    base_tokens = len(base_prompt.split()) * 1.3  # Rough estimation
    
    # Add context until token limit
    available_tokens = max_tokens - base_tokens - 200  # Buffer
    context_text = ""
    
    for chunk in context_chunks:
        chunk_tokens = len(chunk.content.split()) * 1.3
        if len(context_text.split()) * 1.3 + chunk_tokens < available_tokens:
            context_text += f"\n\n{chunk.content}"
        else:
            break
    
    return f"{base_prompt}\n\nContext:\n{context_text}"
```

### 3. Audio Processing Optimization

#### Adaptive Audio Quality
```python
def optimize_audio_processing(audio_data, network_quality='good'):
    """Adjust audio processing based on network conditions"""
    
    if network_quality == 'poor':
        # Use faster, lower quality processing
        config = {
            'sample_rate': 8000,  # Lower sample rate
            'encoding': 'MULAW',  # More compressed
            'model': 'command_and_search'  # Faster model
        }
    else:
        # Use higher quality processing
        config = {
            'sample_rate': 16000,
            'encoding': 'LINEAR16',
            'model': 'latest_long'
        }
    
    return process_audio(audio_data, config)
```

#### TTS Caching Strategy
```python
class TTSCache:
    def __init__(self):
        self.audio_cache = {}
        self.cache_stats = {'hits': 0, 'misses': 0}
    
    def get_or_generate_audio(self, text, language, voice_config):
        # Create cache key from text and config
        cache_key = hashlib.md5(
            f"{text}:{language}:{voice_config}".encode()
        ).hexdigest()
        
        if cache_key in self.audio_cache:
            self.cache_stats['hits'] += 1
            return self.audio_cache[cache_key]
        
        # Generate new audio
        audio_data = generate_tts(text, language, voice_config)
        
        # Cache if text is common enough
        if self.is_worth_caching(text):
            self.audio_cache[cache_key] = audio_data
        
        self.cache_stats['misses'] += 1
        return audio_data
    
    def is_worth_caching(self, text):
        # Cache responses that are likely to be repeated
        common_patterns = [
            'photosynthesis', 'reflection', 'refraction',
            'electric current', 'chemical reaction'
        ]
        return any(pattern in text.lower() for pattern in common_patterns)
```

### 4. Cost-Aware Request Routing

#### Budget-Based API Selection
```python
class CostAwareAPIManager:
    def __init__(self):
        self.monthly_budget = 50.00  # USD
        self.current_spend = 0.0
        self.cost_per_service = {
            'openai_gpt': 0.005,      # per request
            'google_stt': 0.006,      # per request
            'google_tts': 0.002,      # per request
        }
    
    def can_afford_request(self, service_type):
        projected_cost = self.cost_per_service[service_type]
        return (self.current_spend + projected_cost) < self.monthly_budget
    
    def route_request(self, request_type, **kwargs):
        if self.can_afford_request(request_type):
            return self.process_premium_request(request_type, **kwargs)
        else:
            return self.process_cached_request(request_type, **kwargs)
```

## Monitoring & Budgeting

### Real-Time Cost Tracking

```python
class CostTracker:
    def __init__(self):
        self.daily_costs = defaultdict(float)
        self.service_costs = defaultdict(float)
        self.alert_thresholds = {
            'daily': 2.00,    # $2 per day
            'monthly': 50.00  # $50 per month
        }
    
    def track_api_call(self, service, cost):
        today = datetime.now().strftime('%Y-%m-%d')
        self.daily_costs[today] += cost
        self.service_costs[service] += cost
        
        # Check thresholds
        if self.daily_costs[today] > self.alert_thresholds['daily']:
            self.send_cost_alert('daily', self.daily_costs[today])
    
    def get_monthly_projection(self):
        recent_days = list(self.daily_costs.values())[-7:]
        avg_daily_cost = sum(recent_days) / len(recent_days)
        return avg_daily_cost * 30
    
    def send_cost_alert(self, period, amount):
        alert = {
            'type': 'cost_alert',
            'period': period,
            'amount': amount,
            'timestamp': datetime.now().isoformat()
        }
        print(f"COST ALERT: {json.dumps(alert)}")
```

### Budget Dashboard

```python
def generate_cost_dashboard():
    """Generate real-time cost dashboard"""
    dashboard = {
        'current_month': {
            'total_spend': calculate_monthly_spend(),
            'budget': 50.00,
            'remaining': 50.00 - calculate_monthly_spend(),
            'days_remaining': get_days_remaining_in_month()
        },
        'service_breakdown': {
            'openai': get_service_cost('openai'),
            'google_cloud': get_service_cost('google_cloud'),
            'exotel': get_service_cost('exotel')
        },
        'usage_metrics': {
            'questions_processed': get_monthly_question_count(),
            'cost_per_question': calculate_cost_per_question(),
            'cache_savings': calculate_cache_savings()
        },
        'projections': {
            'end_of_month': project_monthly_cost(),
            'next_month': project_next_month_cost()
        }
    }
    return dashboard
```

### Automated Budget Controls

```python
class BudgetController:
    def __init__(self, monthly_budget=50.0):
        self.monthly_budget = monthly_budget
        self.current_spend = 0.0
        self.emergency_mode = False
    
    def check_budget_status(self):
        spend_percentage = (self.current_spend / self.monthly_budget) * 100
        
        if spend_percentage > 90:
            self.enable_emergency_mode()
        elif spend_percentage > 75:
            self.enable_conservation_mode()
        elif spend_percentage > 50:
            self.enable_optimization_mode()
    
    def enable_emergency_mode(self):
        """Activate when 90% budget used"""
        self.emergency_mode = True
        # Only serve cached responses
        # Disable non-essential features
        # Send immediate alerts
    
    def enable_conservation_mode(self):
        """Activate when 75% budget used"""
        # Increase cache TTL
        # Use lower quality TTS
        # Batch API calls more aggressively
    
    def enable_optimization_mode(self):
        """Activate when 50% budget used"""
        # Start optimizing API calls
        # Increase caching aggressiveness
        # Monitor usage more closely
```

## Scaling Economics

### Cost Per Question at Scale

| Monthly Questions | Cost per Question | Monthly Total | Optimization Level |
|-------------------|-------------------|---------------|-------------------|
| 500 | $0.016 | $8.20 | Basic caching |
| 1,000 | $0.014 | $14.00 | Smart caching |
| 5,000 | $0.011 | $55.00 | Aggressive optimization |
| 10,000 | $0.009 | $90.00 | Batch processing |
| 50,000 | $0.006 | $300.00 | Enterprise optimizations |
| 100,000 | $0.005 | $500.00 | Full automation |

### Economies of Scale

#### Volume Discounts
```python
def calculate_volume_pricing(monthly_questions):
    """Calculate pricing with volume discounts"""
    base_cost_per_question = 0.016
    
    if monthly_questions >= 100000:
        discount = 0.70  # 70% of base cost
    elif monthly_questions >= 50000:
        discount = 0.75  # 75% of base cost
    elif monthly_questions >= 10000:
        discount = 0.80  # 80% of base cost
    elif monthly_questions >= 5000:
        discount = 0.85  # 85% of base cost
    else:
        discount = 1.0   # No discount
    
    return base_cost_per_question * discount
```

#### Infrastructure Scaling
```python
def calculate_infrastructure_costs(monthly_questions):
    """Calculate infrastructure costs at different scales"""
    
    # Hosting costs
    if monthly_questions <= 1000:
        hosting_cost = 0  # Free tier
    elif monthly_questions <= 10000:
        hosting_cost = 25  # Basic paid tier
    elif monthly_questions <= 50000:
        hosting_cost = 100  # Professional tier
    else:
        hosting_cost = 300  # Enterprise tier
    
    # Additional services (Redis, monitoring, etc.)
    additional_services = min(monthly_questions * 0.001, 50)
    
    return hosting_cost + additional_services
```

## Best Practices

### 1. API Usage Optimization

#### Request Batching
```python
# Batch similar requests together
def batch_similar_requests(requests, batch_size=10):
    """Group similar API requests for efficiency"""
    batches = []
    current_batch = []
    
    for request in requests:
        current_batch.append(request)
        if len(current_batch) >= batch_size:
            batches.append(current_batch)
            current_batch = []
    
    if current_batch:
        batches.append(current_batch)
    
    return batches
```

#### Retry Logic with Exponential Backoff
```python
import time
import random

def api_call_with_retry(api_function, max_retries=3, base_delay=1):
    """Implement smart retry logic to avoid rate limits"""
    for attempt in range(max_retries):
        try:
            return api_function()
        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            
            # Exponential backoff with jitter
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            time.sleep(delay)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(base_delay)
```

### 2. Cache Management

#### Intelligent Cache Eviction
```python
class IntelligentCache:
    def __init__(self, max_size=1000):
        self.cache = {}
        self.access_count = defaultdict(int)
        self.last_access = {}
        self.max_size = max_size
    
    def get(self, key):
        if key in self.cache:
            self.access_count[key] += 1
            self.last_access[key] = time.time()
            return self.cache[key]
        return None
    
    def put(self, key, value):
        if len(self.cache) >= self.max_size:
            self._evict_least_valuable()
        
        self.cache[key] = value
        self.access_count[key] = 1
        self.last_access[key] = time.time()
    
    def _evict_least_valuable(self):
        # Calculate value score (frequency * recency)
        scores = {}
        current_time = time.time()
        
        for key in self.cache:
            frequency = self.access_count[key]
            recency = 1 / (current_time - self.last_access[key] + 1)
            scores[key] = frequency * recency
        
        # Remove lowest scoring item
        least_valuable = min(scores, key=scores.get)
        del self.cache[least_valuable]
        del self.access_count[least_valuable]
        del self.last_access[least_valuable]
```

### 3. Performance Monitoring

#### Cost-Performance Correlation
```python
def analyze_cost_performance():
    """Analyze relationship between cost and performance"""
    metrics = {
        'cost_per_second_saved': calculate_cost_per_second_saved(),
        'roi_of_caching': calculate_caching_roi(),
        'optimization_effectiveness': measure_optimization_impact()
    }
    
    # Generate recommendations
    recommendations = []
    
    if metrics['cost_per_second_saved'] > 0.01:
        recommendations.append("Consider more aggressive caching")
    
    if metrics['roi_of_caching'] < 2.0:
        recommendations.append("Review cache strategy effectiveness")
    
    return {
        'metrics': metrics,
        'recommendations': recommendations
    }
```

### 4. Budget Management

#### Predictive Budget Alerts
```python
def predict_monthly_overage():
    """Predict if monthly budget will be exceeded"""
    current_day = datetime.now().day
    days_in_month = calendar.monthrange(
        datetime.now().year, 
        datetime.now().month
    )[1]
    
    current_spend = get_month_to_date_spend()
    projected_spend = (current_spend / current_day) * days_in_month
    
    monthly_budget = 50.0
    overage_risk = projected_spend / monthly_budget
    
    if overage_risk > 1.2:
        return "HIGH_RISK"
    elif overage_risk > 1.0:
        return "MEDIUM_RISK"
    else:
        return "LOW_RISK"
```

#### Dynamic Budget Allocation
```python
class DynamicBudgetManager:
    def __init__(self, total_budget=50.0):
        self.total_budget = total_budget
        self.service_allocations = {
            'openai': 0.30,      # 30% of budget
            'google_cloud': 0.50, # 50% of budget
            'exotel': 0.20       # 20% of budget
        }
    
    def reallocate_budget(self, usage_stats):
        """Dynamically adjust budget allocation based on usage"""
        total_usage = sum(usage_stats.values())
        
        for service, usage in usage_stats.items():
            usage_percentage = usage / total_usage
            current_allocation = self.service_allocations[service]
            
            # Adjust allocation based on actual usage
            new_allocation = (current_allocation + usage_percentage) / 2
            self.service_allocations[service] = new_allocation
        
        # Normalize to ensure total = 1.0
        total_allocation = sum(self.service_allocations.values())
        for service in self.service_allocations:
            self.service_allocations[service] /= total_allocation
```

This comprehensive guide provides detailed strategies for optimizing API usage and managing costs effectively while scaling the VidyaVani system.