# FROM python:3.10-alpine

# ENV PYTHONDONTWRITEBYTECODE 1
# COPY /cacert.pem /usr/local/share/ca-certificates/
# USER root
# RUN update-ca-certificates
# ENV PYTHONUNBUFFERED 1
# ENV REQUESTS_CA_BUNDLE=/usr/local/share/ca-certificates/cacert.pem

# RUN pip install jinja2 pyyaml

# WORKDIR /app
# ADD infrastructure /app/infrastructure/
# ADD dbt/models/DWH/STAGING /app/dbt/models/DWH/STAGING/
# COPY main.py /app/

# # ENV PYTHONPATH /app

# CMD ["python", "main.py"]
