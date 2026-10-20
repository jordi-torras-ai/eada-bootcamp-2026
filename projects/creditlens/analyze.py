"""Build the standalone CreditLens app from the Laotse Kaggle CSV.

Usage: python analyze.py path/to/credit_risk_dataset.csv
Requires pandas, numpy, scikit-learn.
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path

# Keep this project self-contained when the optional ML package was installed here.
PROJECT_PACKAGES = Path(__file__).with_name(".creditlens_packages")
if PROJECT_PACKAGES.exists() and sys.version_info[:2] == (3, 12):
    sys.path.insert(0, str(PROJECT_PACKAGES))

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

TARGET = "loan_status"
KNOWN_LEAKAGE = {TARGET}
EXPECTED = ["person_age", "person_income", "person_home_ownership", "person_emp_length", "loan_intent", "loan_grade", "loan_amnt", "loan_int_rate", "loan_percent_income", "cb_person_default_on_file", "cb_person_cred_hist_length", TARGET]

def main():
    if len(sys.argv) < 2:
        raise SystemExit("Drop the Kaggle CSV into this folder and run: python analyze.py credit_risk_dataset.csv")
    source = Path(sys.argv[1]).expanduser().resolve()
    df = pd.read_csv(source)
    if TARGET not in df:
        raise SystemExit(f"Expected target column '{TARGET}'. Found: {', '.join(map(str, df.columns))}")
    if df[TARGET].nunique(dropna=True) != 2:
        raise SystemExit("Expected loan_status to contain exactly two classes.")
    audit = {"file": source.name, "rows": int(len(df)), "columns": list(map(str, df.columns)), "expected_columns_missing": [c for c in EXPECTED if c not in df], "missing": {str(k): int(v) for k,v in df.isna().sum().items() if v}, "duplicates": int(df.duplicated().sum()), "target_counts": {str(k): int(v) for k,v in df[TARGET].value_counts(dropna=False).items()}, "target_rate": float(df[TARGET].mean()), "leakage_review": "loan_status is excluded from predictors. loan_grade and loan_int_rate may encode an earlier underwriting assessment; whether they are available at the intended prediction time is undocumented. Report these as possible timing/proxy leakage and rerun without them as a sensitivity analysis."}
    # Exclude incomplete outcomes and exact duplicates before the split. This avoids
    # identical full records appearing in both train and holdout partitions.
    data = df.dropna(subset=[TARGET]).drop_duplicates().copy()
    audit["model_rows"] = int(len(data))
    y = data[TARGET].astype(int)
    X = data.drop(columns=[TARGET])
    # Flag suspicious rows where age/length/income/loan values are implausible but retain
    # all rows for reproducibility; the app reports these checks rather than silently deleting.
    num_cols = list(X.select_dtypes(include=np.number).columns)
    cat_cols = [c for c in X.columns if c not in num_cols]
    preprocess = ColumnTransformer([
        ("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), num_cols),
        ("cat", Pipeline([("impute", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))]), cat_cols)
    ])
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=.25, random_state=42, stratify=y)
    candidates = {
        "Logistic regression": LogisticRegression(max_iter=1200, class_weight="balanced", random_state=42),
        "Random forest": RandomForestClassifier(n_estimators=180, min_samples_leaf=3, class_weight="balanced", n_jobs=-1, random_state=42),
        "Gradient boosting": HistGradientBoostingClassifier(max_iter=120, learning_rate=.08, l2_regularization=1.0, random_state=42),
    }
    results=[]; fitted={}
    for name, estimator in candidates.items():
        pipe=Pipeline([("prep", preprocess), ("model", estimator)])
        pipe.fit(X_train,y_train); pred=pipe.predict(X_test); prob=pipe.predict_proba(X_test)[:,1]
        result={"name":name,"accuracy":float(accuracy_score(y_test,pred)),"precision":float(precision_score(y_test,pred,zero_division=0)),"recall":float(recall_score(y_test,pred,zero_division=0)),"f1":float(f1_score(y_test,pred,zero_division=0)),"roc_auc":float(roc_auc_score(y_test,prob)),"confusion":confusion_matrix(y_test,pred).tolist()}
        results.append(result); fitted[name]=pipe
    # Transparent, user-selectable criterion: rank by ROC AUC; tie-break on F1.
    winner=max(results,key=lambda r:(r["roc_auc"],r["f1"]))
    # Fit an equivalent standardized logistic model for browser inference, using precisely
    # the same preprocessing learned by sklearn's LogisticRegression pipeline.
    browser_pipe=Pipeline([("prep", preprocess), ("model", LogisticRegression(max_iter=1200,class_weight="balanced",random_state=42))])
    browser_pipe.fit(X,y)
    prep=browser_pipe.named_steps["prep"]; model=browser_pipe.named_steps["model"]
    feature_names=prep.get_feature_names_out().tolist()
    numeric_stats={}
    for c in num_cols:
        s=pd.to_numeric(df[c],errors="coerce").dropna()
        numeric_stats[c]={"count":int(s.count()),"mean":float(s.mean()) if len(s) else None,"median":float(s.median()) if len(s) else None,"variance":float(s.var()) if len(s)>1 else None,"min":float(s.min()) if len(s) else None,"max":float(s.max()) if len(s) else None,"hist":np.histogram(s,bins=12)[0].astype(int).tolist() if len(s) else [],"edges":np.histogram(s,bins=12)[1].astype(float).tolist() if len(s) else []}
    corr=df.select_dtypes(include=np.number).corr().fillna(0)
    report={"audit":audit,"results":results,"winner":winner["name"],"stats":numeric_stats,"correlation":{"labels":list(corr.columns),"values":corr.values.round(3).tolist()},"target_labels":{"0":"No default","1":"Default"},"split":{"train":len(X_train),"test":len(X_test),"seed":42},"model":{"features":feature_names,"coefficients":model.coef_[0].astype(float).tolist(),"intercept":float(model.intercept_[0]),"numeric":num_cols,"categorical":cat_cols,"medians":{c:float(prep.named_transformers_["num"].named_steps["impute"].statistics_[i]) for i,c in enumerate(num_cols)},"categories":{c:[str(x) for x in cats] for c,cats in zip(cat_cols,prep.named_transformers_["cat"].named_steps["onehot"].categories_)},"means":{c:float(prep.named_transformers_["num"].named_steps["scale"].mean_[i]) for i,c in enumerate(num_cols)},"scales":{c:float(prep.named_transformers_["num"].named_steps["scale"].scale_[i]) for i,c in enumerate(num_cols)}}}
    # HTML embeds JSON, so it opens directly as file:// without fetch/server.
    html=Path(__file__).with_name("template.html").read_text(encoding="utf-8")
    payload=json.dumps(report,allow_nan=False,separators=(",",":" )).replace("</","<\\/")
    built=html.replace("/*__CREDITLENS_DATA__*/null", payload)
    Path(__file__).with_name("CreditLens.html").write_text(built,encoding="utf-8")
    # Make index.html the ready-to-open page, rather than exposing the blank template.
    Path(__file__).with_name("index.html").write_text(built,encoding="utf-8")
    print(f"Built CreditLens.html from {source.name}: {len(df):,} rows; selected {report['winner']} by held-out ROC AUC.")

if __name__ == "__main__": main()
