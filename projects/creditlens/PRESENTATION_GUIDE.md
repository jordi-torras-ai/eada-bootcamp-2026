# CreditLens: presentation guide

Plain-language notes for explaining the website and analysis to classmates. The figures below are from the current generated report.

## Suggested opening

> My project is CreditLens, an educational website that explores a credit-risk dataset and demonstrates how classification models estimate whether a loan record has a default label. It has four parts: an interactive estimate, an overview of the data, exploratory data analysis, and a comparison of three models. It is a learning tool, not a real credit approval system.

## Suggested presentation flow (about 5–7 minutes)

### 1. Introduce the project

> CreditLens is a small interactive website for learning how a machine-learning model can study loan records. A visitor can change a hypothetical borrower's details and see the model's estimate. The other pages explain the dataset, show its main patterns, and compare three models. The result is a learning demonstration, not a decision about a real person's eligibility.

### 2. Describe the data

> The dataset has 32,581 loan records and 12 fields. Some fields describe the person, such as age, income, and employment length. Others describe the loan, such as the requested amount, interest rate, loan grade, and loan purpose. The outcome column is called `loan_status`: zero means the record was not marked as default, and one means it was marked as default. About 21.8% of the original rows have the default label. This is historical data, and its collection details are limited, so we should be careful about applying its patterns to people today.

### 3. Walk through EDA

> Before fitting models, I examined the data. The income histogram is crowded toward lower values and has a long tail toward very high values. The mean income is about 66,075, while the median is 55,000. A few very large incomes pull the average upward, so the median better describes the middle record. Variance describes how spread out values are around their mean; it is useful for describing spread, though its units are squared.

> The correlation chart summarizes how numeric fields move together in a straight-line pattern. The default label has a positive correlation with loan-to-income share, about 0.379, and interest rate, about 0.335, in this dataset. These are associations, not proof that either factor causes default. Some fields, such as loan grade and interest rate, may have been assigned during an earlier lending decision, so their timing could make them an imperfect predictor for a real-world use.

### 4. Explain the method

> I removed 165 exact duplicate rows, checked missing data, and kept `loan_status` separate from the input fields. I split the remaining data into training and test groups, keeping the default share similar in both. The models learned from the training group; I compared them on the held-out test group. Missing numeric values were filled with training-set medians, and categories were converted into a format the models can use. I used the same split and evaluation measures for all three models so the comparison is fair within this experiment.

### 5. Compare the models and explain ROC AUC

> I compared logistic regression, random forest, and gradient boosting. Logistic regression is the simpler baseline. Random forest combines many decision trees. Gradient boosting builds trees in sequence, with each new tree trying to improve on the earlier ones. Gradient boosting had the highest ROC AUC in this test split, 94.5%, and the highest F1 score, 83.7%.

> ROC AUC measures how well the model ranks default records above non-default records across many possible cutoffs. A value of 50% is about random ranking, and 100% is perfect ranking. So 94.5% does not mean that 94.5% of predictions are correct. At the displayed 50% cutoff, gradient boosting's accuracy was 93.8%. Its precision was 97.7%: when it flagged a record as default, it was usually right. Its recall was 73.3%: it found about three quarters of the records that had a default label and missed the rest. Which trade-off matters depends on the intended use.

### 6. Show the calculator and close

> The calculator runs logistic regression directly in the browser so the report can be opened as one local HTML file. The model estimates a score from the details entered; the score bands are plain-language descriptions, not approval or safety categories. The probability has not been calibrated for real-world lending. Overall, the project shows how to inspect data, train and compare classifiers, and explain their trade-offs, while also showing why a strong score on one historical dataset is not enough to make real lending decisions.

### Short definitions to remember

- **Accuracy:** the share of all test records classified correctly.
- **Precision:** among records flagged as default, the share that really had the default label.
- **Recall:** among records with the default label, the share the model found.
- **F1:** a single score that balances precision and recall.
- **ROC AUC:** how well scores rank positive cases above negative cases across different cutoffs.
- **False positive:** the model flags default, but the record's label is no default.
- **False negative:** the model predicts no default, but the record's label is default.

## 1. The idea of the website

CreditLens lets a visitor change a hypothetical borrower profile and see how a trained model's output changes. The other pages explain where the data came from, what patterns appear in it, and how three algorithms performed on records held out from training.

