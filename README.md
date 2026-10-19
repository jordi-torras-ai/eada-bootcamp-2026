# EADA Bootcamp 2026 · Ownly

A housing data-science project and property portal: explore Ames home sales, compare compact predictive models, and use Ownly to list homes and connect buyers with sellers.

The DigitalOcean deployment was removed on October 19, 2026. The application source, model artifacts, and reports remain available here, and Ownly can still be run locally. The [deployment guide](deploy/digitalocean/README.md) is retained as a reference for a future installation.

## Try Ownly, the property portal

The [Ownly portal](portal/README.md) supports email/password registration, property listings with seller contact details and cover photos, and private buyer–seller inbox conversations. It stores data in SQLite locally and SQLite-based D1 on the private hosted Site. Email verification is disabled during testing. The valuation tool connects to the saved predictive model with plain-language inputs, five quality levels, square feet/meters, and an interactive map of all 28 Ames neighborhoods.

Use Node.js 22.13 or newer. From a fresh clone:

```bash
git clone https://github.com/jordi-torras-ai/eada-bootcamp-2026.git
cd eada-bootcamp-2026/portal
npm ci
npm run dev
```

Accounts, listings, cover photos, and conversations are stored locally in the ignored `portal/.data/ownly.sqlite` file. The public repository contains application source and learning artifacts; it does not include the private application database or grant access to the hosted Site.

Open http://127.0.0.1:8850. The portal automatically uses the market-adjusted model; no price-period selection is needed. Results show the estimate year and latest available index period, currently 2026Q2, alongside the reference value and market multiplier. There is no measured 2026 accuracy; apartments, buildings constructed after 2010, and other cities remain unsupported by the valuation model. Listings can describe a wider range of properties. The bundled index snapshot determines the period; it must be refreshed as newer observations are published.

## Bring historical prices to the 2026 market level

The local FHFA Ames metropolitan house-price index snapshot is in `dat/market/`, with download URL, publication/retrieval dates, and checksums in `source.json`. The snapshot is not seasonally adjusted, covers sales and appraisal data, and uses revised historical index values. Its latest period is 2026Q2, published August 25, 2026. It is an index, not a new property-level sales dataset.

The separate companion model first normalizes every 2006–2009 training price to the 2010Q2 market level using the recorded sale quarter. It uses the original selected compact histogram boosting architecture with 75 predictors, excluding sale year and month. The resulting reference prediction is multiplied by `324.78 / 166.78 = 1.9473558` to produce a 2026Q2 scenario. Property characteristics are held fixed; renovations, aging, and local deviations from the metropolitan trend are not forecast.

```bash
source ~/myenv/bin/activate
python scripts/train_market_adjustment.py
python scripts/predict_market_prices.py \
  --input models/ames/example_properties.csv \
  --target-period 2026Q2 \
  --output reports/example_market_predictions.csv
```

The build saves a separate model in `models/ames_market/`, creates the browser model and market metadata, and refreshes `reports/ames_models.html` with a 2026 section, an index chart, a calculator, and downloadable scenarios. Only published quarters from the saved index snapshot are accepted. The original model and its KPI files are retained. CSV inference requires the 75 original property predictor columns; extra calendar and identifier fields are preserved in output, but are not used by the reference model.

The companion model and simplified UI have a descriptive retrospective 2010 check, using revised HPI and actual sale-quarter index values. This is not an as-of-date forecast or a new independent holdout; none of those historical metrics measure 2026 accuracy. The UI download includes the reference price, factor, period, source provenance, and supplied/assumed model inputs.

To refresh the HTML from saved results without retraining:

```bash
source ~/myenv/bin/activate
python scripts/train_models.py --report-only
```

## Compare compact price-prediction models

Open [`reports/ames_models.html`](reports/ames_models.html) for the completed, offline model benchmark. It compares linear regression, a decision tree, random forest, XGBoost, a small neural network, ridge regression, and histogram gradient boosting, plus a median-price baseline. Interactive charts, a sortable KPI table, an error analysis, model settings, metric definitions, and downloadable CSVs are embedded in the HTML.

```bash
source ~/myenv/bin/activate
python scripts/train_models.py
```

The benchmark uses the full 2,930-row Ames dataset with 77 predictors. It compares fixed, compact configurations on three forward validation splits (validate on 2007, 2008, and 2009 using only earlier years), selects the lowest mean validation RMSE, refits on 2006–2009, and scores all models on the 341 sales in 2010. Preprocessing is learned within each training fit. Identifiers and sale-type/condition fields are excluded. All learned models use log prices; reported errors are in original USD. CPU work is limited to two threads and there is no parameter search.

