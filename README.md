# 🍃 GreenProof - Sustainable Food Supply Chain

![Version](https://img.shields.io/badge/version-1.0.0-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)
![Blockchain](https://img.shields.io/badge/blockchain-Ethereum-7139e3)
![Platform](https://img.shields.io/badge/platform-Web-orange)

<p align="center">
  <img src="/app/static/images/logo.png" alt="GreenProof Platform" width="300">
</p>

> GreenProof is a University project regarding a blockchain-based platform that tracks CO₂ emissions throughout the entire food supply chain, enabling transparency, accountability, and rewarding sustainable practices through tokenization.

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [System Architecture](#system-architecture)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#configuration)
- [Database](#database-schema)
- [Usage](#usage)
- [Project Structure](#-project-structure)
- [Security Measures](#-security-measures)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)
- [Acknowledgments](#-acknowledgments)

## 🌍 Overview

GreenProof connects the entire food supply chain on a unified platform to track environmental impact from farm to table. The system creates a transparent ecosystem where:

**Key Stakeholders:**
- **Manufacturers** — Primary producers who create raw materials
- **Processors** — Transform raw materials into processed products
- **Transporters** — Move products between supply chain participants
- **Sellers** — Retail companies that sell to end consumers

Each transaction and transfer in the supply chain is recorded on the blockchain, with CO₂ emissions calculated and tokenized. Companies with better environmental performance earn more green tokens, creating a sustainable incentive model.

## ✨ Features

### Core Features

- **🔗 Blockchain Integration**
  - Immutable records of supply chain activities
  - Smart contracts for automated token distribution
  - Transparent and tamper-proof data storage

- **🌱 CO₂ Tracking**
  - Real-time emission calculations
  - Industry-specific emission models
  - Historical emission trends and analytics

- **🏆 Token Economy**
  - ERC20-based green tokens
  - Performance-based token rewards
  - Trading capabilities between supply chain participants

- **👥 User Management**
  - Role-based access control
  - Company verification process
  - Administrative approval workflow

## System Architecture

GreenProof uses a layered architecture that combines blockchain, web services, and data analytics:

```
┌─────────────────────────┐
│     User Interface      │
│  (Web/Mobile Frontend)  │
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│    Application Layer    │
│   (Flask API Services)  │
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐     ┌────────────────────┐
│    Integration Layer    │────▶│  External Services │
│ (Blockchain Connectors) │     │(Email, Storage, etc)│
└───────────┬─────────────┘     └────────────────────┘
            │
┌───────────▼─────────────┐     ┌────────────────────┐
│     Storage Layer       │────▶│     Supabase      │
│  (Database & Chain)     │     │     Database       │
└───────────┬─────────────┘     └────────────────────┘
            │
┌───────────▼─────────────┐
│    Blockchain Layer     │
│  (Ethereum/Contracts)   │
└─────────────────────────┘
```

## 📋 Prerequisites

Before installing GreenProof, ensure you have the following:

- **Python 3.8+** - For backend services
- **Node.js 14+** and npm - For smart contract development
- **Docker** and Docker Compose - For containerization
- **Truffle** - Ethereum development framework
- **MetaMask** - Ethereum wallet for testing
- **Supabase** account - For backend database

## 🚀 Installation

### Clone and Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Software-Security-and-Blockchain.git
   cd Software-Security-and-Blockchain
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install and configure smart contracts**
   ```bash
   cd app/token
   npm install
   ```

4. **Install Truffle globally**
   ```bash
   npm install -g truffle
   ```

5.  **Start Docker services**
   ```bash
   docker-compose up -d
   ```

## Configuration

### Environment Setup

Create a `.env` file in the root directory with the following variables:

```ini
# Blockchain Configuration
PRIVATE_KEY=the_first_key_of_the_first_account_in_the_genesis_file_in_QBFT-Network

# Database Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Email Configuration
EMAIL_USER=notification_email_address
EMAIL_PASSWORD=notification_email_password(preferred email app password)

# Application Configuration
SECRET_KEY=your_secret_key
```
### Database Schema

<p align="center">
  <img src="/app/static/images/database_schema.png" alt="GreenProof Platform" width="800">
</p>

### Database Setup

1. Create a Supabase project from the [Supabase Dashboard](https://app.supabase.io/)
2. Import the database schema using one of these methods:
   - **Option A**: Using the command line (if you have PostgreSQL client installed):
     ```bash
     psql -h your-supabase-host -d postgres -U postgres -f database/schema.sql
     ```
   - **Option B**: Using the Supabase interface:
     1. Go to Supabase SQL Editor
     2. Create a new query
     3. Copy and paste the entire content of [schema.sql](http://_vscodecontentref_/0) file
     4. Execute the query
3. Configure the connection in your [.env](http://_vscodecontentref_/1) file with your Supabase credentials

## Usage

### Running the Application

1. **Start the Flask server**:
   ```bash
   python main.py
   ```

2. **Access the web interface** at `http://localhost:5000`

### User Roles

- **Admin**: Approve new companies, manage system settings
- **Company Admin**: Manage company profile, view emissions, trade tokens
- **Company User**: Input data, view company emissions

## 📂 Project Structure

```
/
├── app/                      # Main application code
│   ├── controllers/          # Business logic controllers
│   ├── routes/               # API endpoints
│   ├── QBFT-Network/         # Blockchain network configuration
│   ├── templates/            # HTML templates
│   │   └── includes/         # Template partials and components
│   ├── token/                # Smart contract code
│   │   ├── contracts/        # Solidity smart contracts
│   │   ├── migrations/       # Contract migration scripts
│   │   └── build/            # Contract compilation artifacts
│   ├── static/               # Static assets
│   │   ├── css/              # Stylesheets
│   │   ├── js/               # JavaScript files
│   │   ├── images/           # Image resources
│   │   └── favicon/          # Favicon files
│   │
│   │ 
│   └── utils/        # Helper functions

```

## 🔒 Security Measures

### Data Validation

All inputs are validated before being processed:
- Emission data is verified against industry standards
- User inputs are sanitized to prevent injection attacks

### Multi-Factor Authentication (MFA)

- Implemented email-based MFA for enhanced account security
- Requires users to verify their identity via a code sent to their registered email address during login

### Sensitive Data Encryption

- Sensitive data (e.g., passwords, API keys) is encrypted at rest in the database
- Utilizes industry-standard encryption algorithms to protect data confidentiality

### Log-User Action

- Comprehensive logging of user actions for auditing and security monitoring
- Logs include timestamps, user IDs, action types, and affected data

### Password Recovery

- Secure password recovery process using email verification
- Prevents unauthorized access to accounts during password resets

### Login Attempt Limiting

- Implemented rate limiting on login attempts to prevent brute-force attacks
- Accounts are temporarily locked after a certain number of failed login attempts

### Unique Sessions

- Enforces unique user sessions to prevent session hijacking
- Each user can only have one active session at a time

### Robust Password Policies

- Enforces strong password policies to ensure password complexity
- Requires passwords to meet minimum length, character type, and complexity requirements

## ❓ Troubleshooting

### Common Issues

1. **Smart contract deployment fails**
   - Ensure Docker is running and accessible

2. **Database connection errors**
   - Verify your Supabase credentials
   - Check network connectivity to Supabase server

3. **Token transfer issues**
   - Ensure MetaMask is connected to the correct network
   - Verify the sender has sufficient token balance

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Made by:
  <a href="https://github.com/L041B">Loris Bottegoni</a>,
  <a href="https://github.com/LeoC-02">Leonardo Cambiotti</a>,
  <a href="https://github.com/Pryce22">Valerio Crocetti</a>,
  <a>Angelo Kollcaku</a>,
  <a>Alex Voltattorni</a>.
</p>
