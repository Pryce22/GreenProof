// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "./GreenToken.sol";

contract EmissionTracker is Ownable {
    GreenToken public greenToken;
    address public gasSponsorship;
    
    struct CompanyStats {
        bool is_processor;
        bool is_manufacturer;
        bool is_seller;
        bool is_transporter;
        // Current period metrics
        uint256 currentPeriodProducts;      // Products in current period
        uint256 currentPeriodEmissions;     // Emissions in current period
        // Previous period metrics
        uint256 previousPeriodProducts;     // Products from previous period
        uint256 previousPeriodEmissions;    // Emissions from previous period
        uint256 tokenBalance;               // GreenTokens earned
        uint256 lastReportedEmissions;      // Last emissions value reported
        uint256 lastUpdateTimestamp;        // Timestamp of last update
    }
    
    // Role-specific emission thresholds (in kg CO2)
    uint256 public processorEmissionThreshold = 115;
    uint256 public manufacturerEmissionThreshold = 11;
    uint256 public sellerEmissionThreshold = 3;
    uint256 public transporterEmissionThresholdPerKm = 111;
    
    // Token reward rates
    uint256 public baseTokenReward = 50 * 10**18;  // Base reward (50 tokens)
    uint256 public volumeBonusThreshold = 100;     // Number of products for bonus
    uint256 public volumeBonusAmount = 20 * 10**18; // Bonus amount (20 tokens)
    uint256 public efficiencyBonusPercent = 10;    // Additional % for high efficiency
    
    mapping(address => CompanyStats) public companyStats;
    address[] private registeredCompanies;
    mapping(address => bool) private isRegistered;
    
    event CompanyEmissionsUpdated(address company, uint256 newEmissions);
    event CompanyRoleUpdated(address company, string role, bool status);
    event TokensRewarded(address company, uint256 amount, string reason);
    event PeriodicDistribution(uint256 timestamp, uint256 totalTokensDistributed);
    
    constructor(address _greenTokenAddress, address initialOwner) 
        Ownable() 
    {
        greenToken = GreenToken(_greenTokenAddress);
        _transferOwnership(initialOwner);
        gasSponsorship = initialOwner;
        // Minting permissions are now set during deployment
    }

    function setGasSponsor(address newSponsor) public onlyOwner {
        require(newSponsor != address(0), "Invalid sponsor address");
        gasSponsorship = newSponsor;
    }

    function sponsoredBatchUpdateCompany(
        address company,
        bool isProcessor,
        bool isManufacturer,
        bool isSeller,
        bool isTransporter,
        uint256 averageEmissions,  // Emissions already scaled by 100
        uint256 totalQuantity
    ) external {
        require(msg.sender == gasSponsorship, "Only sponsor can execute");
        if (!isRegistered[company]) {
        registeredCompanies.push(company);
        isRegistered[company] = true;
        }
    
        CompanyStats storage stats = companyStats[company];
    
        
        // Store current period data as previous before updating
        stats.previousPeriodProducts = stats.currentPeriodProducts;
        stats.previousPeriodEmissions = stats.currentPeriodEmissions;
        
        // Update current period with new data
        stats.currentPeriodProducts = totalQuantity;
        stats.currentPeriodEmissions = averageEmissions;  // Already scaled
        
        // Update roles
        stats.is_processor = isProcessor;
        stats.is_manufacturer = isManufacturer;
        stats.is_seller = isSeller;
        stats.is_transporter = isTransporter;
        
        emit CompanyEmissionsUpdated(company, averageEmissions);
    }

    function distributeTokensForCompany(address company) internal {
        CompanyStats storage stats = companyStats[company];
        uint256 applicableThreshold = getCompanyEmissionThreshold(company);
        
        // Calcola emissioni per prodotto del periodo corrente
        uint256 currentEmissionsPerProduct = stats.currentPeriodProducts > 0 ? 
            stats.currentPeriodEmissions / stats.currentPeriodProducts : 0;
        
        if (currentEmissionsPerProduct < applicableThreshold) {
            uint256 efficiencyPercent = (applicableThreshold - currentEmissionsPerProduct) * 100 / applicableThreshold;
            uint256 reward = baseTokenReward * efficiencyPercent / 100;
            
            // Volume bonus basato sui prodotti del periodo corrente
            if (stats.currentPeriodProducts >= volumeBonusThreshold) {
                reward += volumeBonusAmount;
                emit TokensRewarded(company, volumeBonusAmount, "Volume Bonus");
            }
            
            // Efficiency bonus se l'efficienza è superiore al 50%
            if (efficiencyPercent > 50) {
                uint256 efficiencyBonus = reward * efficiencyBonusPercent / 100;
                reward += efficiencyBonus;
                emit TokensRewarded(company, efficiencyBonus, "Efficiency Bonus");
            }
            
            // Improvement bonus se ci sono dati del periodo precedente
            if (stats.previousPeriodProducts > 0) {
                uint256 previousEmissionsPerProduct = stats.previousPeriodEmissions / stats.previousPeriodProducts;
                if (currentEmissionsPerProduct < previousEmissionsPerProduct) {
                    uint256 improvementBonus = reward * efficiencyBonusPercent / 100;
                    reward += improvementBonus;
                    emit TokensRewarded(company, improvementBonus, "Improvement Bonus");
                }
            }
            
            if (reward > 0) {
                greenToken.mint(company, reward);
                stats.tokenBalance += reward;
                emit TokensRewarded(company, reward, "Emission Efficiency");
            }
        }
    }

    // Update threshold values
    function updateThresholds(
        uint256 _processorThreshold,
        uint256 _manufacturerThreshold,
        uint256 _sellerThreshold,
        uint256 _transporterThresholdPerKm
    ) external onlyOwner {
        processorEmissionThreshold = _processorThreshold;
        manufacturerEmissionThreshold = _manufacturerThreshold;
        sellerEmissionThreshold = _sellerThreshold;
        transporterEmissionThresholdPerKm = _transporterThresholdPerKm;
    }
    
    // Update reward parameters
    function updateRewardParams(
        uint256 _baseTokenReward,
        uint256 _volumeBonusThreshold,
        uint256 _volumeBonusAmount,
        uint256 _efficiencyBonusPercent
    ) external onlyOwner {
        baseTokenReward = _baseTokenReward;
        volumeBonusThreshold = _volumeBonusThreshold;
        volumeBonusAmount = _volumeBonusAmount;
        efficiencyBonusPercent = _efficiencyBonusPercent;
    }
    
    function getCompanyEmissionThreshold(address company) public view returns (uint256) {
        CompanyStats storage stats = companyStats[company];
        uint256 threshold = 0;
        
        if (stats.is_processor) threshold += processorEmissionThreshold / 10;
        if (stats.is_manufacturer) threshold += manufacturerEmissionThreshold;
        if (stats.is_seller) threshold += sellerEmissionThreshold;
        if (stats.is_transporter) threshold += transporterEmissionThresholdPerKm / 10;
        
        return threshold > 0 ? threshold : 1000;
    }

    function sponsoredDistributeTokens() external {
        require(msg.sender == gasSponsorship, "Only sponsor can execute");
        distributeTokensBasedOnEfficiency();
    }

    function distributeTokensBasedOnEfficiency() public {
        for (uint i = 0; i < registeredCompanies.length; i++) {
            address company = registeredCompanies[i];
            CompanyStats storage stats = companyStats[company];
            
            // Skip if no activity
            if (stats.currentPeriodProducts == 0) {
                emit TokensRewarded(company, 0, "No activity");
                continue;
            }
            
            // Calculate threshold properly - thresholds are NOT scaled by 100, but emissions are
            uint256 threshold = getCompanyEmissionThreshold(company) * 100;
            
            // Calculate emissions per product - both values are scaled the same way
            uint256 emissionsPerProduct = stats.currentPeriodProducts > 0 ? 
                stats.currentPeriodEmissions / stats.currentPeriodProducts : 0;
            
            emit CompanyEmissionsUpdated(
                company,
                emissionsPerProduct
            );

            // Debug logs to verify comparison
            // console.log("Emissions per product:", emissionsPerProduct);
            // console.log("Threshold:", threshold);
            
            // Check if emissions are below threshold
            if (emissionsPerProduct < threshold) {
                uint256 efficiency = ((threshold - emissionsPerProduct) * 100) / threshold;
                uint256 reward = (baseTokenReward * efficiency) / 100;
                
                // Volume bonus for significant production
                if (stats.currentPeriodProducts >= volumeBonusThreshold) {
                    reward += volumeBonusAmount;
                    emit TokensRewarded(company, volumeBonusAmount, "Volume Bonus");
                }
                
                // Improvement bonus if emissions decreased
                if (stats.previousPeriodProducts > 0) {
                    uint256 previousEmissionsPerProduct = stats.previousPeriodEmissions / stats.previousPeriodProducts;
                    if (emissionsPerProduct < previousEmissionsPerProduct) {
                        uint256 improvementBonus = (reward * efficiencyBonusPercent) / 100;
                        reward += improvementBonus;
                        emit TokensRewarded(company, improvementBonus, "Improvement Bonus");
                    }
                }
                
                // Only mint tokens if the reward is greater than zero
                if (reward > 0) {
                    greenToken.mint(company, reward);
                    stats.tokenBalance += reward;
                    emit TokensRewarded(
                        company, 
                        reward,
                        "Emission Efficiency"
                    );
                }
            }
        }
    }

    function getAllRegisteredCompanies() public view returns (address[] memory) {
        return registeredCompanies;
    }

    // Split into basic stats and metrics
    function getCompanyBasicStats(address company) external view returns (
        bool isProcessor,
        bool isManufacturer,
        bool isSeller,
        bool isTransporter,
        uint256 tokenBalance
    ) {
        CompanyStats storage stats = companyStats[company];
        return (
            stats.is_processor,
            stats.is_manufacturer,
            stats.is_seller,
            stats.is_transporter,
            stats.tokenBalance
        );
    }

    function getCompanyMetrics(address company) external view returns (
        uint256 currentPeriodProducts,
        uint256 currentPeriodEmissions,
        uint256 previousPeriodProducts,
        uint256 previousPeriodEmissions,
        uint256 emissionThreshold
    ) {
        CompanyStats storage stats = companyStats[company];
        return (
            stats.currentPeriodProducts,
            stats.currentPeriodEmissions,
            stats.previousPeriodProducts,
            stats.previousPeriodEmissions,
            getCompanyEmissionThreshold(company)
        );
    }
}