The EDA previously examined all rows, so 2010 is held out from this modeling procedure but is not a completely unseen external benchmark. Scores apply to historical Ames sales, not today's prices. The report explains further assumptions and limitations.

The selected pipeline and its input schema are saved in `models/ames/`. Make example predictions with:

```bash
source ~/myenv/bin/activate
python scripts/predict_prices.py \
  --input models/ames/example_properties.csv \
  --output reports/example_predictions.csv
```

New input CSVs must include all 77 original predictor column names. Blank cells are supported; literal `NA` category values are preserved. The five-feature starter CSV is not compatible with this full-feature model. The three example properties are held-out rows without target values.

If needed, install the model dependencies in the activated environment:

```bash
python -m pip install -r requirements-models.txt
```

Custom paths are available through `python scripts/train_models.py --help` and `python scripts/predict_prices.py --help`. Defaults resolve relative to the project, so both scripts also work from another current directory. The saved pipeline, metrics, predictions, data checksum, exact split membership, and package versions make the run reviewable and reproducible.

## Start with the EDA mini-course

Open [`courses/eda/index.html`](courses/eda/index.html) in a browser for a beginner-friendly, approximately 20-minute introduction to exploratory data analysis. No coding, installation, or web server is needed.

Six short lessons cover asking questions, reading a table, distributions, relationships, data quality, and communicating findings. The course includes interactive charts built from the local Ames data, quick checks with explanations, a mean-versus-median experiment, and a downloadable personal EDA note. Progress and draft notes are stored in the current browser when storage is available. You can print all lessons or save them as a PDF from the course footer.

The HTML file is self-contained and works offline. Links to the full report, starter CSV, and dictionary use the existing project folders; keep that structure to use those companion resources. The course embeds a snapshot of the current Ames data and is not regenerated by `scripts/eda.py`.

## Generate the EDA report

```bash
source ~/myenv/bin/activate
python scripts/eda.py
```

The script reads the full dataset and produces `reports/ames_eda.html`. Open that file in a browser. Its interactive charts, tables, and chart library are embedded, so the report works offline and can be shared as one file. Hover over charts for details, drag to zoom, and double-click to reset a chart. Search the column guide to find individual variables.

If dependencies are missing, install them in the activated environment:

```bash
python -m pip install -r requirements-eda.txt
```

To choose another copy of the full Ames CSV or a report destination:

```bash
python scripts/eda.py --input dat/ames/ames_housing.csv --output reports/ames_eda.html
```

Default paths work from any current directory. Explicit relative paths are relative to the current directory. The input must use the full dataset's original column names; `ames_starter.csv` is for the later, smaller modeling exercise.

## Project folders

- `courses/eda/index.html`: self-contained introductory EDA course with six interactive lessons.
- `dat/ames/ames_housing.csv`: complete CSV, 2,930 observations and 82 columns.
- `dat/ames/ames_starter.csv`: five proposed inputs and the known sale price.
- `dat/ames/AmesHousing.txt`: original tab-separated release, preserved as downloaded.
- `dat/ames/data_description.txt`: original variable definitions, decoded to UTF-8.
- `dat/ames/source.json`: download provenance and starter-column mapping.
- `scripts/eda.py`: analysis, chart creation, and report generation.
- `scripts/templates/ames_eda.html.j2`: report layout and explanatory text.
- `reports/ames_eda.html`: generated, self-contained report.

## What the analysis does

The report covers price distributions, missing values, documented absent features, duplicate records, date inconsistencies, unusual properties, numeric correlations, quality ratings, neighborhoods, sale conditions, and sale years. It includes a searchable guide to every column and a numeric statistics table.

Blank cells are counted separately. Their meaning needs context: an absent garage can explain a blank garage construction year. The literal category `NA` is preserved: the dictionary often defines it as an absent feature such as no pool or no basement. Parcel IDs retain leading zeros. Numeric-looking category codes such as `MS SubClass` remain categories. Source category padding is trimmed in memory only.

No records are removed, no missing values are filled, and no model is trained. Correlations use available numeric pairs and exclude identifiers and nominal category codes. Pearson correlations describe association, including a numeric approximation for ordered quality ratings; they are not accuracy scores or causal effects. Neighborhood and yearly medians are unadjusted summaries of the homes sold.

The EDA explores all available rows. Before selecting features or tuning a model for a final evaluation, define an untouched holdout and repeat those decisions using training data only. Fit imputation and categorical encoding on training data. The recorded prices are historical USD from 2006–2010.
