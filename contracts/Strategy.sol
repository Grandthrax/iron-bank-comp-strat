// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.6.12;
pragma experimental ABIEncoderV2;

import {BaseStrategy, StrategyParams, VaultAPI} from "@yearnvaults/contracts/BaseStrategy.sol";

import "./Interfaces/DyDx/DydxFlashLoanBase.sol";
import "./Interfaces/DyDx/ICallee.sol";

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/math/Math.sol";
import "@openzeppelin/contracts/utils/Address.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";

import "./Interfaces/Compound/SCErc20I.sol";
import "./Interfaces/Compound/SComptrollerI.sol";
import "./Interfaces/UniswapInterfaces/IUni.sol";


contract Strategy is BaseStrategy, DydxFlashloanBase, ICallee {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    //Flash Loan Providers
    address public SOLO;

    // Comptroller address for compound.finance
    address public compound;

    //IRON BANK
    address public ironBank;
    address public ironBankToken;
    uint256 public maxIronBankLeverage = 4; //max leverage we will take from iron bank
    uint256 public step = 10;

    //Only three tokens we use
    address public comp;
    address public cToken;

    address public uniswapRouter;
    address public weth;

    //Operating variables
    uint256 public collateralTarget = 0.73 ether; // 73%
    uint256 public blocksToLiquidationDangerZone = 46500; // 7 days =  60*60*24*7/13

    uint256 public minWant = 0; //Only lend if we have enough want to be worth it. Can be set to non-zero
    uint256 public minCompToSell = 0.1 ether; //used both as the threshold to sell but also as a trigger for harvest

    //To deactivate flash loan provider if needed
    bool public DyDxActive = true;

    uint256 private dyDxMarketId;

    constructor(
        address _vault,
        address _cToken,
        address _solo,
        address _compound,
        address _ironBank,
        address _ironBankToken,
        address _comp,
        address _uniswapRouter,
        address _weth

    ) public BaseStrategy(_vault) {
        SOLO = _solo;
        compound = _compound;
        ironBank = _ironBank;
        ironBankToken = _ironBankToken;
        comp = _comp;
        uniswapRouter = _uniswapRouter;
        weth = _weth;

        cToken = _cToken;

        //pre-set approvals
        IERC20(_comp).safeApprove(_uniswapRouter, uint256(-1));
        want.safeApprove(address(cToken), uint256(-1));
        want.safeApprove(_solo, uint256(-1));
        want.safeApprove(address(ironBankToken), uint256(-1));

        // You can set these parameters on deployment to whatever you want
        maxReportDelay = 86400; // once per 24 hours
        profitFactor = 15000; // multiple before triggering harvest
        debtThreshold = 500*1e18; // don't bother borrowing if less than debtThreshold

        dyDxMarketId = _getMarketIdFromTokenAddress(_solo, address(want));
    }

    function name() external override view returns (string memory){
        return "IBLevComp";
    }

    function _isAuthorized() internal view {
        require(msg.sender == strategist || msg.sender == governance(), "!authorized");
    }
    function _isGov() internal view {
        require(msg.sender == governance(), "!authorized");
    }

    /*
     * Control Functions
     */
    function setIsDyDxActive(bool _isActive) external {
        _isAuthorized();
        DyDxActive = _isActive;
    }

    function setMinCompToSell(uint256 _minCompToSell) external {
        _isAuthorized();
        minCompToSell = _minCompToSell;
    }

    function setIronBankLeverage(uint256 _multiple) external {
        _isGov();
        maxIronBankLeverage = _multiple;
    }

    function setStep(uint256 _step) external {
        _isGov();
        step = _step;
    }

    function setMinWant(uint256 _minWant) external {
        _isAuthorized();
        minWant = _minWant;
    }

    function updateMarketId() external {
        _isAuthorized();
        dyDxMarketId = _getMarketIdFromTokenAddress(SOLO, address(want));
    }

    function setCollateralTarget(uint256 _collateralTarget) external {
        _isAuthorized();
        (, uint256 collateralFactorMantissa, ) = SComptrollerI(compound).markets(address(cToken));
        require(collateralFactorMantissa > _collateralTarget); //, "!dangerous collateral"
        collateralTarget = _collateralTarget;
    }

    /*
     * Base External Facing Functions
     */
    /*
     * An accurate estimate for the total amount of assets (principle + return)
     * that this strategy is currently managing, denominated in terms of want tokens.
     */
    function estimatedTotalAssets() public override view returns (uint256) {
        (uint256 deposits, uint256 borrows) = getCurrentPosition();

        uint256 _claimableComp = predictCompAccrued();
        uint256 currentComp = IERC20(comp).balanceOf(address(this));

        // Use touch price. it doesnt matter if we are wrong as this is not used for decision making
        uint256 estimatedWant =  priceCheck(comp, address(want),_claimableComp.add(currentComp));
        uint256 conservativeWant = estimatedWant.mul(9).div(10); //10% pessimist
        uint256 ironBankDebt = ironBankOutstandingDebtStored();

        return want.balanceOf(address(this)).add(deposits).add(conservativeWant).sub(borrows).sub(ironBankDebt);
    }

    /*
     * Provide a signal to the keeper that `tend()` should be called.
     * (keepers are always reimbursed by yEarn)
     *
     * NOTE: this call and `harvestTrigger` should never return `true` at the same time.
     * tendTrigger should be called with same gasCost as harvestTrigger
     */
    function tendTrigger(uint256 gasCost) public override view returns (bool) {
        if (harvestTrigger(gasCost)) {
            //harvest takes priority
            return false;
        }

        if (getblocksUntilLiquidation() <= blocksToLiquidationDangerZone) {
            return true;
        }


        uint256 wantGasCost = priceCheck(weth, address(want), gasCost);
        //test if we want to change iron bank position
        (,uint256 _amount)= internalCreditOfficer();
        if(profitFactor.mul(wantGasCost) < _amount){
            return true;
        }
    }

    /*
     * Provide a signal to the keeper that `harvest()` should be called.
     * gasCost is expected_gas_use * gas_price
     * (keepers are always reimbursed by yEarn)
     *
     * NOTE: this call and `tendTrigger` should never return `true` at the same time.
     */
    function harvestTrigger(uint256 gasCost) public override view returns (bool) {
        StrategyParams memory params = vault.strategies(address(this));
        // Should not trigger if strategy is not activated
        if (params.activation == 0) return false;

        uint256 wantGasCost = priceCheck(weth, address(want), gasCost);
        uint256 compGasCost = priceCheck(weth, comp, gasCost);

        // after enough comp has accrued we want the bot to run
        uint256 _claimableComp = predictCompAccrued();

        if (_claimableComp > minCompToSell) {
            // check value of COMP in wei
            if ( _claimableComp.add(IERC20(comp).balanceOf(address(this))) > compGasCost.mul(profitFactor)) {
                return true;
            }
        }


        // Should trigger if hadn't been called in a while
        if (block.timestamp.sub(params.lastReport) >= maxReportDelay) return true;

        //check if vault wants lots of money back
        // dont return dust
        uint256 outstanding = vault.debtOutstanding();
        if (outstanding > profitFactor.mul(wantGasCost)) return true;

        // Check for profits and losses
        uint256 total = estimatedTotalAssets();

        uint256 profit = 0;
        if (total > params.totalDebt) profit = total.sub(params.totalDebt); // We've earned a profit!

        uint256 credit = vault.creditAvailable().add(profit);
        return (profitFactor.mul(wantGasCost) < credit);
    }

    //WARNING. manipulatable and simple routing. Only use for safe functions
    function priceCheck(address start, address end, uint256 _amount) public view returns (uint256) {
        if (_amount == 0) {
            return 0;
        }
        address[] memory path;
        if(start == weth){
            path = new address[](2);
            path[0] = weth;
            path[1] = end;
        }else{
            path = new address[](3);
            path[0] = start;
            path[1] = weth;
            path[2] = end;
        }

        uint256[] memory amounts = IUni(uniswapRouter).getAmountsOut(_amount, path);

        return amounts[amounts.length - 1];
    }

    /*****************
     * Iron Bank
     ******************/

    //simple logic. do we get more apr than iron bank charges?
    //if so, is that still true with increased pos?
    //if not, should be reduce?
    //made harder because we can't assume iron bank debt curve. So need to increment
    function internalCreditOfficer() public view returns (bool borrowMore, uint256 amount) {

        //how much credit we have
        (, uint256 liquidity, uint256 shortfall) = SComptrollerI(ironBank).getAccountLiquidity(address(this));
        uint256 underlyingPrice = SComptrollerI(ironBank).oracle().getUnderlyingPrice(address(ironBankToken));
        
        if(underlyingPrice == 0){
            return (false, 0);
        }

        liquidity = liquidity.mul(1e18).div(underlyingPrice);
        shortfall = shortfall.mul(1e18).div(underlyingPrice);

        uint256 outstandingDebt = ironBankOutstandingDebtStored();

        //repay debt if iron bank wants its money back
        //we need careful to not just repay the bare minimun as it will go over immediately
        if(shortfall > debtThreshold){
            //note we only borrow 1 asset so can assume all our shortfall is from it
            return(false, Math.min(outstandingDebt, shortfall.mul(2))); //return double our shortfall
        }

        uint256 liquidityAvailable = want.balanceOf(address(ironBankToken));
        uint256 remainingCredit = Math.min(liquidity, liquidityAvailable);
        
        //our current supply rate.
        //we only calculate once because it is expensive
        uint256 currentSR = currentSupplyRate();
        //iron bank borrow rate
        uint256 ironBankBR = ironBankBorrowRate(0, true);

        //we have internal credit limit. it is function on our own assets invested
        //this means we can always repay our debt from our capital
        uint256 maxCreditDesired = vault.strategies(address(this)).totalDebt.mul(maxIronBankLeverage);
  
        // if we have too much debt we return
        //overshoot incase of dust
        if(maxCreditDesired.mul(11).div(10) < outstandingDebt){
            borrowMore = false;
            amount = outstandingDebt - maxCreditDesired;
            if(amount < debtThreshold){
                amount = 0;
            }
            return (false, amount);
        }

        //minIncrement must be > 0
        if(maxCreditDesired <= step){
            return (false, 0);
        }

        //we move in 10% increments
        uint256 minIncrement = maxCreditDesired.div(step);

        //we start at 1 to save some gas
        uint256 increment = 1;

        //if sr is > iron bank we borrow more. else return
        if(currentSR > ironBankBR){            
            remainingCredit = Math.min(maxCreditDesired - outstandingDebt, remainingCredit);

            while(minIncrement.mul(increment) <= remainingCredit){
                ironBankBR = ironBankBorrowRate(minIncrement.mul(increment), false);
                if(currentSR <= ironBankBR){
                    break;
                }

                increment++;
            }
            borrowMore = true;
            amount = minIncrement.mul(increment-1);

        }else{

            while(minIncrement.mul(increment) <= outstandingDebt){
                ironBankBR = ironBankBorrowRate(minIncrement.mul(increment), true);

                //we do increment before the if statement here
                increment++;
                if(currentSR > ironBankBR){
                    break;
                }

            }
            borrowMore = false;

            //special case to repay all
            if(increment == 1){
                amount = outstandingDebt;
            }else{
                amount = minIncrement.mul(increment - 1);
            }

        }

        //we dont play with dust:
        if (amount < debtThreshold) { 
            amount = 0;
        }
     }

     function ironBankOutstandingDebtStored() public view returns (uint256 available) {

        return SCErc20I(ironBankToken).borrowBalanceStored(address(this));
     }


     function ironBankBorrowRate(uint256 amount, bool repay) public view returns (uint256) {
        uint256 cashPrior = want.balanceOf(address(ironBankToken));

        uint256 borrows = SCErc20I(ironBankToken).totalBorrows();
        uint256 reserves = SCErc20I(ironBankToken).totalReserves();

        InterestRateModel model = SCErc20I(ironBankToken).interestRateModel();
        uint256 cashChange;
        uint256 borrowChange;
        if(repay){
            cashChange = cashPrior.add(amount);
            borrowChange = borrows.sub(amount);
        }else{
            cashChange = cashPrior.sub(amount);
            borrowChange = borrows.add(amount);
        }

        uint256 borrowRate = model.getBorrowRate(cashChange, borrowChange, reserves);

        return borrowRate;
    }



    /*****************
     * Public non-base function
     ******************/

    //Calculate how many blocks until we are in liquidation based on current interest rates
    //WARNING does not include compounding so the estimate becomes more innacurate the further ahead we look
    //equation. Compound doesn't include compounding for most blocks
    //((deposits*colateralThreshold - borrows) / (borrows*borrowrate - deposits*colateralThreshold*interestrate));
    function getblocksUntilLiquidation() public view returns (uint256) {
        (, uint256 collateralFactorMantissa, ) = SComptrollerI(compound).markets(address(cToken));

        (uint256 deposits, uint256 borrows) = getCurrentPosition();

        uint256 borrrowRate = SCErc20I(cToken).borrowRatePerBlock();

        uint256 supplyRate = SCErc20I(cToken).supplyRatePerBlock();

        uint256 collateralisedDeposit1 = deposits.mul(collateralFactorMantissa).div(1e18);
        uint256 collateralisedDeposit = collateralisedDeposit1;

        uint256 denom1 = borrows.mul(borrrowRate);
        uint256 denom2 = collateralisedDeposit.mul(supplyRate);

        if (denom2 >= denom1) {
            return uint256(-1);
        } else {
            uint256 numer = collateralisedDeposit.sub(borrows);
            uint256 denom = denom1 - denom2;
            //minus 1 for this block
            return numer.mul(1e18).div(denom);
        }
    }

    // This function makes a prediction on how much comp is accrued
    // It is not 100% accurate as it uses current balances in Compound to predict into the past
    function predictCompAccrued() public view returns (uint256) {


        //last time we ran harvest
        uint256 lastReport = vault.strategies(address(this)).lastReport;
        uint256 blocksSinceLast= (block.timestamp.sub(lastReport)).div(13); //roughly 13 seconds per block

        return blocksSinceLast.mul(compBlockShare());
    }

    function compBlockShare() public view returns (uint256){
        (uint256 deposits, uint256 borrows) = getCurrentPosition();
        if (deposits == 0) {
            return 0; // should be impossible to have 0 balance and positive comp accrued
        }

        //comp speed is amount to borrow or deposit (so half the total distribution for want)
        uint256 distributionPerBlock = SComptrollerI(compound).compSpeeds(address(cToken));

        uint256 totalBorrow = SCErc20I(cToken).totalBorrows();

        //total supply needs to be echanged to underlying using exchange rate
        uint256 totalSupplyCtoken = SCErc20I(cToken).totalSupply();
        uint256 totalSupply = totalSupplyCtoken.mul(SCErc20I(cToken).exchangeRateStored()).div(1e18);

        uint256 blockShareSupply = 0;
        if(totalSupply > 0){
            blockShareSupply = deposits.mul(distributionPerBlock).div(totalSupply);
        }

        uint256 blockShareBorrow = 0;
        if(totalBorrow > 0){
            blockShareBorrow = borrows.mul(distributionPerBlock).div(totalBorrow);
        }

        //how much we expect to earn per block
        return blockShareSupply.add(blockShareBorrow);
    }

    function currentSupplyRate() public view returns (uint256 supply) {
        //first let's do standard borrow and lend
        uint256 cashPrior = want.balanceOf(address(cToken));

        uint256 totalBorrows = SCErc20I(cToken).totalBorrows();
        uint256 reserves = SCErc20I(cToken).totalReserves();

        uint256 reserverFactor = SCErc20I(cToken).reserveFactorMantissa();
        InterestRateModel model = SCErc20I(cToken).interestRateModel();

        //the supply rate is derived from the borrow rate, reserve factor and the amount of total borrows.
        uint256 supplyRate = model.getSupplyRate(cashPrior, totalBorrows, reserves, reserverFactor);
        uint256 borrowRate = model.getBorrowRate(cashPrior, totalBorrows, reserves);



        uint256 compPerBlock = compBlockShare();
        uint256 estimatedWant =  priceCheck(comp, address(want),compPerBlock);
        uint256 compRate;
        if(estimatedWant != 0){
            compRate = estimatedWant.mul(9).div(10); //10% pessimist
            //now need to scale. compPerBlock is out total.
            compRate = compRate.mul(1e18).div(netBalanceLent());

        }

        //our supply rate is:
        //comp + lend - borrow
        supplyRate = compRate.add(supplyRate);
        if(supplyRate > borrowRate){
            supply = supplyRate.sub(borrowRate);
        }else{
            supply = 0;
        }


    }

    //Returns the current position
    //WARNING - this returns just the balance at last time someone touched the cToken token. Does not accrue interst in between
    //cToken is very active so not normally an issue.
    function getCurrentPosition() public view returns (uint256 deposits, uint256 borrows) {
        (, uint256 ctokenBalance, uint256 borrowBalance, uint256 exchangeRate) = SCErc20I(cToken).getAccountSnapshot(address(this));
        borrows = borrowBalance;

        deposits = ctokenBalance.mul(exchangeRate).div(1e18);
    }

    //statechanging version
    function getLivePosition() internal returns (uint256 deposits, uint256 borrows) {
        deposits = SCErc20I(cToken).balanceOfUnderlying(address(this));

        //we can use non state changing now because we updated state with balanceOfUnderlying call
        borrows = SCErc20I(cToken).borrowBalanceStored(address(this));
    }

    //Same warning as above
    function netBalanceLent() public view returns (uint256) {
        (uint256 deposits, uint256 borrows) = getCurrentPosition();
        return deposits.sub(borrows);
    }

    /***********
     * internal core logic
     *********** */
    /*
     * A core method.
     * Called at beggining of harvest before providing report to owner
     * 1 - claim accrued comp
     * 2 - if enough to be worth it we sell
     * 3 - because we lose money on our loans we need to offset profit from comp.
     */
    function prepareReturn(uint256 _debtOutstanding)
        internal
        override
        returns (
            uint256 _profit,
            uint256 _loss,
            uint256 _debtPayment
        ) {
        _profit = 0;
        _loss = 0; //for clarity. also reduces bytesize

        if (SCErc20I(cToken).balanceOf(address(this)) == 0) {

            uint256 wantBalance = want.balanceOf(address(this));
            //no position to harvest
            //but we may have some debt to return
            //it is too expensive to free more debt in this method so we do it in adjust position
            _debtPayment = Math.min(wantBalance, _debtOutstanding);           
            return (_profit, _loss, _debtPayment);
        }
        (uint256 deposits, uint256 borrows) = getLivePosition();

        //claim comp accrued
        _claimComp();
        //sell comp
        _disposeOfComp();

        uint256 wantBalance = want.balanceOf(address(this));

        uint256 investedBalance = deposits.sub(borrows);
        uint256 balance = investedBalance.add(wantBalance);

        uint256 ibDebt = SCErc20I(ironBankToken).borrowBalanceCurrent(address(this));
        uint256 debt = vault.strategies(address(this)).totalDebt.add(ibDebt);

        //Balance - Total Debt is profit
        if (balance > debt) {
            _profit = balance - debt;

            if (wantBalance < _profit) {
                //all reserve is profit
                _profit = wantBalance;
            } else if (wantBalance > _profit.add(_debtOutstanding)){
                _debtPayment = _debtOutstanding;
            }else{
                _debtPayment = wantBalance - _profit;
            }
        } else {
            //we will lose money until we claim comp then we will make money
            //this has an unintended side effect of slowly lowering our total debt allowed
            _loss = debt - balance;
            _debtPayment = Math.min(wantBalance, _debtOutstanding);
        }


    }

    /*
     * Second core function. Happens after report call.
     *
     * Similar to deposit function from V1 strategy
     */

    function adjustPosition(uint256 _debtOutstanding) internal override {
        //emergency exit is dealt with in prepareReturn
        if (emergencyExit) {
            return;
        }

        //start off by borrowing or returning:
        (bool borrowMore, uint256 amount) = internalCreditOfficer();

        //if repaying we use debOutstanding
        if(!borrowMore){
            _debtOutstanding = amount;
        }else if(amount > 0){
            //borrow the amount we want
            SCErc20I(ironBankToken).borrow(amount);
        }

        //we are spending all our cash unless we have debt outstanding
        uint256 _wantBal = want.balanceOf(address(this));
        
        if(_wantBal < _debtOutstanding){
            //this is graceful withdrawal. dont use backup
            //we use more than 1 because withdrawunderlying causes problems with 1 token due to different decimals
            if(SCErc20I(cToken).balanceOf(address(this)) > 1){
                _withdrawSome(_debtOutstanding - _wantBal);
            }
            if(!borrowMore){
                SCErc20I(ironBankToken).repayBorrow(Math.min(_debtOutstanding, want.balanceOf(address(this))));
            }
            return;
        }

        (uint256 position, bool deficit) = _calculateDesiredPosition(_wantBal - _debtOutstanding, true);

        //if we are below minimun want change it is not worth doing
        //need to be careful in case this pushes to liquidation
        if (position > minWant) {
            //if dydx is not active we just try our best with basic leverage
            if (!DyDxActive) {
                uint i = 5;
                while(position > 0){
                    position = position.sub(_noFlashLoan(position, deficit));
                    i++;
                }
            } else {
                //if there is huge position to improve we want to do normal leverage. it is quicker
                if (position > want.balanceOf(SOLO)) {
                    position = position.sub(_noFlashLoan(position, deficit));
                }

                //flash loan to position
                if(position > 0){
                    doDyDxFlashLoan(deficit, position);
                }

            }
        }

       // if(!borrowMore){
            //now we have debt outstanding lent without being needed:
        //    cToken.redeemUnderlying(_debtOutstanding);
         //   ironBankToken.repayBorrow(Math.min(_debtOutstanding, want.balanceOf(address(this))));
        //}
    }

    /*************
     * Very important function
     * Input: amount we want to withdraw.
     *       cannot be more than we have
     * Returns amount we were able to withdraw. notall if user has some balance left
     *
     * Deleverage position -> redeem our cTokens
     ******************** */
    function _withdrawSome(uint256 _amount) internal returns (bool notAll) {
        (uint256 position, bool deficit) = _calculateDesiredPosition(_amount, false);

        //If there is no deficit we dont need to adjust position
        if (deficit) {
            //we do a flash loan to give us a big gap. from here on out it is cheaper to use normal deleverage.
            if (DyDxActive) {
                position = position.sub(doDyDxFlashLoan(deficit, position));
            }

            uint8 i = 0;
            //position will equal 0 unless we haven't been able to deleverage enough with flash loan
            //if we are not in deficit we dont need to do flash loan
            while (position > 0) {
                position = position.sub(_noFlashLoan(position, true));
                i++;

                //A limit set so we don't run out of gas
                if (i >= 5) {
                    notAll = true;
                    break;
                }
            }
        }

        //now withdraw
        //if we want too much we just take max

        //This part makes sure our withdrawal does not force us into liquidation
        (uint256 depositBalance, uint256 borrowBalance) = getCurrentPosition();

        uint256 AmountNeeded = 0;
        if(collateralTarget > 0){
            AmountNeeded = borrowBalance.mul(1e18).div(collateralTarget);
        }
        uint256 redeemable = depositBalance.sub(AmountNeeded);

        if (redeemable < _amount) {
            SCErc20I(cToken).redeemUnderlying(redeemable);
        } else {
            SCErc20I(cToken).redeemUnderlying(_amount);
        }

        //let's sell some comp if we have more than needed
        //flash loan would have sent us comp if we had some accrued so we don't need to call claim comp
        _disposeOfComp();
    }

    /***********
     *  This is the main logic for calculating how to change our lends and borrows
     *  Input: balance. The net amount we are going to deposit/withdraw.
     *  Input: dep. Is it a deposit or withdrawal
     *  Output: position. The amount we want to change our current borrow position.
     *  Output: deficit. True if we are reducing position size
     *
     *  For instance deficit =false, position 100 means increase borrowed balance by 100
     ****** */
    function _calculateDesiredPosition(uint256 balance, bool dep) internal returns (uint256 position, bool deficit) {
        //we want to use statechanging for safety
        (uint256 deposits, uint256 borrows) = getLivePosition();

        //When we unwind we end up with the difference between borrow and supply
        uint256 unwoundDeposit = deposits.sub(borrows);

        //we want to see how close to collateral target we are.
        //So we take our unwound deposits and add or remove the balance we are are adding/removing.
        //This gives us our desired future undwoundDeposit (desired supply)

        uint256 desiredSupply = 0;
        if (dep) {
            desiredSupply = unwoundDeposit.add(balance);
        } else {
            if(balance > unwoundDeposit) balance = unwoundDeposit;
            desiredSupply = unwoundDeposit.sub(balance);
        }

        //(ds *c)/(1-c)
        uint256 num = desiredSupply.mul(collateralTarget);
        uint256 den = uint256(1e18).sub(collateralTarget);

        uint256 desiredBorrow = num.div(den);
        if (desiredBorrow > 1e5) {
            //stop us going right up to the wire
            desiredBorrow = desiredBorrow - 1e5;
        }

        //now we see if we want to add or remove balance
        // if the desired borrow is less than our current borrow we are in deficit. so we want to reduce position
        if (desiredBorrow < borrows) {
            deficit = true;
            position = borrows - desiredBorrow; //safemath check done in if statement
        } else {
            //otherwise we want to increase position
            deficit = false;
            position = desiredBorrow - borrows;
        }
    }

    /*
     * Liquidate as many assets as possible to `want`, irregardless of slippage,
     * up to `_amount`. Any excess should be re-invested here as well.
     */
    function liquidatePosition(uint256 _amountNeeded) internal override returns (uint256 _amountFreed, uint256 _loss) {
        uint256 _balance = want.balanceOf(address(this));

        uint256 assets = netBalanceLent().add(_balance);

        uint256 debtOutstanding = vault.debtOutstanding();
        if(debtOutstanding > assets){
            _loss = debtOutstanding - assets;
        }

        if (assets < _amountNeeded) {
            //if we cant afford to withdraw we take all we can
            //withdraw all we can
            (uint256 deposits, uint256 borrows) = getLivePosition();

            //1 token causes rounding error with withdrawUnderlying
            if(SCErc20I(cToken).balanceOf(address(this)) > 1){
                _withdrawSome(deposits.sub(borrows));
            }

            _amountFreed = Math.min(_amountNeeded, want.balanceOf(address(this)));
        } else {
            if (_balance < _amountNeeded) {
                _withdrawSome(_amountNeeded.sub(_balance));

                //overflow error if we return more than asked for
                _amountFreed = Math.min(_amountNeeded, want.balanceOf(address(this)));
            }else{
                _amountFreed = _amountNeeded;
            }
        }
    }

    function _claimComp() internal {
        SCErc20I[] memory tokens = new SCErc20I[](1);
        tokens[0] = SCErc20I(cToken);

        SComptrollerI(compound).claimComp(address(this), tokens);
    }

    //sell comp function
    function _disposeOfComp() internal {
        uint256 _comp = IERC20(comp).balanceOf(address(this));

        if (_comp > minCompToSell) {
            address[] memory path = new address[](3);
            path[0] = comp;
            path[1] = weth;
            path[2] = address(want);

            IUni(uniswapRouter).swapExactTokensForTokens(_comp, uint256(0), path, address(this), now);
        }
    }


    //lets leave
    //if we can't deleverage in one go set collateralFactor to 0 and call harvest multiple times until delevered
    function prepareMigration(address _newStrategy) internal override {
        (uint256 deposits, uint256 borrows) = getLivePosition();
        _withdrawSome(deposits.sub(borrows));

        (, , uint256 borrowBalance, ) = SCErc20I(cToken).getAccountSnapshot(address(this));

        require(borrowBalance < debtThreshold); //, "DELEVERAGE_FIRST"

        //return our iron bank deposit:
        //state changing
        uint256 ibBorrows = SCErc20I(ironBankToken).borrowBalanceCurrent(address(this));
        SCErc20I(ironBankToken).repayBorrow(Math.min(ibBorrows, want.balanceOf(address(this))));

        want.safeTransfer(_newStrategy, want.balanceOf(address(this)));

        IERC20 _comp = IERC20(comp);
        uint _compB = _comp.balanceOf(address(this));
        if(_compB > 0){
            _comp.safeTransfer(_newStrategy, _compB);
        }
    }

    //Three functions covering normal leverage and deleverage situations
    // max is the max amount we want to increase our borrowed balance
    // returns the amount we actually did
    function _noFlashLoan(uint256 max, bool deficit) internal returns (uint256 amount) {
        //we can use non-state changing because this function is always called after _calculateDesiredPosition
        (uint256 lent, uint256 borrowed) = getCurrentPosition();

        //if we have nothing borrowed then we can't deleverage any more
        if (borrowed == 0 && deficit) {
            return 0;
        }

        (, uint256 collateralFactorMantissa, ) = SComptrollerI(compound).markets(address(cToken));

        if (deficit) {
            amount = _normalDeleverage(max, lent, borrowed, collateralFactorMantissa);
        } else {
            amount = _normalLeverage(max, lent, borrowed, collateralFactorMantissa);
        }

        //emit Leverage(max, amount, deficit, address(0));
    }

    //maxDeleverage is how much we want to reduce by
    function _normalDeleverage(
        uint256 maxDeleverage,
        uint256 lent,
        uint256 borrowed,
        uint256 collatRatio
    ) internal returns (uint256 deleveragedAmount) {
        uint256 theoreticalLent = 0;

        //collat ration should never be 0. if it is something is very wrong... but just incase
        if(collatRatio != 0){
            theoreticalLent = borrowed.mul(1e18).div(collatRatio);
        }

        deleveragedAmount = lent.sub(theoreticalLent);

        if (deleveragedAmount >= borrowed) {
            deleveragedAmount = borrowed;
        }
        if (deleveragedAmount >= maxDeleverage) {
            deleveragedAmount = maxDeleverage;
        }

        SCErc20I(cToken).redeemUnderlying(deleveragedAmount);

        //our borrow has been increased by no more than maxDeleverage
        SCErc20I(cToken).repayBorrow(deleveragedAmount);
    }

    //maxDeleverage is how much we want to increase by
    function _normalLeverage(
        uint256 maxLeverage,
        uint256 lent,
        uint256 borrowed,
        uint256 collatRatio
    ) internal returns (uint256 leveragedAmount) {
        uint256 theoreticalBorrow = lent.mul(collatRatio).div(1e18);

        leveragedAmount = theoreticalBorrow.sub(borrowed);

        if (leveragedAmount >= maxLeverage) {
            leveragedAmount = maxLeverage;
        }

        SCErc20I(cToken).borrow(leveragedAmount);
        SCErc20I(cToken).mint(want.balanceOf(address(this)));
    }

    function protectedTokens() internal override view returns (address[] memory) {

        //want is protected automatically
        address[] memory protected = new address[](2);
        protected[0] = comp;
        protected[1] = address(cToken);
        return protected;
    }

    /******************
     * Flash loan stuff
     ****************/

    // Flash loan DXDY
    // amount desired is how much we are willing for position to change
    function doDyDxFlashLoan(bool deficit, uint256 amountDesired) internal returns (uint256) {
        uint256 amount = amountDesired;
        ISoloMargin solo = ISoloMargin(SOLO);

        // Not enough want in DyDx. So we take all we can
        uint256 amountInSolo = want.balanceOf(SOLO);

        if (amountInSolo < amount) {
            amount = amountInSolo;
        }

        uint256 repayAmount = amount.add(2); // we need to overcollateralise on way back

        bytes memory data = abi.encode(deficit, amount, repayAmount);

        // 1. Withdraw $
        // 2. Call callFunction(...)
        // 3. Deposit back $
        Actions.ActionArgs[] memory operations = new Actions.ActionArgs[](3);

        operations[0] = _getWithdrawAction(dyDxMarketId, amount);
        operations[1] = _getCallAction(
            // Encode custom data for callFunction
            data
        );
        operations[2] = _getDepositAction(dyDxMarketId, repayAmount);

        Account.Info[] memory accountInfos = new Account.Info[](1);
        accountInfos[0] = _getAccountInfo();

        solo.operate(accountInfos, operations);

        //emit Leverage(amountDesired, amount, deficit, SOLO);

        return amount;
    }

    //returns our current collateralisation ratio. Should be compared with collateralTarget
    function storedCollateralisation() public view returns (uint256 collat) {
        (uint256 lend, uint256 borrow) = getCurrentPosition();
        if (lend == 0) {
            return 0;
        }
        collat = uint256(1e18).mul(borrow).div(lend);
    }

    //DyDx calls this function after doing flash loan
    function callFunction(
        address sender,
        Account.Info memory account,
        bytes memory data
    ) public override {
        (bool deficit, uint256 amount, uint256 repayAmount) = abi.decode(data, (bool, uint256, uint256));
        require(msg.sender == SOLO); //, "NOT_SOLO"

        uint256 bal = want.balanceOf(address(this));
        require(bal >= amount); //, "FLASH_FAILED" to stop malicious calls

        //if in deficit we repay amount and then withdraw
        if (deficit) {
            SCErc20I(cToken).repayBorrow(amount);

            //if we are withdrawing we take more to cover fee
            SCErc20I(cToken).redeemUnderlying(repayAmount);
        } else {
            //check if this failed incase we borrow into liquidation
            require(SCErc20I(cToken).mint(bal) == 0); //dev: "mint error"
            //borrow more to cover fee
            // fee is so low for dydx that it does not effect our liquidation risk.
            //DONT USE FOR AAVE
            SCErc20I(cToken).borrow(repayAmount);
        }

    }

}
