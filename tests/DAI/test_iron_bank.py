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

    assert strategy.internalCreditOfficer()[1] == strategy.ironBankOutstandingDebtStored()
   # print(strategy.internalCreditOfficer())
   # stateOfStrat(strategy, dai, comp)
    strategy.harvest({'from': strategist})
    #stateOfStrat(strategy, dai, comp)
    assert strategy.ironBankOutstandingDebtStored() == 0


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
    blocksPerYear = 2_300_000
    print("iron bank apr:", strategy.ironBankBorrowRate(0, True)*blocksPerYear/1e18)
    print("strat apr:", strategy.currentSupplyRate()*blocksPerYear/1e18)
    print(strategy.ironBankOutstandingDebtStored()/1e18)
    print(strategy.ironBankRemainingCredit()/1e18)
    
    
    #first time we do not borrow anything because SR is 0
    #strategy.harvest({'from': strategist})
    
    


    #print(strategy.compBlockShare())
    #print(strategy.compBlockShare()*1e18/deposit)
    #print(strategy.ironBankBorrowRate(0, True))
    #print(strategy.currentSupplyRate())
    #print(strategy.ironBankOutstandingDebtStored()/1e18)
    #print(strategy.ironBankRemainingCredit()/1e18)

    #stateOfStrat(strategy, dai, comp)