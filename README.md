🌐 IoT-Driven CO Monitoring ETL Pipeline & Surveillance using AWS

A Cloud Computing Project

📌 Overview

This project implements an end-to-end ETL pipeline, real-time monitoring system, and analytics dashboard for CO (Carbon Monoxide) surveillance in high-altitude trekking tents. Since CO poisoning is a major risk at high altitudes—responsible for multiple deaths annually—this system aims to provide real-time alerts and cloud-based monitoring to reduce life-threatening exposure.

The solution uses IoT telemetry, processed through a fully serverless AWS ecosystem, enabling reliable, scalable, and low-cost analytics.

🚀 Key Features
🔹 Real-Time Data Ingestion

IoT environmental telemetry (Temperature, Humidity, CO levels)

Simulated dataset from Kaggle, mapped to 3 tents:

Tent 00 – controlled environment

Tent B8 – storage-like stable readings

Tent 1C – highly variable, work-area-like environment

🔹 ETL Pipeline on AWS

Extract → Raw data uploaded to an S3 bucket

Transform → AWS Glue cleans, enriches, and standardizes data

Load → Processed dataset stored in a structured S3 data lake

Automated schema detection and partitioning

🔹 Analytics + Queries

Amazon Athena queries for:

Latest tent readings

CO trends

Max/Avg temperature, humidity, and CO

High-CO alert counts

Temperature distribution analysis

🔹 Backend

Python Flask API exposing:

/latest

/avg_metrics

/max_metrics

/humidity_co

/temp_dist

/alert_counts

/co_trend

Integrated AWS SDK for querying Athena and generating live analytics

Simulated CO alerts for demonstration

🔹 Frontend Dashboard

Built using React.js

Real-time charts and tables:

CO Trend Line Graph

Temperature Distribution

Humidity vs CO Scatter Plot

Alerts Summary

Automatic refresh + alert popups

Clean UI for tent-wise monitoring

🏗️ System Architecture

IoT Sensor Data → S3 (raw) → AWS Glue ETL → S3 (processed) → Athena → Flask API → React Dashboard

This architecture is:
✔ Serverless
✔ Scalable
✔ Cost-efficient
✔ Easy to extend for real IoT deployments

📂 Project Structure
iot-dashboard-project/
├── backend/
│   └── app.py
│
├── frontend/   (React app - added as submodule)
│
└── README.md

🔧 Technologies Used
AWS

Amazon S3

AWS Glue

AWS Athena

IAM

CloudWatch (logs)

Backend

Python

Flask

Boto3

Frontend

React.js

Chart.js / Recharts

Dataset

Kaggle IoT Telemetry Dataset

Mapped to “Tents” for project relevance

🧪 Demo Capabilities

Simulated high CO alert (e.g., 130+ ppm)

API returns processed analytics in real-time

Dashboard auto-updates

Graphs and stats refresh every few seconds

📌 How to Run Locally
Backend
cd backend
pip install -r requirements.txt
python app.py

Frontend
cd frontend
npm install
npm start

🔐 Security Note

All AWS credentials have been removed.
Users should add their own configuration via environment variables.

🎯 Purpose of the Project

This project demonstrates how Cloud Computing + IoT can be combined to solve a real-world safety problem. It highlights:

Serverless data pipelines

Real-time analytics

Scalable big-data processing

Practical cloud deployment techniques

📘 Future Enhancements

Replace simulated data with live IoT sensor hardware

Add DynamoDB for persistent alerts

Add SNS/SMS push notifications

Deploy backend on AWS Lambda

Host frontend on AWS Amplify
