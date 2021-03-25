from itertools import count
from brownie import Wei, reverts
from useful_methods import genericStateOfStrat, withdraw, stateOfStrat,genericStateOfVault, deposit, tend, sleep, harvest
import random
import brownie

def test_internal_iron_bank(strategy, ironbank, ibdai, creamdev, web3, dai, comp, chain, cdai, vault,currency, whale, strategist):
    # print(strategy.currentSupplyRate())
    assert strategy.internalCreditOfficer()[1] == 0

    ironbank._setCreditLimit(strategy, 1_000_000 *1e18, {'from': creamdev})
    #print(ironbank.getAccountLiquidity(strategy))
    assert strategy.internalCreditOfficer()[1] == 0

    #now deposit 
    deposit = 1_000 *1e18
    dai.approve(vault, 2 ** 256 - 1, {'from': whale})
    dai.approve(ibdai, 2 ** 256 - 1, {'from': whale})

    #make sure iron bank has enough funds
    ibdai.mint(deposit*10, {'from': whale})

    vault.deposit(deposit, {'from': whale})
    strategy.harvest({'from': strategist})
    assert strategy.ironBankOutstandingDebtStored() == 0
    #first time we do not borrow anything because SR is 0
    strategy.harvest({'from': strategist})
    #stateOfStrat(strategy, dai, comp)
    #print(strategy.ironBankOutstandingDebtStored()/1e18)
    stateOfStrat(strategy, dai, comp)

    deposits, borrows = strategy.getCurrentPosition()

    #deposits should be more than 5x deposit

    assert deposits > deposit*5
    assert strategy.ironBankOutstandingDebtStored() <= deposit*4
    assert strategy.ironBankOutstandingDebtStored() > 0

    


    #print(strategy.compBlockShare())
    #print(strategy.compBlockShare()*1e18/deposit)
    #print(strategy.ironBankBorrowRate(0, True))
    #print(strategy.currentSupplyRate())
    #print(strategy.ironBankOutstandingDebtStored()/1e18)
    #print(strategy.ironBankRemainingCredit()/1e18)

    #stateOfStrat(strategy, dai, comp)
    loanrequest = strategy.internalCreditOfficer()[1]

    assert loanrequest == 0

def test_reduce_credit_limit(strategy, ironbank, ibdai, creamdev, web3, dai, comp, chain, cdai, vault,currency, whale, strategist):
     # print(strategy.currentSupplyRate())
    #assert strategy.internalCreditOfficer()[1] == 0

    ironbank._setCreditLimit(strategy, 1_000_000 *1e18, {'from': creamdev})
    #print(ironbank.getAccountLiquidity(strategy))
    #assert strategy.internalCreditOfficer()[1] == 0

    #now deposit 
    deposit = 1_000 *1e18
    dai.approve(vault, 2 ** 256 - 1, {'from': whale})
    dai.approve(ibdai, 2 ** 256 - 1, {'from': whale})

    #make sure iron bank has enough funds
    ibdai.mint(deposit*10, {'from': whale})

    vault.deposit(deposit, {'from': whale})
    strategy.harvest({'from': strategist})
    assert strategy.ironBankOutstandingDebtStored() == 0
    #first time we do not borrow anything because SR is 0
    strategy.harvest({'from': strategist})
    #stateOfStrat(strategy, dai, comp)
    #print(strategy.ironBankOutstandingDebtStored()/1e18)

    deposits, borrows = strategy.getCurrentPosition()

    #deposits should be more than 5x deposit

    assert deposits > deposit*5
    assert strategy.ironBankOutstandingDebtStored() <= deposit*4
    assert strategy.ironBankOutstandingDebtStored() > 0

    ironbank._setCreditLimit(strategy, 0 *1e18, {'from': creamdev})

    assert strategy.internalCreditOfficer()[1] <= strategy.ironBankOutstandingDebtStored() +10 and strategy.internalCreditOfficer()[1] >= strategy.ironBankOutstandingDebtStored() -10
   # print(strategy.internalCreditOfficer())
   # stateOfStrat(strategy, dai, comp)
    strategy.harvest({'from': strategist})
    #stateOfStrat(strategy, dai, comp)
    assert strategy.ironBankOutstandingDebtStored() < 10


