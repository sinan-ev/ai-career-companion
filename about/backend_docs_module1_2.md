# Backend Documentation — Module 1 & Module 2
> **AI Career Companion** | Full line-by-line backend explanation

---

## 📁 PROJECT ENTRY POINT — `Backend/main.py`

**What it is:** The FastAPI application root. Every HTTP request enters here.

**Why it exists:** Ties all 4 modules together under one server. Routes `/process` uploads, mounts module routers, and switches storage between local disk and GCS.

### Key sections

| Lines | What it does |
|---|---|
| `app = FastAPI(...)` | Creates the ASGI app. Title, version, CORS config all set here |
| `app.add_middleware(CORSMiddleware, allow_origins=["*"])` | Allows any frontend domain to call the API |
| `app.include_router(module3_router, prefix="/m3")` | Mounts Module 3 routes under `/m3/...` |
| `app.include_router(module4_router, prefix="/m4")` | Mounts Module 4 routes under `/m4/...` |
| `@app.post("/process")` | **Main endpoint** — receives an uploaded CSV/Excel file |
| `@app.get("/download/{artifact_id}")` | In GCS mode returns a signed URL; in local mode streams the file directly |
| `cleanup_old_local_files(...)` | Called after each run to delete exports older than N hours (local mode only) |

### `/process` endpoint logic (step by step)
```
1. Receive multipart file upload
2. Read bytes → pandas DataFrame
3. Run module1.core.pipeline.run_pipeline(df) → AnalysisResponse
4. Run module2.core.pipeline_module2.run_module2(df, module1_output) → Module2Response
5. Depending on STORAGE_BACKEND:
   - local  → save CSV to exports/, save .pkl to artifacts/
   - gcs    → upload via gcs_storage.save_csv / save_pickle → get signed URL
6. Return unified JSON response to frontend
```

**Input:** `multipart/form-data` with field `file` (CSV or Excel)  
**Output:** JSON with `module1`, `module2`, `download_url`

---

## 📁 `Backend/utils/gcs_storage.py`

**What it is:** A storage abstraction layer.  
**Why it exists:** Code never calls `open()` or `pickle.dump()` directly — it calls these functions, which automatically route to local disk OR Google Cloud Storage based on the `STORAGE_BACKEND` env var.

| Function | Input | Output | What it does |
|---|---|---|---|
| `save_pickle(obj, path)` | Python object, file path | None | Serialises with `joblib`, uploads to GCS or writes to disk |
| `load_pickle(path)` | file path | Python object | Loads `.pkl` from GCS or disk |
| `save_json(data, path)` | dict, file path | None | Writes JSON to GCS or disk |
| `load_json(path)` | file path | dict | Reads JSON from GCS or disk |
| `save_csv(df, path)` | DataFrame, path | str (download URL or path) | Saves CSV; returns signed URL if GCS |
| `get_signed_url(blob_name)` | GCS blob name | str (URL) | Generates 1-hour signed download URL |
| `cleanup_old_local_files(dir, hours)` | directory, age | None | Deletes files older than `hours` (local mode only) |

**How GCS detection works:**
```python
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")
# "local" → uses filesystem paths
# "gcs"   → uses google-cloud-storage client with GCS_BUCKET_NAME env var
```

---

## 📁 `Backend/utils/llm_client.py`

**What it is:** Shared Groq API wrapper used by all modules.  
**Why it exists:** Centralises API key management and model selection in one place.

### `get_groq_client()` — used by Module 1 & 3
```python
@lru_cache()           # Only creates the client ONCE — cached for app lifetime
def get_groq_client() -> Groq:
    return Groq(api_key=_GROQ_API_KEY)
```
- Reads `GROQ_API_KEY` from `.env`
- `@lru_cache` means the Groq object is instantiated once and reused

### `LLMClient` class — used by Module 4 engines
```python
class LLMClient:
    def generate(self, system_prompt, user_prompt, require_json=False):
```
- Wraps `.chat.completions.create()`
- `require_json=True` appends `"Always respond with valid JSON only"` to system prompt
- Default model: `llama-3.1-8b-instant`
- Default max tokens: 2048 (overridable per call)

---

## 📁 `Backend/module1/config.py`

