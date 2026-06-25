import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error
import joblib
import os


DATA_PATH = "data/airtel_auto_training_data.csv"
MODEL_PATH = "models/airtel_revenue_model.pkl"


df = pd.read_csv(DATA_PATH)

# Remove known bad outlier for now
df = df[df["Quarter"] != "Q4 FY19"]

X = df[["ARPU", "Customer Base"]]
y = df["Revenue"]

model = LinearRegression()
model.fit(X, y)

predictions = model.predict(X)

r2 = r2_score(y, predictions)
mae = mean_absolute_error(y, predictions)

print("Model trained successfully")
print("Rows used:", len(df))
print("R2 Score:", round(r2, 4))
print("Mean Absolute Error:", round(mae, 2))

print("\nCoefficients:")
print("ARPU:", model.coef_[0])
print("Customer Base:", model.coef_[1])
print("Intercept:", model.intercept_)

os.makedirs("models", exist_ok=True)
joblib.dump(model, MODEL_PATH)

print("\nModel saved to:", MODEL_PATH)


print("Model trained successfully")
print("Rows used:", len(df))
print("R2 Score:", round(r2,4))
print("Mean Absolute Eroor:", round(mae,2))