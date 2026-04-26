% Calibration handout — Samee
% Build predictive models to solve real-world classification and regression tasks

**Annotator:** Samee

**Brief:** Given a specific dataset (textual, tabular, or image-based), design and implement a machine learning pipeline that cleans data, performs feature engineering, and trains a predictive model. The deliverable should help a stakeholder understand: the predictive power of the features, the model's performance against a baseline, and how it handles unseen data. Deliver a documented Jupyter Notebook (or Python script) with training/evaluation loops, at least 2 distinct model architectures, and a 1-page report on error analysis.

**Rate each plan:** Feasibility 1-5 (1=not viable, 5=clearly doable) | Scope fit 1-5 (1=wrong size, 5=perfectly scoped for 14 days) | One sentence.

\bigskip

**Plan 1:** Use a tabular dataset (e.g., UCI Heart Disease, Kaggle House Prices) → Scikit-learn for a standard supervised learning pipeline

The student will build a predictive pipeline using a public tabular dataset to perform binary classification or regression. The core mechanism involves exploratory data analysis (EDA), handling missing values, and comparing a linear baseline (e.g., Logistic Regression or Linear Regression) against an ensemble method (e.g., Random Forest or XGBoost). The two scenarios compare model performance before and after hyperparameter tuning using GridSearch or RandomSearch, highlighting how specific feature transformations impact the final evaluation metrics (Accuracy/F1 or RMSE).

Feasibility: 4 / 5 \quad Scope fit: 3 / 5

Notes: Very feasible with standard tools and public datasets, but the scope may be a bit broad if the student tries to include EDA, feature engineering, two models, hyperparameter tuning, and full error analysis within 14 days. These are doable using scikit-learn, I think learning of PyTorch is necessary now so the assignment/project should reflect that.

\medskip

**Plan 2:** Use a text-based dataset (e.g., IMDb reviews, Twitter Sentiment) → Natural Language Processing (NLP) with NLTK or Spacy and Scikit-learn

The student will build a sentiment analysis or topic classification model using a dataset of text entries. The core mechanism involves text preprocessing (tokenization, lemmatization, stop-word removal) and converting text to numerical vectors using TF-IDF or Word2Vec. The two scenarios compare a traditional "Bag of Words" approach with a Naive Bayes classifier against a more modern approach using a pre-trained embedding or a simple Recurrent Neural Network (RNN). The evaluation will focus on confusion matrices to identify which classes are most frequently misidentified.

Feasibility: 3 / 5 \quad Scope fit: 5 / 5

Notes: This is feasible with common NLP datasets and Scikit-learn baselines, but the scope becomes large for 14 days if the student must cover preprocessing, TF-IDF/Word2Vec, Naive Bayes, embeddings or an RNN, and error analysis; it would fit better if the neural model is kept simple, preferably implemented in PyTorch.

\medskip

**Plan 3:** Use an image dataset (e.g., MNIST, CIFAR-10, or Kaggle Plant Pathology) → Computer Vision with PyTorch or TensorFlow/Keras

This project uses deep learning to perform image classification. The core approach involves building and training a Convolutional Neural Network (CNN) from scratch to recognize patterns in image data. The two scenarios are distinguished by complexity: the first scenario uses a simple custom CNN architecture, while the second scenario employs Transfer Learning by fine-tuning a pre-trained model (like ResNet or MobileNet) on the specific dataset. The deliverable will include visualizations of the loss/accuracy curves and a set of saliency maps or "incorrectly classified" examples.

Feasibility: 3 / 5 \quad Scope fit: 3 / 5

Notes: This is a strong fit because it uses PyTorch/TensorFlow, includes two distinct architectures through a custom CNN and transfer learning, and supports clear error analysis through misclassified examples; however, the scope should stay with MNIST or CIFAR-10 rather than a complex Kaggle medical/plant dataset to remain manageable in 14 days. 3 / 5 for scope, because there is not much data cleaning invloved in this project. The project should cover multiple aspects of machine learning.

\medskip

**Plan 4:** Use an unlabeled dataset (e.g., Mall Customer Segmentation, Credit Card transactions) → Unsupervised Learning for Clustering and Anomaly Detection

The project applies unsupervised machine learning to discover hidden structures in data or detect outliers. The core mechanism involves using K-Means or DBSCAN for customer segmentation, alongside Principal Component Analysis (PCA) for dimensionality reduction and visualization. The two scenarios are distinguished by the clustering objective: the first focuses on identifying distinct "personas" within the user base, while the second uses Isolation Forests to identify anomalous entries that deviate significantly from the norm.

Feasibility: 4 / 5 \quad Scope fit: 2 / 5

Notes: The methods are feasible and useful, but this plan does not fit the brief as well because the assignment asks for predictive classification or regression models with baseline comparison and evaluation on unseen data, while clustering/anomaly detection is mainly unsupervised and harder to evaluate clearly in that framework.

\medskip