from itertools import count
from brownie import Wei, reverts
import eth_abi
from brownie.convert import to_bytes
from useful_methods import genericStateOfStrat, withdraw, stateOfVault,stateOfStrat,genericStateOfVault, deposit, tend, sleep, harvest
import random
import brownie

def test_screenshot(live_vault_dai, Contract,usdc, web3, accounts, chain, cdai, comp, dai, live_strategy2, live_strategy, currency, whale, samdev,creamdev, ibdai,ironbank):
    strategist = samdev

    strategy = live_strategy2
    

    vault = live_vault_dai
    #dai.approve(vault, 2 ** 256 - 1, {'from': whale})
    #vault.deposit(12000*1e18, {'from': whale})
    #strategy.harvest({'from': strategist})
    #strategy.tend({'from': strategist})
    #ironbank._setCreditLimit(strategy, 0, {'from': creamdev})
    #strategy.setMinCompToSell(0, {'from': strategist})
    #strategy.setKeeper(strategist, {'from': strategist})
    #vault.updateStrategyDebtLimit(strategy, 10, {'from': strategist})
    #strategy.harvest({'from': strategist})
    #strategy.harvest({'from': strategist})
    #strategy.harvest({'from': strategist})
    #stateOfStrat(strategy, dai, comp)
    #genericStateOfVault(vault, dai)
    #strategy.setDebtThreshold(0, {'from': strategist})

    #print("iron borrow: ", strategy.ironBankBorrowRate(0, True))
    #print("current supply: ", strategy.currentSupplyRate())
    #print("credit officer", strategy.internalCreditOfficer())
    #print("remaining credit", strategy.ironBankRemainingCredit()/1e18)
    print("iron bank outstanding", strategy.ironBankOutstandingDebtStored())

    #strategy.harvest({'from': strategist})

    

    #stateOfStrat(strategy, currency, comp)
    #genericStateOfVault(vault, currency)
    #genericStateOfStrat(strategy,currency, vault )

def test_limit_push(live_vault_dai, Contract,usdc, web3, accounts, chain, cdai, comp, dai, live_strategy2, live_strategy, currency, whale,samdev,creamdev, ibdai,ironbank):
    strategist = samdev
    strategy = live_strategy2
    

    vault = live_vault_dai

    stateOfStrat(strategy2, dai, comp)

    stateOfStrat(strategy, dai, comp)
    genericStateOfVault(vault, dai)

    print("iron borrow: ", strategy.ironBankBorrowRate(0, True))
    print("current supply: ", strategy.currentSupplyRate())
    print("credit officer", strategy.internalCreditOfficer())
    #print("remaining credit", strategy.ironBankRemainingCredit()/1e18)
    print("iron bank outstanding", strategy.ironBankOutstandingDebtStored()/1e18)

