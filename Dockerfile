FROM python3.7

RUN pip install joblib scikit-learn

COPY .* /
