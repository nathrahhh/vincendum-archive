# Credit Risk Engine

A full-stack private credit risk management platform that evaluates borrowers, assesses loan applications, and monitors portfolio exposure.

This project simulates a private credit workflow from client onboarding, deal evaluation, approval, and portfolio monitoring.

---

## Project Overview

Credit Risk Engine helps lenders evaluate new lending opportunities while managing:

- Client credit limits
- Portfolio concentration risk
- Loan approval workflows
- Risk breaches
- Portfolio exposure

The system separates client onboarding, loan evaluation, and portfolio monitoring to reflect a realistic credit approval process.

---

# Workflow

Client Application

↓

Admin Review

↓

Approved Client Created

↓

Deal Application Submitted

↓

Risk Evaluation

↓

+----------------+
|                |
Rejected       Pending
|                |
Breach Log    Admin Approval
                 |
                 v
          Portfolio Position

↓

Portfolio Monitoring

---

# Features

## Client Onboarding

Users can submit new borrower applications with:

- Business name
- Industry
- Requested credit limit

Administrators can:

- Review applications
- Approve clients
- Reject applications

Approved applications create new clients in the system.

---

## Deal Evaluation

Loan requests are evaluated before entering the portfolio.

Each deal goes through two risk checks:

### 1. Portfolio Concentration Risk

The system checks whether adding a new loan would breach industry exposure limits.

Example:

Current Technology Exposure:
$500,000

New Loan:
$300,000

The system evaluates whether total exposure remains within acceptable limits.

---

### 2. Client Credit Limit Check

The system checks borrower-level exposure.

Example:

Client Credit Limit:
$100,000

Existing Exposure:
$30,000

New Loan Request:
$50,000

Remaining Capacity:
$70,000

Result:
Approved

---

# Deal Lifecycle

Deals move through the following stages:

Submitted

↓

Risk Evaluation

↓

Pending

↓

Admin Approval

↓

Portfolio Position Created


Rejected deals:

Submitted

↓

Risk Evaluation

↓

Rejected

↓

Risk Breach Logged


Rejected deals do not enter the portfolio.

---

# Portfolio Monitoring

The portfolio dashboard tracks approved lending positions.

Features include:

- Current portfolio exposure
- Industry exposure breakdown
- Approved loans
- Borrower exposure

Only approved deals become portfolio positions.

---

# Risk Breach Monitoring

The system records risk events generated during evaluation.

Examples:

- Client credit limit exceeded
- Industry concentration limit exceeded

Stored breach information includes:

- Risk rule
- Reason
- Exposure values
- Additional details

---

# Technology Stack

## Frontend

- React
- TypeScript
- Vite

## Backend

- Python
- FastAPI
- SQLAlchemy

## Database

- PostgreSQL

## Data Analysis

- Pandas
- Matplotlib
- Jupyter Notebook

---

# System Architecture

Frontend

React + TypeScript

        |

        v

Backend API

FastAPI

        |

        v

Risk Engines + Business Logic

        |

        v

PostgreSQL Database


---

# Database Structure

## Clients

Stores approved borrowers.

Fields:

- ID
- Business name
- Industry
- Credit limit


## Deals

Stores submitted loan requests.

Fields:

- Deal name
- Loan value
- Industry
- Status
- Client ID

Statuses:

- PENDING
- APPROVED
- REJECTED


## Positions

Stores approved loans that have entered the portfolio.

Only approved deals become positions.


## Breaches

Stores risk events created during evaluation.

---

# Example Workflow

A borrower submits a loan request:

Company:

TechNova Solutions

Requested Loan:

$300,000


The system checks:

1. Does the borrower have enough remaining credit capacity?

2. Does the loan create excessive portfolio concentration?


If approved:

Deal

↓

Admin Approval

↓

Portfolio Position


If rejected:

Deal

↓

Risk Breach Logged

---

# Project Status

This project is an ongoing prototype exploring private credit workflows, lending controls, and financial technology system design.

It was built as a portfolio project to demonstrate full-stack development, financial risk modelling, and software engineering practices.
