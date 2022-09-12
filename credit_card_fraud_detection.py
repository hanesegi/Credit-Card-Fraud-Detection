# -*- coding: utf-8 -*-
"""Credit Card Fraud Detection

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/14gqB4bUQ7QUKup5gUdtIlbXUX9aBllGz

#Business Problem

<p align="justify"> perusahaan kartu kredit dapat mengenali transaksi kartu kredit palsu sehingga pelanggan tidak dikenakan biaya untuk barang yang tidak mereka beli.</p>

#Data Source

[dataset kaggle ](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud)

#Load Data
"""

# connect to Kaggle API

from google.colab import files
uploaded = files.upload()

for fn in uploaded.keys():
  print('User uploaded file "{name}" with length {length} bytes'.format(
      name=fn, length=len(uploaded[fn])))
  
# Then move kaggle.json into the folder where the API expects to find it.
!mkdir -p ~/.kaggle/ && mv kaggle.json ~/.kaggle/ && chmod 600 ~/.kaggle/kaggle.json

!kaggle datasets download -d mlg-ulb/creditcardfraud

!unzip /content/creditcardfraud.zip

"""#Import library"""

# Commented out IPython magic to ensure Python compatibility.
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
# %matplotlib inline
import seaborn as sns

from sklearn import preprocessing
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split,StratifiedKFold,cross_val_score,GridSearchCV

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier 
from sklearn.tree import DecisionTreeClassifier

# from sklearn.pipeline import make_pipeline
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler


from imblearn.pipeline import Pipeline as imbpipeline
from sklearn.model_selection import StratifiedKFold
# from sklearn.pipeline import Pipeline


from sklearn import metrics
from sklearn.metrics import precision_score, recall_score, confusion_matrix, classification_report, accuracy_score, f1_score

data = pd.read_csv('/content/creditcard.csv', sep=',')
data.head(2)

data.info()

data.shape

# check imbalance dataset
data['Class'].value_counts(normalize=True)*100
print("Transaksi yang bukan Penipuan :", round(data['Class'].value_counts()[0]/len(data) * 100,2), '% dari dataset')
print("Transaksi Penipuan :" , round(data['Class'].value_counts()[1]/len(data) * 100,2), '% dari dataset')

"""* **Catatan:** Pada dataset ini, sebagian besar transaksi adalah transaksi normal. Jika kami membangun model kami menggunakan kumpulan data ini, model kami mungkin tidak mendeteksi transaksi Penipuan. Untuk mengatasi masalah ketidakseimbangan dataset kita dapat menggunakan undersampling dengan teknik cross validation StratifiedKFold dan oversampling (SMOTE) dengan teknik cross validation StratifiedKFold.

#Exploratory Data Analysis
"""

from pylab import rcParams
rcParams['figure.figsize'] = 8,6
LABELS = ['Normal', 'Fraud']

count_classes = pd.value_counts(data['Class'], sort=True)
count_classes.plot(kind = 'bar', rot = 0)
plt.title("Transaction class distribution")
plt.xticks(range(2), LABELS)
plt.xlabel('Class')
plt.ylabel('Frequency')
plt.show()

# separating fraud and no-fraud transactions
fraud = data[data['Class']==1]
normal = data[data['Class']==0]

print(fraud.shape, normal.shape)

#  descriptive statistics for normal transactions
normal.Amount.describe()

#  descriptive statistics for fraud transactions
fraud.Amount.describe()

f, (ax1, ax2) = plt.subplots(2,1, sharex = True)
f.suptitle("Amount per transaction by class")
bins = 50
ax1.hist(fraud.Amount, bins=bins)
ax1.set_title('Fraud')

ax2.hist(normal.Amount, bins=bins)
ax2.set_title('normal')

plt.xlabel("Amount ($)")
plt.ylabel("No. of Transaction")

plt.xlim(0,20000)
plt.yscale('log')
plt.show()

f, (ax1, ax2) = plt.subplots(2,1, sharex = True)
f.suptitle("Time of transaction vs Amount by Class")

ax1.scatter(fraud.Time, fraud.Amount)
ax1.set_title('Fraud')

ax2.scatter(normal.Time, normal.Amount)
ax2.set_title('normal')

plt.xlabel("Time (in second)")
plt.ylabel("Amount")

plt.show()

# Correlation check

corrmat = data.corr()
top_corr_feature = corrmat.index
plt.figure(figsize=(20,20))
g = sns.heatmap(data[top_corr_feature].corr(), annot=True, cmap='coolwarm')

# making a copy of original data
data1 = data.copy()
data1.shape

