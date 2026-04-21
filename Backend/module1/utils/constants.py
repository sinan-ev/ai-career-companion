# utils/constants.py

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

# Keyword → plain English meaning
COLUMN_KEYWORD_MAP = {
    "age": "Age of the individual",
    "fare": "Ticket or service price paid",
    "survived": "Survival outcome (target variable)",
    "sex": "Biological sex of the individual",
    "gender": "Gender of the individual",
    "salary": "Annual salary in currency units",
    "revenue": "Total revenue generated",
    "profit": "Net profit after costs",
    "department": "Organizational department",
    "dept": "Organizational department",
    "date": "Date of the event or record",
    "timestamp": "Exact date and time of event",
    "id": "Unique identifier",
    "name": "Name of entity or person",
    "country": "Country of origin or operation",
    "city": "City of origin or operation",
    "email": "Email address",
    "phone": "Phone number",
    "price": "Price of a product or service",
    "quantity": "Quantity or count of items",
    "churn": "Customer churn indicator (target variable)",
    "score": "Performance or evaluation score",
    "rating": "User or product rating",
    "class": "Class or category label",
    "target": "Target variable for prediction",
    "label": "Classification label",
}

# Domain hint keywords
DOMAIN_KEYWORD_MAP = {
    "titanic": ["survived", "pclass", "fare", "embarked", "cabin"],
    "sales": ["revenue", "profit", "sales", "units_sold", "discount"],
    "hr": ["salary", "department", "employee", "hire_date", "churn"],
    "healthcare": ["patient", "diagnosis", "hospital", "treatment", "age", "bmi"],
    "ecommerce": ["product", "price", "quantity", "order", "customer"],
    "finance": ["stock", "price", "volume", "open", "close", "market"],
    "logistics": ["shipment", "delivery", "weight", "origin", "destination"],
}