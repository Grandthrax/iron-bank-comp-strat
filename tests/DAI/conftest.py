import pytest
from brownie import Wei, config


#change these fixtures for generic tests
@pytest.fixture
def currency(interface):
    #this one is dai:
    yield interface.ERC20('0x6b175474e89094c44da98b954eedeac495271d0f')
    #this one is weth:
    #yield interface.ERC20('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2')
@pytest.fixture
def vault(gov, rewards, guardian, currency, pm):
    Vault = pm(config["dependencies"][0]).Vault
    vault = guardian.deploy(Vault, currency, gov, rewards, "", "")
    yield vault
@pytest.fixture
def rewards(gov):
    yield gov  # TODO: Add rewards contract
@pytest.fixture
def Vault(pm):
    yield pm(config["dependencies"][0]).Vault

@pytest.fixture
def weth(interface):
  
    yield interface.ERC20('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2')

@pytest.fixture
def strategy_changeable(YearnWethCreamStratV2, YearnDaiCompStratV2):
    #yield YearnWethCreamStratV2
    yield YearnDaiCompStratV2

@pytest.fixture
def whale(accounts, web3, weth,dai, gov, chain):
    #big binance7 wallet
    acc = accounts.at('0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8', force=True)
    #big binance8 wallet
    #acc = accounts.at('0xf977814e90da44bfa03b6295a0616a897441acec', force=True)

    #lots of weth account
    wethAcc = accounts.at('0x767Ecb395def19Ab8d1b2FCc89B3DDfBeD28fD6b', force=True)

    weth.transfer(acc, weth.balanceOf(wethAcc),{"from": wethAcc} )

    weth.transfer(gov, Wei('100 ether'),{"from": acc} )
    dai.transfer(gov, Wei('10000 ether'),{"from": acc} )

    assert  weth.balanceOf(acc) > 0
    yield acc

@pytest.fixture()
def strategist(accounts, whale, currency):
    decimals = currency.decimals()
    currency.transfer(accounts[1], 100 * (10 ** decimals), {'from': whale})
    yield accounts[1]


@pytest.fixture
def samdev(accounts):
    yield accounts.at('0xC3D6880fD95E06C816cB030fAc45b3ffe3651Cb0', force=True)
@pytest.fixture
def gov(accounts):
    yield accounts[3]


@pytest.fixture
def guardian(accounts):
    # YFI Whale, probably
    yield accounts[2]

@pytest.fixture
def keeper(accounts):
    # This is our trusty bot!
    yield accounts[4]

@pytest.fixture
def rando(accounts):
    yield accounts[9]


@pytest.fixture
def dai(interface):
    yield interface.ERC20('0x6b175474e89094c44da98b954eedeac495271d0f')

@pytest.fixture
def usdc(interface):
    yield interface.ERC20('0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48')

#any strategy just deploys base strategy can be used because they have the same interface
@pytest.fixture
def strategy_generic(YearnDaiCompStratV2):
    #print('Do you want to use deployed strategy? (y)')
    #if input() == 'y' or 'Y':
    print('Enter strategy address')
    yield YearnDaiCompStratV2.at(input())

@pytest.fixture
def vault_generic(Vault):
    print('Enter vault address')
    yield Vault.at(input())

@pytest.fixture
def strategist_generic(accounts):
    print('Enter strategist address')
    yield accounts.at(input(), force=True)

@pytest.fixture
def governance_generic(accounts):
    print('Enter governance address')
    yield accounts.at(input(), force=True)

@pytest.fixture
def whale_generic(accounts):
    print('Enter whale address')
    yield accounts.at(input(), force=True)

@pytest.fixture
def want_generic(interface):
    print('Enter want address')
    yieldinterface.ERC20(input())

@pytest.fixture
def live_vault(Vault):
    yield Vault.at('0x9B142C2CDAb89941E9dcd0B6C1cf6dEa378A8D7C')