**What it is:** Pydantic settings model for Module 1.  
**Why it exists:** Type-safe, validated configuration loaded from `.env`.

```python
class Settings(BaseSettings):
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"
    storage_backend: str = "local"
    gcs_bucket_name: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"   # ← CRITICAL: ignores GCP-injected env vars like K_SERVICE
    )
```

**Why `extra="ignore"`?**  
Cloud Run injects variables like `K_SERVICE`, `K_REVISION`. Without `extra="ignore"`, Pydantic raises `ValidationError` because these fields are not declared in `Settings`.

```python
@lru_cache()
def get_settings() -> Settings:
    return Settings()
```
Settings object is cached — only parsed once per process lifetime.

---

## 📁 `Backend/module1/core/pipeline.py`

**What it is:** The Module 1 orchestrator — the 9-stage data understanding pipeline.  
**Why it exists:** Converts a raw DataFrame into a rich structured JSON describing domain, schema, quality, column meanings, and suggestions.

### The 9 stages (in order)
```
Stage 1: _load_data()         → validate shape, dtypes, size
Stage 2: _validate_schema()   → check for empty columns, all-null cols
Stage 3: _detect_schema()     → classify each column: numeric/categorical/datetime/boolean/id/unknown
Stage 4: _profile_data()      → compute missing%, duplicates, outliers per column
Stage 5: _detect_domain()     → LLM call → guess "Finance", "Healthcare", etc.
Stage 6: _generate_meanings() → LLM call → human meaning for each column name
Stage 7: _summarise()         → LLM call → 2-3 sentence dataset summary
Stage 8: _suggest_analyses()  → LLM call → list of suggested analysis ideas
Stage 9: _build_response()    → pack everything into AnalysisResponse Pydantic model
```

**Input:** `pd.DataFrame`  
**Output:** `AnalysisResponse` dict with keys:
- `dataset_info` — rows, cols, domain, file_name, was_sampled
- `data_schema` — `{numeric: [...], categorical: [...], datetime: [...], ...}`
- `data_quality` — `{missing_percent: {col: pct}, duplicate_rows: N, outlier_summary: {...}}`
- `column_meanings` — `{"Age": "Age of the passenger in years", ...}`
- `ai_summary` — short natural language dataset description
- `suggested_analyses` — list of analysis ideas

**LLM pattern used throughout:**
```python
response = groq_client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[
        {"role": "system", "content": "Return ONLY valid JSON. No markdown."},
        {"role": "user",   "content": filled_prompt}
    ],
    response_format={"type": "json_object"}
)
result = json.loads(response.choices[0].message.content)
```

---

## 📁 `Backend/module2/core/pipeline_module2.py`

**What it is:** The Module 2 orchestrator — AI-driven data cleaning pipeline.  
**Why it exists:** Unlike Module 1 (fixed 9 stages), Module 2 is dynamic — an AI agent decides which cleaning steps to run based on the actual data problems found.

### Flow
```
1. validate_inputs(df, module1_output)   → cross-check df columns vs Module 1 schema
2. generate_eda(df, module1_output)      → deep EDA report (skew, outliers, correlations)
3. agent_planner.generate_plan(...)      → LLM decides step sequence
4. target_detector.detect_target(...)    → identify Y column for ML
5. rule_engine.execute_plan(...)         → execute steps in canonical order
6. dataset_builder.build_datasets(...)  → build analytics_df + ml_df
7. artifact_manager.save_artifacts(...) → save encoders/scalers to disk or GCS
8. Return Module2Response
```

**Why validation first?**  
Module 1 may have sampled the data. The validator ensures the actual DataFrame matches the schema Module 1 analysed — if columns are missing, it raises a clear error before any cleaning starts.

---

## 📁 `Backend/module2/core/agent_planner.py`

**What it is:** The AI brain of Module 2 — decides which cleaning steps to run.

### `generate_plan(module1_output, eda_report)` → `List[str]`
```python
# 1. Build a rich text prompt with all dataset facts
prompt = _build_prompt(module1_output, eda_report)

# 2. Call Groq LLM → get JSON array of step names
raw = _call_groq(prompt, api_key)

# 3. Parse & validate → only allow known step names
plan = _parse_plan(raw)

# 4. If anything fails → rules-based fallback
if not plan:
    plan = _fallback_plan(module1_output, eda_report)
```