The prediction page uses logistic regression because it is straightforward to explain and its fitted parameters can be included directly in one standalone HTML file. Gradient boosting ranked highest in the model comparison, so the calculator and the top-ranked comparison model are not the same model. The website says this explicitly.

## 2. What the dataset represents

The source is the [“Credit Risk Dataset” shared on Kaggle](https://www.kaggle.com/datasets/laotse/credit-risk-dataset). It has 32,581 rows and 12 columns. Each row represents a loan record with borrower characteristics, loan details, credit-history fields, and an outcome named `loan_status`.

- `loan_status = 0`: the record has no default label.
- `loan_status = 1`: the record has a default label.
- The source file contains 25,473 zero labels and 7,108 one labels, so about 21.8% of its rows have the default label.
- There are 165 exact duplicate rows. Those were removed before the model split, leaving 32,416 labeled unique records for modeling.
- `person_emp_length` has 895 missing values and `loan_int_rate` has 3,116. The models fill missing numeric values with a median calculated from training data and missing categories with the most common training category.

This is historical data with limited documentation about when and how it was collected. We cannot assume that it represents current borrowers or current lending conditions.

## 3. How to explain the EDA page

EDA means **exploratory data analysis**. It is the first examination of a dataset: we summarize values, inspect distributions, and look for relationships and data-quality concerns before interpreting a model.

### Mean, median, and variance

The **mean** is the arithmetic average. The **median** is the middle value after sorting observations. When a variable has a long tail or extreme values, the mean can be pulled away from what is typical, while the median is often more representative.

For example, annual income has a mean of about 66,075 and a median of 55,000. Its maximum is 6,000,000, which creates a very long upper tail. That is why the income histogram is concentrated at the low end with a few extreme values. The mean and median tell us different things about this distribution.

**Variance** is the average squared distance from the mean (using the sample denominator, n−1). It measures spread. Because deviations are squared, variance is in squared units and can look large; it is most useful for comparing spread in the same variable or for statistical calculations. The standard deviation, which is the square root of variance, returns to the variable's original units.

The age and employment-length maximums (144 years and 123 years) are implausible. They are clues that these records should be investigated. The project keeps them visible and discusses them rather than silently deleting them.

### Histograms

A histogram groups numeric values into intervals. Bar height shows how many records fall in each interval. The income histogram shows strong right skew: many records have more moderate income values and a few have extremely high values. This helps explain why the mean exceeds the median.

### Correlations

The correlation heatmap uses **Pearson's correlation**, which ranges from −1 to +1. A value near +1 means two numeric variables tend to increase together; near −1 means one tends to decrease as the other increases; near zero means little linear relationship in this sample.

The strongest positive correlations with the default label are loan-to-income share (about +0.379) and interest rate (about +0.335). Income itself has a negative correlation with the default label (about −0.144). These are descriptive relationships in this dataset; they do **not** show that a variable causes default. Loan grade and interest rate may also reflect an earlier underwriting decision, which is a possible timing or proxy-leakage concern.

## 4. Methodology: how the models were built

1. The script checks the columns, missing values, duplicates, and target balance.
2. It removes exact duplicate rows and rows without a target label. The target column is kept separate from the predictors so the model cannot use the answer as an input.
3. It splits the remaining records into 75% training and 25% testing, stratifying the split so the default proportion stays similar. A fixed random seed (42) makes the split reproducible.
4. Preprocessing is learned in each training pipeline: numeric gaps are filled using the training median, category gaps with the training mode, categories are one-hot encoded, and numeric fields are standardized.
5. Each of the three algorithms is fit on the training partition and evaluated on the same held-out test partition. The comparison ranks models by ROC AUC, using F1 as a tie-breaker.

The held-out set has 8,104 records. It is used to estimate how well the trained algorithms classify unseen rows from this same dataset. This is one test split, not cross-validation or an external validation study.

## 5. How to explain the models

- **Logistic regression** learns a weighted relationship between the inputs and the log-odds of the default label. It is a common, relatively simple classification model. Balanced class weighting was used to give the smaller default group more influence during fitting.
- **Random forest** combines many decision trees. Individual trees make rule-like splits; averaging many trees can capture nonlinear patterns and interactions. Balanced class weighting was used.
- **Gradient boosting** builds decision trees sequentially, where each new tree tries to improve the errors left by earlier trees. In this project configuration, it did not use class weights.

## 6. Model comparison and metrics

| Model | Accuracy | Precision | Recall | F1 | ROC AUC |
|---|---:|---:|---:|---:|---:|
| Logistic regression | 81.3% | 55.2% | 77.0% | 64.3% | 86.9% |
| Random forest | 92.2% | 87.1% | 75.6% | 80.9% | 93.3% |
| Gradient boosting | 93.8% | 97.7% | 73.3% | 83.7% | 94.5% |

Use these simple explanations:

- **Accuracy:** out of all test records, how many labels were correct?
- **Precision:** when the model predicted default, how often was the record labeled default?
- **Recall:** out of the records that were labeled default, how many did the model find?
- **F1:** one score that balances precision and recall.
- **ROC AUC:** how well does the model rank default records above non-default records across possible thresholds? AUC of 0.5 is about random ranking; 1.0 is perfect ranking. Gradient boosting's 0.945 is strong ranking performance on this test set. It does **not** mean 94.5% of its predictions are correct; accuracy is 93.8% here.

Gradient boosting has the highest ROC AUC and F1 in this split. Its precision is high (97.7%), but recall is lower (73.3%). In simple terms, when it flagged default, it was usually right, but it still missed some of the records that had a default label.

### Confusion matrix: the actual counts

At the illustrative 50% threshold, the Gradient Boosting model produced:

| | Predicted no default | Predicted default |
|---|---:|---:|
| **Actual no default** | 6,301 correct | 31 false positives |
| **Actual default** | 474 false negatives | 1,298 correct |

A **false positive** is a no-default record flagged as default. A **false negative** is a default record the model missed. The counts show why accuracy alone is not enough: different mistakes have different meanings and costs.

## 7. How to explain the interactive estimate

The Risk Estimate page uses a logistic regression model refit on all 32,416 labeled, deduplicated rows. The visitor enters a hypothetical profile; the browser applies the model's fitted preprocessing and coefficients locally. The page shows the model's estimated score, a predicted class using a 50% display threshold, and plain-language wording.

The displayed ranges (lower, middle, higher, very high) are **descriptive score bands only**. They do not mean “safe,” “approved,” “qualified,” or “rejected.” Balanced class weighting can shift the model's probability output, and the model was not calibrated against a separate calibration sample. So the percentage is not a reliable real-world probability of an individual defaulting.

A useful explanation to classmates is:

> The model estimates a higher or lower score for the recorded default label based on patterns in historical records. It does not establish that this hypothetical borrower will or will not default.

## 8. Limitations and conclusion

- The dataset is historical, and collection time, sampling, and population are not well documented.
- Implausible maximum values and missing data may affect the analysis.
- Loan grade and interest rate may contain information about a prior lender decision. Their timing relative to default is unclear, so possible proxy or timing leakage needs further investigation.
- The results come from one random held-out split. There is no cross-validation, external test set, or current-population validation.
- The 50% classification threshold is illustrative. We did not optimize a threshold for a specific use case.
- The probability output has not been calibrated. Fairness, causal effects, and real lending suitability have not been evaluated.

### Closing statement

> In this dataset, Gradient Boosting achieved the strongest ranking performance, with ROC AUC 94.5%, while also showing a precision-recall trade-off at the 50% threshold. CreditLens demonstrates a complete classification workflow and makes those trade-offs visible. Because the data is historical and limited, the results are educational evidence about this dataset, not a basis for real lending decisions.

## Questions classmates may ask

**Why is Gradient Boosting not used in the calculator?**  
The calculator embeds logistic-regression parameters directly so the app stays self-contained in one HTML file. The comparison page still reports that Gradient Boosting ranked highest. A future version could export a tree ensemble for browser inference.

**Does an AUC of 94.5% mean the model is right 94.5% of the time?**  
No. AUC measures how well scores rank positive cases above negative cases over many thresholds. Accuracy for Gradient Boosting at the selected 50% threshold is 93.8%.

**Does a high score mean a borrower should be rejected?**  
No. The score bands are educational labels, the probability is uncalibrated, and the project does not assess fairness, current performance, or legal suitability.

**What would you improve next?**  
Check the unusual records, evaluate a model without loan grade and interest rate, use repeated or cross-validation splits, test probability calibration and thresholds, and validate on a better documented dataset with a clear intended prediction time.