# feature scaling 'Amount' and 'Time'
standard_Scaler=StandardScaler()
data1['s_amount'] = standard_Scaler.fit_transform(data1['Amount'].values.reshape(-1,1))
data1['s_time'] = standard_Scaler.fit_transform(data1['Time'].values.reshape(-1,1))

data1.drop(['Time','Amount'], axis=1, inplace=True)

data1.head()

y=data1["Class"]
x= data1.drop(["Class"],axis=1)

X_train, X_test, y_train, y_test = train_test_split(x, y, test_size=0.4, stratify=y, random_state=101)

#  Model training and evaluation
recall_list =[]
def modelEval(xtr,ytr,xte,yte,model):
    
    model.fit(xtr,ytr)
    
    # Prediction for Test and Train Dataset
    test_pred=model.predict(xte)
    train_pred =model.predict(xtr)
    
    tpr_score = metrics.precision_score(ytr, train_pred)
    trc_score = metrics.recall_score(ytr, train_pred)
    tac_score =metrics.accuracy_score(ytr,train_pred)

    #  Confusion Matrix and calculating accuracy score
    print("For Training Dataset.")   
    print(f'Accuracy: {tac_score:.4f}, Precision: {tpr_score:.2f}, Recall: {trc_score:.2f}')
    print(classification_report(ytr, train_pred))
    print("===============================")
    
    pr_score = metrics.precision_score(yte, test_pred)
    rc_score = metrics.recall_score(yte, test_pred)
    ac_score = metrics.accuracy_score(yte, test_pred)
    recall_list.append(rc_score)
    print("===============================")
    print("For Testing Dataset")
    print("===============================")
    print("F1:",metrics.f1_score(yte, test_pred))
    print(f'Accuracy: {ac_score:.2f}, Precision: {pr_score:.2f}, Recall: {rc_score:.2f}')
    print("===============================")
    

    print(classification_report(yte,test_pred))
    metrics.plot_confusion_matrix(model,xte,yte,cmap='YlGnBu')

print("Model Name : RandomForest")

model_rf = RandomForestClassifier(n_estimators=200,criterion ='gini', max_depth=10, min_samples_leaf=10,
                                              min_samples_split=10, random_state=42)
rf_model_Acc = modelEval(X_train,y_train,X_test,y_test,model_rf)

pipeline = imbpipeline(steps =[['underSample', RandomUnderSampler(random_state=110,sampling_strategy='majority')],
                           ['classifier', RandomForestClassifier(random_state=110)]])

RandomForestClassifier
param_grid = { "classifier__n_estimators":[200],
               "classifier__max_depth": [8,10],
               "classifier__min_samples_split":[10,12],
               "classifier__min_samples_leaf": [10,12],
               "classifier__criterion": ["gini", "entropy"]}

grid_search = GridSearchCV(estimator=pipeline,param_grid =param_grid,
                           
                           n_jobs=3)


rf_model_Acc = modelEval(X_train,y_train,X_test,y_test,grid_search)

pipeline = imbpipeline(steps =[['smote', SMOTE(random_state=110)],
                           ['classifier', RandomForestClassifier(random_state=110)]])

RandomForestClassifier
param_grid = { "classifier__n_estimators":[150],
               "classifier__max_depth": [10],
               "classifier__min_samples_split":[12],
               "classifier__min_samples_leaf":[15],
               "classifier__criterion": ["gini"]}

grid_search = GridSearchCV(estimator=pipeline,param_grid =param_grid,
                           n_jobs=3)


rf_model_Acc = modelEval(X_train,y_train,X_test,y_test,grid_search)

from xgboost import XGBClassifier
xgb_classifier = XGBClassifier()
xgb_model_Acc = modelEval(X_train,y_train,X_test,y_test,xgb_classifier)

model_list = ["Random Forest","RandomForestUnderSampler","RandomForestSMOTE","XGBoost"]

col_pal = sns.color_palette("cool",n_colors=7)
plt.rcParams['figure.figsize']=15,6 
ax = sns.barplot(x=model_list, y=recall_list, palette = col_pal, saturation =1.5)
plt.xlabel("Model Klasifikasi", fontsize = 16 )
plt.ylabel("% Recall", fontsize = 16)
plt.title("Perbandingan Model", fontsize = 16)
plt.xticks(fontsize = 12, horizontalalignment = 'center', rotation = 8)
plt.yticks(fontsize = 13)
for p in ax.patches:
    width, height = p.get_width(), p.get_height()
    x, y = p.get_xy() 
    ax.annotate(f'{height:.2%}', (x + width/2, y + height*1.02), ha='center', fontsize = 'x-large')
plt.show()

