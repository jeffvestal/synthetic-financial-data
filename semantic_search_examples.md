# Semantic Search Example Queries

This file contains example queries that demonstrate the semantic search capabilities of the financial dataset. All queries have been tested and validated against the generated synthetic financial data.

## Basic Semantic Search Examples

### Environmental & Legal Issues
```
Query: "environmental lawsuit disposal practices regulatory compliance"
Expected Results: ISRG (Intuitive Surgical environmental practices), VXUS (Vanguard environmental lawsuit)
Boost Settings: Semantic=3.0, Title=2.0 (high precision for legal content)
```

### Supply Chain & Risk Management  
```
Query: "supply chain risk insurance volatility business interruption"
Expected Results: AIG (supply chain risk assessment articles)
Boost Settings: Semantic=2.0, Title=1.5 (balanced approach)
```

### Pharmaceutical & Patent Law
```
Query: "patent invalidation pharmaceutical drug court ruling intellectual property"
Expected Results: JNJ (Johnson & Johnson patent court ruling), IBM (AI patent lawsuit)
Boost Settings: Semantic=2.5, Title=2.0 (comprehensive legal coverage)
```

### Corporate Finance & Debt Management
```
Query: "debt restructuring refinancing balance sheet optimization"
Expected Results: MO (Altria debt restructuring), NEE (NextEra financial concerns)
Boost Settings: Semantic=2.0, Title=1.5 (standard financial analysis)
```

### Clean Energy & Sustainability
```
Query: "clean energy sustainability renewable divestiture utilities"
Expected Results: XEL (Xcel Energy sustainability report)
Boost Settings: Semantic=2.0, Title=1.5 (environmental focus)
```

## Hybrid Search Examples (Semantic + Traditional)

### Corporate Leadership Changes
```
Query: "corporate leadership succession planning communication services"
Top Results: CHTR (Charter CEO departure), DIS (Disney CEO resignation)
Response Time: ~296ms
```

### Financial Optimization Strategies
```
Query: "balance sheet debt restructuring consumer staples financial optimization" 
Top Results: XLP (consumer staples challenges), NEE (debt concerns)
Response Time: ~289ms
```

### Energy Sector Transformation
```
Query: "renewable energy clean technology utilities sector transformation"
Top Results: NEE (NextEra Energy), DUK (Duke Energy leadership)
Response Time: ~206ms
```

## Domain-Specific Query Examples

### Risk Management Domain

#### Operational Risk
```
Query: "operational risk supply chain disruption mitigation strategies"
Focus: Supply chain resilience and business continuity planning
```

#### Credit Risk
```
Query: "credit risk assessment financial exposure management"
Focus: Financial risk evaluation and exposure control
```

#### Market Risk
```
Query: "market volatility portfolio optimization defensive positioning"
Focus: Volatility management and defensive investment strategies
```

### Corporate Finance Domain

#### Capital Structure
```
Query: "capital structure optimization debt equity balance"
Focus: Balance sheet optimization and financing decisions
```

#### M&A Activity
```
Query: "merger acquisition due diligence valuation analysis"
Focus: Corporate transactions and valuation methodologies  
```

#### Shareholder Returns
```
Query: "dividend policy shareholder return capital allocation"
Focus: Capital allocation decisions and shareholder value
```

### Regulatory Compliance Domain

#### Environmental Compliance
```
Query: "environmental compliance sustainability reporting requirements"
Focus: Environmental regulations and sustainability mandates
```

#### Financial Disclosure
```
Query: "financial disclosure transparency regulatory filing updates"
Focus: Financial reporting and transparency requirements
```

#### Intellectual Property
```
Query: "intellectual property protection patent litigation defense"
Focus: IP protection strategies and patent disputes
```

## Advanced Query Patterns

### Multi-Concept Queries
```
Query: "insurance risk management supply chain volatility"
Purpose: Tests ability to understand interconnected financial concepts
```

### Sector-Specific Thematic Queries
```
Query: "healthcare innovation medical device regulatory approval"
Query: "financial services digital transformation regulatory compliance"
Query: "energy transition renewable technology grid modernization"
```

### Event-Driven Queries
```
Query: "earnings disappointment analyst downgrade stock pressure"
Query: "leadership transition strategic direction market uncertainty"
Query: "regulatory investigation compliance failure reputation risk"
```

## Query Optimization Tips

### Boost Parameter Guidelines
- **Environmental/Legal Content**: Semantic=3.0, Title=2.0 (high precision)
- **Standard Financial Analysis**: Semantic=2.0, Title=1.5 (balanced)  
- **Broad Market Queries**: Semantic=1.5, Title=1.2 (wide coverage)

### Hybrid Search Settings
- **Semantic Component**: 2.0x boost for conceptual understanding
- **Traditional Component**: 1.2x boost for exact term matching
- **Title Fields**: Additional 1.5x boost for headline relevance

### Performance Expectations
- **Single Query Response Time**: 200-300ms
- **Typical Result Count**: 10-20 relevant documents per query
- **Score Ranges**: 30-140 for high relevance matches

## Dataset Coverage

The semantic search covers the following financial instruments and entities:

### Stocks & ETFs
- VXUS, AIG, JNJ, CHTR, ISRG, MO, XEL, EWO
- XLP, NEE, DUK, EA, IBM, DHR, PG, DIS, SMH, XLI

### Content Types
- **News Articles**: 550+ articles with semantic_text fields
- **Financial Reports**: 120+ reports with semantic_text fields  
- **Topics**: Environmental issues, patent disputes, leadership changes, debt restructuring

### Sectors Covered
- Healthcare, Technology, Utilities, Consumer Staples
- Financials, Communication Services, Energy
- Single Country Equity, Industrials

---

*All queries tested with ELSER (.elser-2-elasticsearch) semantic search on financial_news and financial_reports indices*