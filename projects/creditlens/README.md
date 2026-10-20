# CreditLens · Credit Risk Intelligence

CreditLens is an academic project that demonstrates an end-to-end classification workflow using the [“Credit Risk Dataset” shared on Kaggle](https://www.kaggle.com/datasets/laotse/credit-risk-dataset). It includes a standalone interactive estimate, dataset overview, exploratory data analysis, and a plain-language model comparison.

## View the app

Open [`index.html`](index.html) in a modern browser. The report is self-contained: charts, fitted logistic-regression parameters, and analysis are embedded in the file. It works locally without a server or network connection. `CreditLens.html` is the same ready-to-open app; `template.html` is the source template used to regenerate it.

## Rebuild from the CSV

1. Download the CSV from the Kaggle link above and place it next to `analyze.py` and `template.html` as `credit_risk_dataset.csv`.
2. Install Python dependencies if needed: `python3 -m pip install pandas numpy scikit-learn`.
3. Run `python3 analyze.py credit_risk_dataset.csv`.
4. Open the regenerated `index.html` or `CreditLens.html`.

The raw CSV is not included in this repository. Download it from Kaggle and review that source's terms before redistributing the data.

## Project contents

- `index.html` and `CreditLens.html`: self-contained interactive report.
- `template.html`: editable presentation and interaction template.
- `analyze.py`: dataset audit, preprocessing, classifier comparison, and HTML build.
- `PRESENTATION_GUIDE.md`: peer-friendly script and explanation of the dataset, EDA, metrics, model comparison, and limitations.

## Analysis notes

The analysis checks the source columns, missingness, exact duplicates, and class balance. It reports means, medians, sample variances, numeric histograms, and Pearson correlations. Three classifiers—logistic regression, random forest, and gradient boosting—are compared with accuracy, precision, recall, F1, ROC AUC, and a confusion matrix.

Exact duplicates are removed before the stratified 75/25 train/test split (seed 42). Numeric gaps are median-imputed and categorical gaps are mode-imputed using training data; categories are one-hot encoded and numeric values standardized. The target `loan_status` is excluded from predictors. The interactive calculator uses logistic regression refit on all labeled, deduplicated rows so the model can run directly in browser JavaScript.

## Limitations

This is a historical dataset with limited documentation about collection time and population. It is not evidence about current borrowers, lending performance, fairness, or causality. Loan grade and interest rate may reflect prior underwriting decisions; their timing relative to the outcome is unclear. Calculator scores are uncalibrated educational model outputs and must not be used for real credit decisions.