def test_supply_rates(strategy, ironbank, ibdai, creamdev, web3, dai, comp, chain, cdai, vault,currency, whale, strategist):
    # print(strategy.currentSupplyRate())
    assert strategy.internalCreditOfficer()[1] == 0

    ironbank._setCreditLimit(strategy, 1_000_000 *1e18, {'from': creamdev})
    #print(ironbank.getAccountLiquidity(strategy))
    assert strategy.internalCreditOfficer()[1] == 0

    #now deposit 
    deposit = 1000 *1e18
    dai.approve(vault, 2 ** 256 - 1, {'from': whale})
    dai.approve(ibdai, 2 ** 256 - 1, {'from': whale})

    #make sure iron bank has enough funds
    ibdai.mint(deposit*10, {'from': whale})

    vault.deposit(deposit, {'from': whale})
    strategy.harvest({'from': strategist})

    assert strategy.ironBankOutstandingDebtStored() == 0
    strategy.harvest({'from': strategist})
    assert strategy.ironBankOutstandingDebtStored() > 0
    blocksPerYear = 2_300_000
    print("iron bank apr:", strategy.ironBankBorrowRate(0, True)*blocksPerYear/1e18)
    print("strat apr:", strategy.currentSupplyRate()*blocksPerYear/1e18)
    print(strategy.ironBankOutstandingDebtStored()/1e18)
    #print(strategy.ironBankRemainingCredit()/1e18)
    
    
    #first time we do not borrow anything because SR is 0
    #strategy.harvest({'from': strategist})
    
    


    #print(strategy.compBlockShare())
    #print(strategy.compBlockShare()*1e18/deposit)
    #print(strategy.ironBankBorrowRate(0, True))
    #print(strategy.currentSupplyRate())
    #print(strategy.ironBankOutstandingDebtStored()/1e18)
    #print(strategy.ironBankRemainingCredit()/1e18)

    #stateOfStrat(strategy, dai, comp)

def test_migrate(strategy, ironbank, ibdai,Strategy, creamdev,gov, web3, dai, comp, chain, cdai, vault,currency, whale, strategist):
    

    ironbank._setCreditLimit(strategy, 1_000_000 *1e18, {'from': creamdev})

    #now deposit 
    deposit = 1000 *1e18
    dai.approve(vault, 2 ** 256 - 1, {'from': whale})
    dai.approve(ibdai, 2 ** 256 - 1, {'from': whale})

    #make sure iron bank has enough funds
    ibdai.mint(deposit*10, {'from': whale})

    vault.deposit(deposit, {'from': whale})
    strategy.harvest({'from': strategist})
    assert strategy.ironBankOutstandingDebtStored() == 0
    strategy.harvest({'from': strategist})
    assert strategy.ironBankOutstandingDebtStored() > 0

    uinswap = '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D'
    weth = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
    ironcomptroller = '0xAB1c342C7bf5Ec5F02ADEA1c2270670bCa144CbB'
    irontoken = '0x8e595470Ed749b85C6F7669de83EAe304C2ec68F'
    comptroller = '0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B'
    solo = '0x1E0447b19BB6EcFdAe1e4AE1694b0C3659614e4e'

    strategy2 = strategist.deploy(Strategy,vault, cdai, solo, comptroller, ironcomptroller, irontoken, comp, uinswap, weth)
    ironbank._setCreditLimit(strategy2, 1_000_000 *1e18, {'from': creamdev})
    vault.migrateStrategy(strategy, strategy2, {'from': gov})
    assert strategy.ironBankOutstandingDebtStored() < 10
    stateOfStrat(strategy, dai, comp)
    strategy2.harvest({'from': strategist})
    assert strategy2.ironBankOutstandingDebtStored() == 0
    #
    #genericStateOfVault(vault, dai)
   # stateOfStrat(strategy2, dai, comp)

    print(strategy2.tendTrigger(2000000 * 30 * 1e9))
    print(strategy2.tendTrigger(1000000 * 30 * 1e9))
    print(strategy2.internalCreditOfficer())

    strategy2.tend({'from': strategist})
    
    assert strategy2.ironBankOutstandingDebtStored() > 0
    stateOfStrat(strategy2, dai, comp)