**Valid step names:** `remove_duplicates`, `handle_missing`, `handle_outliers`, `feature_engineering`, `encoding`, `scaling`, `feature_selection`

### `_build_prompt()` — what goes into the LLM context
| Data section | Source |
|---|---|
| Domain, dataset type, row/col counts | `module1_output["dataset_info"]` |
| Schema (numeric/categorical/datetime cols) | `module1_output["data_schema"]` |
| Missing % per column | `module1_output["data_quality"]["missing_percent"]` |
| Skewed columns, outlier columns | `eda_report["column_reports"]` |
| High-cardinality categoricals | `eda_report["column_reports"]` |
| EDA warnings (top 5 by severity) | `eda_report["warnings"]` sorted critical→low |

### `_fallback_plan()` — rules-based fallback logic
```python
if duplicate_rows > 0:           → add "remove_duplicates"
if any missing values:           → add "handle_missing"
if any outliers (severe):        → add "handle_outliers"
if skewed cols OR datetime cols: → add "feature_engineering"
if categorical_cols exist:       → add "encoding"
if numeric_cols exist:           → add "scaling"
if total_cols > 15 OR high card: → add "feature_selection"
```

---

## 📁 `Backend/module2/core/rule_engine.py`

**What it is:** The execution engine — runs each step in correct order regardless of what order the AI listed them.

**Why canonical order matters:**
```
Wrong order:  encode → handle_missing  (can't encode nulls)
Right order:  handle_missing → encode  (nulls gone before encoding)
```

### `CANONICAL_ORDER` (always enforced)
```python
["remove_duplicates", "handle_missing", "handle_outliers",
 "feature_engineering", "encoding", "scaling", "feature_selection"]
```

### `execute_plan(df, plan, module1_output, memory, ...)` → `(df, artifacts, steps_summary)`
```python
for step in steps_to_run:           # only steps in the AI's plan, but in canonical order
    memory.start_step(step)
    try:
        df_current, note = _run_step(step, df_current, ...)
        memory.end_step(step, details=note)
        steps_summary.append((step, "success", note))
    except Exception as e:
        memory.fail_step(step, error=str(e))
        continue                    # pipeline continues — one broken step doesn't stop all
```

**`artifacts` dict accumulated across steps:**
```python
{
  "encoder_map":    {},   # filled by encoding step
  "scaler_map":     {},   # filled by scaling step
  "features_added": [],   # filled by feature_engineering step
  "dropped_cols":   {},   # filled by feature_selection step
}
```

---

## 📁 `Backend/module2/core/memory.py` — `PipelineMemory`

**What it is:** Real-time execution logger for the dynamic pipeline.

```python
class PipelineMemory:
    def start_step(self, step_name)   → record start time
    def end_step(self, step_name, details="")  → record end time + note
    def fail_step(self, step_name, error="")   → mark failed + error message
    def log_warning(self, msg)         → add a warning entry
    def get_log(self)                  → return full structured log
```

**Why it exists:** Since Module 2 steps are dynamic (different for each dataset), there needs to be a trace of what ran, what was skipped, what failed, and why — for debugging and the final response.

---

## 📁 `Backend/module2/tools/cleaning.py`

**What it is:** Implements `handle_missing` and `remove_duplicates`.

### `handle_missing(df, module1_output)` — 3-pass strategy

**Pass 1 — Drop columns with too much missing data:**
```python
DROP_COLUMN_THRESHOLD = 60.0   # columns with >60% nulls are dropped entirely
effective_pct = max(module1_pct, actual_df_pct)  # use the worse estimate
```

**Pass 2 — Impute remaining nulls per column type:**
```python
numeric + skewed meaning (age/salary/fare):  → fill with MEDIAN
numeric + normal distribution:               → fill with MEAN  (also median by default — safer)
categorical + low cardinality (≤20 unique):  → fill with MODE
categorical + high cardinality (>20 unique): → fill with "missing" (string literal)
datetime:                                    → forward-fill, then backward-fill
unknown type (numeric):                      → fill with median
unknown type (text):                         → fill with "missing"
```

