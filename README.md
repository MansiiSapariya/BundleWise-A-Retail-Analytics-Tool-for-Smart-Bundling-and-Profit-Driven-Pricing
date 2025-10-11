# 🛍️ BundleWise: Retail Analytics Tool for Smart Bundling and Profit-Driven Pricing

### 📘 Overview

**BundleWise** is an intelligent retail analytics system designed to help small and medium-sized businesses (SMBs) make data-driven decisions in product bundling, dynamic pricing, and performance analytics.
Built using **Python**, **Flask**, **Pandas**, and **Plotly**, the tool transforms sales data into actionable insights through an intuitive dashboard and exportable reports.



## 🎬 Demo Video

Watch the complete project demonstration here:
👉 [**BundleWise Demo Video**](https://drive.google.com/file/d/10Ip-N6BpPMiyY5VFP2jEq01S9kxHJXdr/view)



## 📸 Screenshots

All application screenshots, visualizations, and dashboards are included in the **BundleWise Report (PDF)** available in this repository.
It contains detailed visuals of:

* The **Upload Page**
* **Dashboard Tabs** (Summary, Product, Customer, and Advanced Analytics)
* **Bundle Recommendations and Pricing Module**
* **Generated PDF Report**



## 🎯 Objectives

* Identify product bundles using **Market Basket Analysis (MBA)** and **Sequential Pattern Mining (SPM)**.
* Recommend **optimized pricing strategies** for individual products and bundles.
* Provide an **interactive analytics dashboard** for sales, customer behavior, and advanced insights.
* Allow exporting of results in **PDF** and **Excel** formats.
* Enable **non-technical retailers** to use analytics through a simple, self-service interface.



## 🧩 System Features

### 🔹 Data Upload & Preprocessing

* Supports **CSV**, **Excel**, and **PDF** formats.
* Automatically validates and cleans uploaded data.
* Handles missing values, incorrect schema, and inconsistent formats.

### 🔹 Bundling Module

* Performs **Market Basket Analysis (MBA)** using the **Eclat** algorithm to identify frequently bought-together items.
* Uses **Sequential Pattern Mining (SPM)** to detect purchase sequences over time.
* Displays support, confidence, and lift values for all recommendations.

### 🔹 Pricing Optimization Module

* Suggests **profit-driven bundle prices** using optimization algorithms.
* Highlights potential **revenue gains** and **customer savings**.
* Flexible to adapt to changing pricing strategies.

### 🔹 Analytics Dashboard

* **Summary Tab:** KPIs such as total revenue, number of products, transactions, and AOV.
* **Product Performance Tab:** Top products, revenue concentration, and sales distribution.
* **Customer Insights Tab:** Customer segmentation, loyalty, and repeat purchase rates.
* **Advanced Analytics Tab:** Cross-sell heatmaps, seasonal trends, and profitability analysis.

### 🔹 Reporting Module

* Export results in **PDF** and **Excel**.
* Includes KPIs, 15+ visualizations, and actionable insights.
* Ideal for business reviews and decision-making.



## 🏗️ System Architecture

**BundleWise** follows a modular, three-layer architecture:

1. **Data Layer:** Handles ingestion, validation, and preprocessing.
2. **Backend Layer:** Performs MBA, SPM, and pricing optimization.
3. **Visualization & Reporting Layer:** Generates dashboards and reports using Flask + Plotly + ReportLab.



## ⚙️ Installation & Setup

### 🖥️ Requirements

* **Python:** 3.9 or above
* **RAM:** Minimum 4 GB
* **Browser:** Google Chrome or Microsoft Edge



### 🔧 Step 1: Create and Activate a Virtual Environment

#### 🪟 On Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

#### 🐧 On macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```



### 📦 Step 2: Install Dependencies

Install all required libraries using:

```bash
pip install -r requirements.txt
```



### ▶️ Step 3: Run the Application

Start the Flask server:

```bash
python app.py
```

Then open your browser and go to:

```
http://127.0.0.1:5000/
```


### 📂 Step 4: Upload Data

* Navigate to the **Upload Data** section.
* Upload your sales dataset (`.csv`, `.xlsx`, or `.pdf`).
* Wait for automatic validation and cleaning.

> 💡 **Note:** Sample sales data is included in the repository (`/sample_data/`) for testing and demonstration purposes.



## 📊 How to Use

1. **Upload** your transaction dataset or use the provided sample file.
2. **Analyze Bundles** — view frequently bought-together products.
3. **Optimize Prices** — get dynamic pricing suggestions.
4. **Explore Dashboard** — switch between Summary, Product, Customer, and Advanced tabs.
5. **Export Reports** in PDF or Excel for meetings and records.



## 🧠 Tech Stack

| Component           | Technology Used                                                                                          |
| ------------------- | -------------------------------------------------------------------------------------------------------- |
| **Backend**         | Python (Flask Framework)                                                                                 |
| **Data Processing** | Pandas, NumPy                                                                                            |
| **Visualization**   | Plotly, Matplotlib                                                                                       |
| **Reports**         | ReportLab, OpenPyXL                                                                                      |
| **Algorithms**      | Market Basket Analysis (Eclat), Sequential Pattern Mining, PrefixSpan, Optimization (Linear Programming) |
| **File Handling**   | Tabula-py (for PDFs)                                                                                     |



## 👩‍💻 Team Members

* **Abishai Tom**
* **Liya Khatija**
* **Mansi Sapariya**



## 🧾 License
This project was developed as part of the **M.Sc. Data Science** program at **CHRIST (Deemed to be University)**, Bengaluru, under the guidance of **Dr. Apash Roy**.