@pytest.fixture
def live_strategy(YearnDaiCompStratV2):
    yield YearnDaiCompStratV2.at('0x4C6e9d7E5d69429100Fcc8afB25Ea980065e2773')

@pytest.fixture
def live_vault_weth(Vault):
    yield Vault.at('0xf20731f26e98516dd83bb645dd757d33826a37b5')

@pytest.fixture
def live_strategy_weth(YearnWethCreamStratV2):
    yield YearnDaiCompStratV2.at('0x97785a81b3505ea9026b2affa709dfd0c9ef24f6')

@pytest.fixture
def dai(interface):
    yield interface.ERC20('0x6b175474e89094c44da98b954eedeac495271d0f')

#uniwethwbtc
@pytest.fixture
def uni_wethwbtc(interface):
    yield interface.ERC20('0xBb2b8038a1640196FbE3e38816F3e67Cba72D940')


@pytest.fixture
def samdev(accounts):
    yield accounts.at('0xC3D6880fD95E06C816cB030fAc45b3ffe3651Cb0', force=True)

@pytest.fixture
def earlyadopter(accounts):
    yield accounts.at('0x769B66253237107650C3C6c84747DFa2B071780e', force=True)

@pytest.fixture
def comp(interface):
    yield interface.ERC20('0xc00e94Cb662C3520282E6f5717214004A7f26888')

@pytest.fixture
def cdai(interface):
    yield interface.CErc20I('0x5d3a536e4d6dbd6114cc1ead35777bab948e3643')

#@pytest.fixture(autouse=True)
#def isolation(fn_isolation):
#    pass
@pytest.fixture(scope="module", autouse=True)
def shared_setup(module_isolation):
    pass

@pytest.fixture
def gov(accounts):
    yield accounts[0]



#uniswap weth/wbtc
@pytest.fixture()
def whaleU(accounts, history, web3, shared_setup):
    acc = accounts.at('0xf2d373481e1da4a8ca4734b28f5a642d55fda7d3', force=True)
    yield acc
    



@pytest.fixture
def rando(accounts):
    yield accounts[9]



@pytest.fixture()
def seededvault(vault, dai, rando):
   # Make it so vault has some AUM to start
    amount = Wei('10000 ether')
    token.approve(vault, amount, {"from": rando})
    vault.deposit(amount, {"from": rando})
    assert token.balanceOf(vault) == amount
    assert vault.totalDebt() == 0  # No connected strategies yet
    yield vault
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass

@pytest.fixture()
def strategy(strategist,gov, keeper, vault,  Strategy, cdai):
    strategy = strategist.deploy(Strategy,vault, "LeveragedDaiCompFarm", cdai)
    strategy.setKeeper(keeper)

    vault.addStrategy(
        strategy,
        2 ** 256 - 1,2 ** 256 - 1, 
        1000,  # 0.5% performance fee for Strategist
        {"from": gov},
    )
    yield strategy

@pytest.fixture()
def largerunningstrategy(gov, strategy, dai, vault, whale):

    amount = Wei('499000 ether')
    dai.approve(vault, amount, {'from': whale})
    vault.deposit(amount, {'from': whale})    

    strategy.harvest({'from': gov})
    
    #do it again with a smaller amount to replicate being this full for a while
    amount = Wei('1000 ether')
    dai.approve(vault, amount, {'from': whale})
    vault.deposit(amount, {'from': whale})   
    strategy.harvest({'from': gov})
    
    yield strategy

@pytest.fixture()
def enormousrunningstrategy(gov, largerunningstrategy, dai, vault, whale):
    dai.approve(vault, dai.balanceOf(whale), {'from': whale})
    vault.deposit(dai.balanceOf(whale), {'from': whale})   
   
    collat = 0

    while collat < largerunningstrategy.collateralTarget() / 1.001e18:

        largerunningstrategy.harvest({'from': gov})
        deposits, borrows = largerunningstrategy.getCurrentPosition()
        collat = borrows / deposits
        
    
    yield largerunningstrategy
