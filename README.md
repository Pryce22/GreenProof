# 🍃 GreenProof - Sustainable Food Supply Chain

![Version](https://img.shields.io/badge/version-1.0.0-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)
![Blockchain](https://img.shields.io/badge/blockchain-Ethereum-7139e3)
![Platform](https://img.shields.io/badge/platform-Web-orange)

<p align="center">
  <img src="https://via.placeholder.com/600x300?text=GreenProof+Platform" alt="GreenProof Platform" width="600">
</p>

> GreenProof is a revolutionary blockchain-based platform that tracks CO₂ emissions throughout the entire food supply chain, enabling transparency, accountability, and rewarding sustainable practices through tokenization.

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Smart Contracts](#-smart-contracts)
- [API Reference](#-api-reference)
- [Security Measures](#-security-measures)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
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

- **🔐 Digital Signature Verification**
  - RSA-SHA256 cryptographic verification
  - Secure data submission and validation
  - Protection against fraudulent emission reports

- **🏆 Token Economy**
  - ERC20-based green tokens
  - Performance-based token rewards
  - Trading capabilities between supply chain participants

- **👁️ Supply Chain Transparency**
  - QR code product tracking
  - Consumer-facing product journey visualization
  - Environmental impact metrics for consumers

- **👥 User Management**
  - Role-based access control
  - Company verification process
  - Administrative approval workflow

## 🏗️ System Architecture

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
│  (Database & Chain)     │     │     Database      │
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

### Blockchain Setup

1. **Start Docker services**
   ```bash
   docker-compose up -d
   ```

2. **Deploy smart contracts**
   ```bash
   cd app/token
   truffle migrate --reset
   ```

3. **Verify deployment**
   ```bash
   truffle console
   truffle(development)> GreenToken.deployed().then(instance => instance.name())
   ```

## ⚙️ Configuration

### Environment Setup

Create a `.env` file in the root directory with the following variables:

```ini
# Blockchain Configuration
PRIVATE_KEY=your_ethereum_private_key
INFURA_PROJECT_ID=your_infura_project_id

# Database Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Email Configuration
EMAIL_USER=notification_email_address
EMAIL_PASSWORD=notification_email_password
EMAIL_SERVER=smtp.your-email-provider.com
EMAIL_PORT=587

# Application Configuration
DEBUG=True
SECRET_KEY=your_secret_key
```

### Database Setup

1. Create a Supabase project from the [Supabase Dashboard](https://app.supabase.io/)
2. Import the database schema:
   ```bash
   psql -h your-supabase-host -d postgres -U postgres -f database/schema.sql
   ```
3. Configure the connection in your `.env` file

## 🖥️ Usage

### Running the Application

1. **Start the Flask server**:
   ```bash
   python main.py
   ```

2. **Access the web interface** at `http://localhost:5001`

### User Roles

- **Admin**: Approve new companies, manage system settings
- **Company Admin**: Manage company profile, view emissions, trade tokens
- **Company User**: Input data, view company emissions

## 📂 Project Structure

```
/
├── app/                  # Main application code
│   ├── controllers/      # Business logic controllers
│   ├── routes/           # API endpoints
│   ├── templates/        # HTML templates
│   ├── token/            # Smart contract code
│   └── utils/            # Helper functions
├── static/               # Static assets
│   ├── css/              # Stylesheets
│   ├── js/               # JavaScript files
│   └── images/           # Image resources
├── tests/                # Test suites
├── database/             # Database migrations and schemas
├── docker/               # Docker configuration
├── docs/                 # Documentation
└── scripts/              # Utility scripts
```

## 📝 Smart Contracts

GreenProof uses two primary smart contracts:

### GreenToken Contract

An ERC20-compliant token used for rewarding sustainable practices:

```solidity
// Simplified GreenToken contract
contract GreenToken is ERC20 {
    address private _minter;
    
    constructor(address initialOwner) ERC20("GreenToken", "GRN") {
        _minter = initialOwner;
    }
    
    function mint(address to, uint256 amount) external {
        require(msg.sender == _minter, "Only minter can mint tokens");
        _mint(to, amount);
    }
    
    function setMinter(address minter, bool status) external {
        // Logic to set minter permissions
    }
}
```

### EmissionTracker Contract

Tracks and verifies emissions data on-chain:

```solidity
// Simplified EmissionTracker contract
contract EmissionTracker {
    GreenToken private _token;
    
    struct EmissionRecord {
        uint256 timestamp;
        uint256 amount;
        string dataHash;
        bool verified;
    }
    
    mapping(address => EmissionRecord[]) private _emissionRecords;
    
    constructor(address tokenAddress) {
        _token = GreenToken(tokenAddress);
    }
    
    function recordEmission(uint256 amount, string memory dataHash) external {
        // Record emissions and reward tokens based on performance
    }
}
```

## 🔒 Security Measures

### Digital Signature Verification

The system uses RSA-SHA256 signatures to verify the authenticity of emissions data:

```javascript
const verifier = crypto.createVerify('RSA-SHA256');
verifier.update(data);
verifier.end();
return verifier.verify(publicKey, signature, 'base64');
```

### Data Validation

All inputs are validated before being processed:
- Emission data is verified against industry standards
- User inputs are sanitized to prevent injection attacks
- API endpoints are protected with authentication and rate limiting

## ❓ Troubleshooting

### Common Issues

1. **Smart contract deployment fails**
   - Ensure Ganache is running and accessible
   - Check your Ethereum account has sufficient funds

2. **Database connection errors**
   - Verify your Supabase credentials
   - Check network connectivity to Supabase server

3. **Token transfer issues**
   - Ensure MetaMask is connected to the correct network
   - Verify the sender has sufficient token balance

## 🤝 Contributing

We welcome contributions to GreenProof! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add some amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a pull request

Please read our [Contributing Guidelines](CONTRIBUTING.md) for more details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👏 Acknowledgments

- The Ethereum community for their incredible tools and documentation
- Our early adopter companies for valuable feedback
- All contributors who have helped shape this project

---

<p align="center">
  Made with ❤️ by the GreenProof Team
</p>
