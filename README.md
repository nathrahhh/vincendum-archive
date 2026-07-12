# Credit Risk Engine

A full-stack private credit risk management platform that simulates the lending workflow from borrower onboarding to portfolio monitoring.

The system evaluates loan requests using borrower credit limits and portfolio concentration rules before approving loans into the portfolio.

---

## Overview

Private credit teams need to answer two key questions before approving a loan:

1. Can this borrower take on more debt?
2. Will this loan create excessive portfolio risk?

This platform models that process by separating:

- Client onboarding
- Deal evaluation
- Risk checks
- Approval workflow
- Portfolio monitoring

---

## Workflow
             Client Application
                     |
                     v
              Admin Review
                     |
         +-----------+-----------+
         |                       |
      Rejected              Approved Client
         |                       |
    Risk Logged                 |
                                 v
                          Deal Application
                                 |
                                 v
                          Risk Evaluation
                                 |
                +----------------+----------------+
                |                                 |
             Rejected                          Pending
                |                                 |
          Breach Logged                   Admin Approval
                                                  |
                                                  v
                                           Portfolio Position
                                                  |
                                                  v
                                       Portfolio Monitoring



---

## Technology Stack

Frontend:
- React
- TypeScript
- Vite

Backend:
- Python
- FastAPI
- SQLAlchemy

Database:
- PostgreSQL

---

## Key Components

**Client Management**
- Borrower onboarding
- Credit limit assignment
- Financial data storage

**Deal Workflow**
- Loan application submission
- Risk evaluation
- Approval/rejection process

**Portfolio Monitoring**
- Approved loan positions
- Industry exposure tracking
- Borrower exposure monitoring

**Risk Management**
- Concentration breach logging
- Credit limit breach logging

---

## Project Goal

This project explores how private credit risk processes can be represented in a full-stack application, combining financial risk concepts with software engineering practices.
