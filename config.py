REGRESSION_MODELS = [
    "Linear Regression",
    "Ridge Regression",
    "Random Forest Regression",
]

TREND_MODELS = ["Prophet"]

MODEL_DESCRIPTIONS = {
    "Linear Regression": (
        "Simple and transparent. Best when the revenue relationship is "
        "approximately linear."
    ),
    "Ridge Regression": (
        "A regularised linear model that usually gives more stable estimates."
    ),
    "Random Forest Regression": (
        "Learns more complex patterns but can be less reliable outside the "
        "historical range."
    ),
    "Prophet": (
        "Projects future revenue from the historical time-series trend."
    ),
}

APPROACH_DESCRIPTIONS = {
    "Regression Based": (
        "Uses business drivers such as ARPU and customer base."
    ),
    "Trend Based": (
        "Uses the sequence and shape of historical revenue values."
    ),
}