def test_migrate(live_vault_dai, Strategy,live_strategy2, strategist,Contract,usdc, web3, accounts, chain, cdai, comp, dai, live_strategy, currency, whale,samdev,creamdev, ibdai,ironbank):
        
    strategist = samdev
    strategy = live_strategy
    vault = live_vault_dai
    strategy2 = live_strategy2

    uinswap = '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D'
    weth = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
    ironcomptroller = '0xAB1c342C7bf5Ec5F02ADEA1c2270670bCa144CbB'
    irontoken = '0x8e595470Ed749b85C6F7669de83EAe304C2ec68F'
    comptroller = '0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B'
    solo = '0x1E0447b19BB6EcFdAe1e4AE1694b0C3659614e4e'

   # strategy2 = strategist.deploy(Strategy,vault, cdai, solo, comptroller, ironcomptroller, irontoken, comp, uinswap, weth)
    

    #stateOfStrat(strategy, dai, comp)
    #genericStateOfVault(vault, dai)
    
   # ironbank._setCreditLimit(strategy, 0, {'from': creamdev})
    print("credit officer", strategy.internalCreditOfficer())
    strategy.harvest({'from': strategist})
    vault.migrateStrategy(strategy, strategy2, {'from': strategist})
    stateOfStrat(strategy, dai, comp)

    #vault.revokeStrategy(strategy,{'from': strategist} )
    #strategy.setEmergencyExit({'from': strategist})

    #strategy.harvest({'from': strategist})
    #strategy.harvest({'from': strategist})
    #strategy.setEmergencyExit({'from': strategist})
    #strategy.harvest({'from': strategist})
   # ironbank._setCreditLimit(strategy2, 10_000 *1e18, {'from': creamdev})
    strategy2.harvest({'from': strategist})

    #stateOfStrat(strategy2, dai, comp)
    #genericStateOfVault(vault, dai)

    strategy2.tend({'from': strategist})
    stateOfStrat(strategy2, dai, comp)
    genericStateOfVault(vault, dai)
   
    #strategy2.harvest({'from': strategist2})
    
   # ironbank._setCreditLimit(strategy, 10_000 *1e18, {'from': creamdev})
   # stateOfStrat(strategy_base, dai, comp)
   # genericStateOfVault(vault, dai)
   # strategy.harvest({'from': strategist})
   # stateOfStrat(strategy_base, dai, comp)
   # genericStateOfVault(vault, dai)

    #print("iron borrow: ", strategy.ironBankBorrowRate(0, True))
    #print("current supply: ", strategy.currentSupplyRate())

    #print("iron bank outstanding", strategy.ironBankOutstandingDebtStored()/1e18)

    #strategy.harvest({'from': strategist})


def test_flash_loan(live_vault_dai2,live_vault_dai3,live_strategy_dai3, Contract, largerunningstrategy, web3,live_gov, accounts, chain, cdai, comp, dai, live_strategy_dai2,currency, whale,samdev):
    
    vault = live_vault_dai3
    live_strat = live_strategy_dai3

    #aave = Contract.from_explorer('0x398eC7346DcD622eDc5ae82352F02bE94C62d119')
    #malicious call
    #calldata = eth_abi.encode_abi(['bool', 'uint256'], [True, 1000])
    #calldata = eth_abi.encode_single('(bool,uint256)', [True, 1000])
    #print(calldata)
    #aave.flashLoan(live_strat, dai, 100, calldata, {'from': whale})
def test_shutdown(live_strategy_dai2,live_vault_dai2,live_strategy_usdc3, live_strategy_usdc4,live_vault_usdc3, live_strategy_dai4, Contract, usdc, web3,live_gov, accounts, chain, cdai, comp, dai, currency, whale,samdev):
    stateOfStrat(live_strategy_dai2, dai, comp)
    live_vault_dai2.revokeStrategy(live_strategy_dai2,  {'from': samdev})
    stateOfStrat(live_strategy_dai2, dai, comp)

    live_strategy_dai2.harvest({'from': samdev})
    live_strategy_dai2.harvest({'from': samdev})
    
    stateOfStrat(live_strategy_dai2, dai, comp)
    genericStateOfVault(live_vault_dai2, dai)
    

def test_migration(live_vault_dai3,live_strategy_dai3,live_strategy_usdc3, live_strategy_usdc4,live_vault_usdc3, live_strategy_dai4, Contract, usdc, web3,live_gov, accounts, chain, cdai, comp, dai, live_strategy_dai2,currency, whale,samdev):
    
    vault = live_vault_dai3
    live_strat = live_strategy_dai4
    old_strat = live_strategy_dai3
    stateOfStrat(old_strat, dai, comp)

    vault.migrateStrategy(old_strat, live_strat, {'from': live_gov})

    live_strat.harvest({'from':samdev})
    stateOfStrat(live_strat, dai, comp)

    print('usdc done')
    vault = live_vault_usdc3
    live_strat = live_strategy_usdc4
    old_strat = live_strategy_usdc3
    stateOfStrat(old_strat, usdc, comp)

    vault.migrateStrategy(old_strat, live_strat, {'from': live_gov})

    live_strat.harvest({'from':samdev})
    stateOfStrat(live_strat, usdc, comp)

    #aave = Contract.from_explorer('0x398eC7346DcD622eDc5ae82352F02bE94C62d119')
    #malicious call
    #calldata = eth_abi.encode_abi(['bool', 'uint256'], [True, 1000])
    #calldata = eth_abi.encode_single('(bool,uint256)', [True, 1000])
    #print(calldata)
    #aave.flashLoan(live_strat, dai, 100, calldata, {'from': whale})