**Pass 3 — Drop any remaining rows that still have nulls**

---

## 📁 `Backend/module2/tools/outliers.py`

**What it is:** IQR-based outlier detection and handling.

### Logic
```python
IQR_MULTIPLIER = 1.5        # standard Tukey fence
q1, q3 = series.quantile([0.25, 0.75])
iqr = q3 - q1
lower_fence = q1 - 1.5 * iqr
upper_fence = q3 + 1.5 * iqr
```

**Columns that are ALWAYS skipped:**
- ID/index columns (`id`, `uuid`, `key`)
- Binary/flag columns (`flag`, `indicator`, `dummy`)
- Date part columns (`year`, `month`, `day`)
- Columns with fewer than 5 unique values (likely stored-as-int categoricals)

**Two strategies:**
- `"cap"` (default) → `df[col].clip(lower=lower_fence, upper=upper_fence)` — values clamped, no rows lost
- `"remove"` → rows where any column is outside fence are collected and dropped together

---

## 📁 `Backend/module2/tools/encoding.py`

**What it is:** Smart categorical-to-numeric encoder. Strategy chosen per column based on cardinality.

### Strategy table
| Unique values | Strategy | How |
|---|---|---|
| 0–2 | **binary** | `{val_a: 0, val_b: 1}` |
| 3–10 | **one-hot** | `pd.get_dummies(drop_first=True)` — original col dropped |
| 11–50 | **ordinal** | rank by frequency (most frequent = highest integer) |
| >50 OR high-card pattern | **frequency** | replace each value with its count in training data |
| boolean dtype | **boolean** | `{True/yes/1: 1, False/no/0: 0}` |

**Protected columns (never encoded):** target column, ID columns, numeric columns, datetime columns.

**Inference reuse:** `apply_saved_encoding(df, encoder_map)` re-applies the same mapping to test/new data without re-fitting.

---

## 📁 `Backend/module2/tools/scaling.py`

**What it is:** Smart numeric scaler. Strategy chosen per column based on data shape.

### Strategy selection logic
```python
if col in outlier_cols (Module 1 flagged): → RobustScaler  (median/IQR — resistant to outliers)
if col name matches rate/ratio/pct pattern AND values in [0,1]: → MinMaxScaler
if abs(skewness) > 2.0:                    → RobustScaler
if min >= 0 AND low coefficient of variation: → MinMaxScaler
else:                                      → StandardScaler (z-score)
```

**Columns NEVER scaled:** target column, ID columns, datetime columns, already-binary (0/1) columns, flag/indicator columns.

**Inference reuse:** `apply_saved_scaling(df, scaler_map)` applies fitted scalers to new data using `.transform()` (not `.fit_transform()`).

---

## 📁 `Backend/module2/tools/features.py`

**What it is:** Creates new derived columns from existing ones.

### 7 sub-operations
| # | Operation | Trigger | Example output |
|---|---|---|---|
| 1 | Datetime extraction | Any datetime column | `date_col_year`, `_month`, `_day`, `_weekday`, `_hour` |
| 2 | Log transform | Numeric col with `abs(skew) > 1.0` AND `min >= 0` | `Fare_log = log1p(Fare)` |
| 3 | Age binning | Col name/meaning contains age/tenure/experience | `Age_group = "young_adult"` |
| 4 | Family/combo features | Two cols with family keywords (SibSp, Parch) | `family_size = SibSp + Parch + 1` |
| 5 | Ratio features | Price col ÷ Count col | `Fare_per_family_size` |
| 6 | Categorical interaction | Two low-cardinality categoricals (≤5 unique) | `Sex_x_Pclass = "male_1"` |
| 7 | Suggestion hints | Module 1's `suggested_analyses` mentions "log" or "interaction" | honours the hint |

---

## 📁 `Backend/module2/tools/feature_selection.py`

**What it is:** Drops low-value columns through 3 progressive filters.

### Stage 0 — Always-drop columns
ID and raw datetime columns are dropped before any analysis (they carry no ML signal).

### Stage 1 — Variance filter
```python
VARIANCE_THRESHOLD = 0.01   # drop if std/range < 1% of column range
# Near-constant columns are useless for ML
```

