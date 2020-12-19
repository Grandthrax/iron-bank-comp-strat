from itertools import count
from brownie import Wei, reverts
from useful_methods import genericStateOfStrat, withdraw, stateOfStrat,genericStateOfVault, deposit, tend, sleep, harvest
import random
import brownie

def test_internal_iron_bank(strategy, ironbank, ibdai, creamdev, web3, dai, comp, chain, cdai, vault,currency, whale, strategist):
    print(strategy.currentSupplyRate())
    assert strategy.internalCreditOfficer()[1] == 0

    ironbank._setCreditLimit(strategy, 1_000_000 *1e18, {'from': creamdev})
    print(ironbank.getAccountLiquidity(strategy))
    assert strategy.internalCreditOfficer()[1] == 0

    #now deposit 
    deposit = 1_000 *1e18
    dai.approve(vault, 2 ** 256 - 1, {'from': whale})
    vault.deposit(deposit, {'from': whale})
    strategy.harvest({'from': strategist})

    print(strategy.compBlockShare())
    print(strategy.compBlockShare()*1e18/deposit)
    print(strategy.ironBankBorrowRate(0, True))
    print(strategy.currentSupplyRate())
    print(strategy.ironBankOutstandingDebtStored()/1e18)
    print(strategy.ironBankRemainingCredit()/1e18)

    #stateOfStrat(strategy, dai, comp)
    loanrequest = strategy.internalCreditOfficer()[1]
    print(loanrequest/1e18)
    assert loanrequest <= 4*deposit
    assert loanrequest > 0