def test_add_strat(live_vault_dai, Contract,usdc, web3, accounts, chain, cdai, comp, dai, live_strategy, currency, whale,samdev,creamdev, ibdai,ironbank):
    strategist = samdev
    strategy = live_strategy
    ironbank._setCreditLimit(strategy, 1_000_000 *1e18, {'from': creamdev})
    vault = live_vault_dai
    currency = dai
    gov = samdev

    stateOfStrat(strategy, currency, comp)
    genericStateOfVault(vault, currency)

    
    vault.addStrategy(
        strategy,
        2 ** 256 - 1,2 ** 256 - 1, 
        1000,  # 0.5% performance fee for Strategist
        {"from": gov}
    )

    amount = Wei('1000 ether')
    #print(dai.balanceOf(whale)/1e18)
    dai.approve(vault, amount, {'from': whale})
    vault.deposit(amount, {'from': whale})  
    chain.mine(1)

    strategy.harvest({'from': strategist})
    strategy.harvest({'from': strategist})

    stateOfStrat(strategy, currency, comp)
    genericStateOfVault(vault, currency)
    genericStateOfStrat(strategy,currency, vault )

def test_add_keeper(live_vault_dai2, Contract, web3, accounts, chain, cdai, comp, dai, live_strategy_dai2,currency, whale,samdev):
    strategist = samdev
    strategy = live_strategy_dai2
    vault = live_vault_dai2

    #stateOfStrat(strategy, dai, comp)
    #genericStateOfVault(vault, dai)

    keeper = Contract.from_explorer("0x13dAda6157Fee283723c0254F43FF1FdADe4EEd6")

    kp3r = Contract.from_explorer("0x1cEB5cB57C4D4E2b2433641b95Dd330A33185A44")

    #strategy.setKeeper(keeper, {'from': strategist})

    #carlos = accounts.at("0x73f2f3A4fF97B6A6d7afc03C449f0e9a0c0d90aB", force=True)

    #keeper.addStrategy(strategy, 1700000, 10, {'from': carlos})

    bot = accounts.at("0xfe56a0dbdad44Dd14E4d560632Cc842c8A13642b", force=True)

    assert keeper.harvestable(strategy) == False

    depositAmount =  Wei('3500 ether')
    deposit(depositAmount, whale, currency, vault)

    assert keeper.harvestable(strategy) == False

    depositAmount =  Wei('1000 ether')
    deposit(depositAmount, whale, currency, vault)
    assert keeper.harvestable(strategy) == True

    keeper.harvest(strategy, {'from': bot})
    balanceBefore = kp3r.balanceOf(bot)
    #print(tx.events) 
    chain.mine(4)
    #assert kp3r.balanceOf(bot) > balanceBefore
    #strategy.harvest({'from': strategist})

    assert keeper.harvestable(strategy) == False

    stateOfStrat(strategy, dai, comp)
    genericStateOfVault(vault, dai)

    #stateOfStrat(strategy, dai, comp)
    #stateOfVault(vault, strategy)
    #depositAmount =  Wei('1000 ether')
    
    #deposit(depositAmount, whale, currency, vault)

    #stateOfStrat(strategy, dai, comp)
    #genericStateOfVault(vault, dai)

    #strategy.harvest({'from': strategist})

    #stateOfStrat(strategy, dai, comp)
    #genericStateOfVault(vault, dai)