### Stage 2 — Correlation filter
```python
CORRELATION_THRESHOLD = 0.95
# For each highly-correlated pair, keep the one with higher variance
# If one is protected (has a meaning), keep the protected one
```

### Stage 3 — Mutual Information filter
```python
MI_BOTTOM_PERCENTILE = 10   # drop bottom 10% by MI score with target
# Uses sklearn's mutual_info_classif or mutual_info_regression
# Skipped if fewer than 5 features (too small to safely drop anything)
# Safe fallback: if all MI = 0, drop nothing
```

---

## 📁 `Backend/module2/services/target_detector.py`

**What it is:** Identifies which column is the prediction target (Y variable).

### Detection priority (highest confidence first)
```
Priority 1 (0.95): Column MEANING contains "target", "label", "outcome", "predict"...
Priority 2 (0.85): Column NAME contains "survived", "churn", "price", "fraud", "y"...
Priority 3 (0.75): Column name appears near prediction words in Module 1's ai_summary
Priority 4 (0.65): Column name appears in Module 1's suggested_analyses text
Priority 5 (0.40): Last column in DataFrame (ML convention fallback)
Priority 6 (0.10): Absolute fallback — last column no matter what
```

**Non-target protection:** Columns matching `id`, `index`, `uuid`, `date`, `time` are explicitly rejected at every priority level.

---

## 📁 `Backend/module2/services/dataset_builder.py`

**What it is:** Creates two purpose-built output DataFrames.

### Why two datasets?
| Dataset | Purpose | Encoding | Scaling |
|---|---|---|---|
| `analytics_dataset` | Dashboards, reports, humans | ❌ Original string values kept | ❌ Raw numbers |
| `ml_dataset` | Model training (sklearn, XGBoost) | ✅ All numeric | ✅ Normalised range |

### `_compute_target_stats(df, target_col)`
- **Classification** (≤20 unique values): returns class distribution, balance %, imbalance flag (minority < 20%)
- **Regression** (>20 unique): returns mean, median, std, min, max

---

## 📁 `Backend/module2/services/artifact_manager.py`

**What it is:** Saves and loads fitted encoder/scaler objects.

**Why this is critical:** If you re-fit encoders on test data, `male=1/female=0` could flip to `male=0/female=1` — the model gets opposite inputs and produces garbage predictions.

### `save_artifacts(encoder_map, scaler_map, feature_cols, module1_output)`
```
artifacts/
└── {domain}_{timestamp}/
    ├── encoders.pkl      → full encoder_map dict
    ├── scalers.pkl       → full scaler_map dict (fitted sklearn objects)
    ├── metadata.json     → human-readable info (domain, rows, cols, encoder types)
    └── feature_list.json → ordered list of feature columns for inference
```

### `load_artifacts(artifact_dir)` → used for inference
```python
result["encoder_map"] = load_pickle("encoders.pkl")
result["scaler_map"]  = load_pickle("scalers.pkl")
result["feature_columns"] = load_json("feature_list.json")["feature_columns"]
```

### `list_saved_artifacts()` → API endpoint support
Lists all saved artifact folders sorted by recency, returning domain, timestamp, encoder/scaler counts.

---

## 📁 `Backend/module2/tools/eda.py` — `generate_eda()`

**What it is:** Deep Exploratory Data Analysis — produces a rich report that feeds the AI planner.

### What it computes
| Analysis | Method | Threshold |
|---|---|---|
| Skewness | `series.skew()` | moderate: \|skew\|>1.0, high: \|skew\|>2.0 |
| Outliers | IQR method | `OUTLIER_IQR_K = 1.5` (standard Tukey) |
| Correlations | Pearson `corr().abs()` | `CORR_HIGH = 0.85` |
| Cardinality | `nunique()` | low: ≤10, high: >50 |
| Target distribution | value_counts or describe | auto-detects classification vs regression |

### Quality Grade (`_compute_quality_grade`)
```
A: penalty < 2     (clean dataset)
B: penalty 2–3     (minor issues)
C: penalty 4–6     (moderate problems)
D: penalty ≥ 7     (serious data quality issues)
```
Penalties accumulate from: high missing %, severe outliers, high correlations, many duplicates, tiny dataset (<100 rows).
