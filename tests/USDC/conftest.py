import pytest
from brownie import Wei, config


#change these fixtures for generic tests
@pytest.fixture
def currency(interface):
    #this one is dai:
    #yield interface.ERC20('0x6b175474e89094c44da98b954eedeac495271d0f')
    #usdc
    yield interface.ERC20('0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48')
    #this one is weth:
    #yield interface.ERC20('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2')
@pytest.fixture
def vault(gov, rewards, guardian, currency, pm, Vault):

    vault = gov.deploy(Vault)
    vault.initialize(currency, gov, rewards, "", "", guardian)
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})

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
def whale(accounts, web3, weth,currency, gov, chain):
    #big binance7 wallet
    acc = accounts.at('0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8', force=True)
    #big binance8 wallet
    #acc = accounts.at('0xf977814e90da44bfa03b6295a0616a897441acec', force=True)
    #big binance1 wallet
    #acc = accounts.at('0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE', force=True)

    #lots of weth account
    #if weth transfer fails change to new weth account
    wethAcc = accounts.at('0x1840c62fD7e2396e470377e6B2a833F3A1E96221', force=True)

    #weth.transfer(acc, weth.balanceOf(wethAcc),{"from": wethAcc} )

    decimals = currency.decimals()
    #wethDeposit = 100 *1e18
    deposit = 10000 *(10 ** decimals)

    #assert weth.balanceOf(acc)  > wethDeposit
    assert currency.balanceOf(acc) > deposit

    #weth.transfer(gov, wethDeposit,{"from": acc} )
    currency.transfer(gov, deposit,{"from": acc} )

    #assert  weth.balanceOf(acc) > 0
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
def daddy(accounts):
    yield accounts.at('0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52', force=True)

@pytest.fixture
def creamdev(accounts):
    yield accounts.at('0x6D5a7597896A703Fe8c85775B23395a48f971305', force=True)

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
def live_strategy(Strategy):
    yield Strategy.at('0x2F082A8f4A41FB81AC3cfb39Cf41Ca47378d692E')

@pytest.fixture
def live_strat_030(Strategy):
    yield Strategy.at('0x77b7CD137Dd9d94e7056f78308D7F65D2Ce68910')


#0x1cfa165d8f6aa883fca19c58cf4e73ae2105b80ca9f0974abaf0d2bc50bf6ded <- new strat hash
@pytest.fixture
def live_vault_dai(Vault):
    yield Vault.at('0x19D3364A399d251E894aC732651be8B0E4e85001')

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

@pytest.fixture
def cyusdc(interface):
    yield interface.CErc20I('0x76Eb2FE28b36B3ee97F3Adae0C69606eeDB2A37c')

@pytest.fixture
def cusdc(interface):
    yield interface.CErc20I('0x39AA39c021dfbaE8faC545936693aC917d5E7563')
    

@pytest.fixture
def ibdai(interface):
    yield interface.CErc20I('0x8e595470Ed749b85C6F7669de83EAe304C2ec68F')

@pytest.fixture
def ironbank(interface):
    yield interface.IronBankControllerI('0xAB1c342C7bf5Ec5F02ADEA1c2270670bCa144CbB')

#@pytest.fixture(autouse=True)
#def isolation(fn_isolation):
#    pass
@pytest.fixture(scope="module", autouse=True)
def shared_setup(module_isolation):
    pass

@pytest.fixture
def gov(accounts):
    yield accounts[0]
@pytest.fixture
def live_gov(accounts):
    yield accounts.at('0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52', force=True)



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
def strategy_base(strategist,gov, keeper, vault,  Strategy, cyusdc, cusdc):
    uinswap = '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D'
    weth = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
    ironcomptroller = '0xAB1c342C7bf5Ec5F02ADEA1c2270670bCa144CbB'
    comptroller = '0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B'
    solo = '0x1E0447b19BB6EcFdAe1e4AE1694b0C3659614e4e'
    comp = '0xc00e94Cb662C3520282E6f5717214004A7f26888'

    strategy = strategist.deploy(Strategy,vault, cusdc, solo, comptroller, ironcomptroller, cyusdc, comp, uinswap, weth)
    strategy.setKeeper(keeper)
    yield strategy

@pytest.fixture()
def strategy(strategist,gov, keeper, vault,  strategy_base):
    
    strategy = strategy_base
    vault.addStrategy(
        strategy, 10_000,
        2 ** 256 - 1, 
        1000,  # 0.5% performance fee for Strategist
        {"from": gov},
    )

    yield strategy

@pytest.fixture()
def smallrunningstrategy(gov, strategy,ironbank, usdc,creamdev, cyusdc, vault, whale):
    usdc.approve(cyusdc, 2 ** 256 - 1, {'from': whale})
    decimals = usdc.decimals()
    ironbank._setCreditLimit(strategy, 1_000_000 *1e18, {'from': creamdev})

    cyusdc.mint(10_000_000*(10 ** decimals), {'from': whale})

    amount = 10_000 * (10 ** decimals)
    usdc.approve(vault, amount, {'from': whale})
    vault.deposit(amount, {'from': whale})    

    strategy.harvest({'from': gov})
    
    #do it again with a smaller amount to replicate being this full for a while
    amount = 1000 * (10 ** decimals)
    usdc.approve(vault, amount, {'from': whale})
    vault.deposit(amount, {'from': whale})   
    strategy.harvest({'from': gov})
    
    yield strategy

@pytest.fixture()
def largerunningstrategy(gov,ironbank, strategy,creamdev, dai, vault, whale):

    amount = Wei('499000 ether')
    dai.approve(vault, amount, {'from': whale})
    vault.deposit(amount, {'from': whale})    
    ironbank._setCreditLimit(strategy, 1_000_000 *1e18, {'from': creamdev})
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
        print(collat)
        
    
    yield largerunningstrategy

